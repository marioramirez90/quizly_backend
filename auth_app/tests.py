"""Automated unit and integration tests for authentication workflows."""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.api.authenticate import CookieJWTAuthentication
from auth_app.api.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserDetailSerializer,
)
from auth_app.api.utils import (
    blacklist_refresh_token,
    build_refreshed_response,
    delete_auth_cookies,
    generate_tokens_for_user,
    get_refresh_token_from_request,
    refresh_access_token_from_cookie,
    set_auth_cookies,
    set_single_cookie,
)


class RegistrationTests(TestCase):
    """Test user registration endpoint and serializer validation."""

    def setUp(self):
        """Initialize test client and default credentials."""
        self.client = APIClient()
        self.register_url = '/api/register/'
        self.valid_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'confirmed_password': 'SecurePassword123!',
        }

    def test_registration_success(self):
        """Verify successful user registration returns 201."""
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='john_doe').exists())

    def test_registration_password_mismatch(self):
        """Verify mismatched passwords return 400 validation error."""
        data = dict(self.valid_data, confirmed_password='DifferentPassword123')
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Verify registering with an existing email returns 400 error."""
        User.objects.create_user(
            username='existing', email='john@example.com', password='pwd'
        )
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_username(self):
        """Verify duplicate username returns 400 error."""
        User.objects.create_user(
            username='john_doe', email='other@example.com', password='pwd'
        )
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginLogoutTests(TestCase):
    """Test login, logout, and token blacklisting flows."""

    def setUp(self):
        """Create sample user for authentication."""
        self.client = APIClient()
        self.username = 'alice'
        self.password = 'SecretPass123'
        self.user = User.objects.create_user(
            username=self.username,
            email='alice@example.com',
            password=self.password,
        )

    def test_login_success(self):
        """Verify valid login sets access and refresh cookies."""
        payload = {'username': self.username, 'password': self.password}
        response = self.client.post('/api/login/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_invalid_credentials(self):
        """Verify invalid credentials return 401 error."""
        payload = {'username': self.username, 'password': 'WrongPassword'}
        response = self.client.post('/api/login/', payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """Verify logout blacklists token and removes cookies."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(Exception):
            refresh.check_blacklist()

    def test_logout_unauthenticated(self):
        """Verify logout without credentials returns 401."""
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(TestCase):
    """Test token refresh endpoint behavior with cookies."""

    def setUp(self):
        """Initialize client and user for refresh tests."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='bob', email='bob@example.com', password='pwd'
        )

    def test_refresh_token_success(self):
        """Verify refreshing token returns updated access token cookie."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post('/api/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_refresh_token_missing(self):
        """Verify missing refresh token returns 401."""
        response = self.client.post('/api/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_invalid(self):
        """Verify invalid refresh token returns 401."""
        self.client.cookies['refresh_token'] = 'invalid_token_string'
        response = self.client.post('/api/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CookieJWTAuthenticationTests(TestCase):
    """Test custom CookieJWTAuthentication class."""

    def setUp(self):
        """Set up request factory and test user."""
        self.factory = RequestFactory()
        self.auth = CookieJWTAuthentication()
        self.user = User.objects.create_user(
            username='carol', email='carol@example.com', password='pwd'
        )

    def test_authenticate_via_cookie(self):
        """Verify user is authenticated when token is in cookie."""
        refresh = RefreshToken.for_user(self.user)
        request = self.factory.get('/')
        request.COOKIES['access_token'] = str(refresh.access_token)
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.user)

    def test_authenticate_via_header(self):
        """Verify user is authenticated when token is in header."""
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        request = self.factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.user)

    def test_authenticate_no_credentials(self):
        """Verify None is returned when no credentials are provided."""
        request = self.factory.get('/')
        self.assertIsNone(self.auth.authenticate(request))


class AuthUtilsAndSerializersTests(TestCase):
    """Test utility functions and serializers in auth_app."""

    def setUp(self):
        """Create sample user for utility tests."""
        self.user = User.objects.create_user(
            username='dave', email='dave@example.com', password='pwd'
        )

    def test_generate_and_set_cookies(self):
        """Verify token generation and cookie assignment on response."""
        access, refresh = generate_tokens_for_user(self.user)
        response = Response()
        set_auth_cookies(response, access, refresh)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_delete_cookies(self):
        """Verify delete_auth_cookies removes token cookies."""
        response = Response()
        delete_auth_cookies(response)
        self.assertIn('access_token', response.cookies)

    def test_blacklist_handles_empty_or_invalid(self):
        """Verify blacklist_refresh_token handles None safely."""
        self.assertIsNone(blacklist_refresh_token(''))
        self.assertIsNone(blacklist_refresh_token('invalid_junk'))

    def test_get_refresh_token_from_request_data(self):
        """Verify token retrieval from request body when cookie absent."""
        factory = RequestFactory()
        request = factory.post('/', data={'refresh_token': 'body_token'})
        self.assertEqual(
            get_refresh_token_from_request(request), 'body_token'
        )

    def test_build_refreshed_response_failure(self):
        """Verify build_refreshed_response returns error flag on bad token."""
        resp, err = build_refreshed_response('bad_token')
        self.assertTrue(err)
        self.assertIsNone(resp)

    def test_user_detail_serializer(self):
        """Verify UserDetailSerializer output fields."""
        serializer = UserDetailSerializer(self.user)
        self.assertEqual(serializer.data['username'], 'dave')
