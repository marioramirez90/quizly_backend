"""API views for authentication including registration, login, and logout."""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserDetailSerializer,
)
from .utils import (
    blacklist_refresh_token,
    build_refreshed_response,
    delete_auth_cookies,
    generate_tokens_for_user,
    get_refresh_token_from_request,
    set_auth_cookies,
)


class RegisterView(generics.CreateAPIView):
    """Register a new user account with validated credentials."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Validate payload, create user, and return created response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate user credentials and set JWT auth cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return response with auth cookies."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access_token, refresh_token = generate_tokens_for_user(user)
        user_data = UserDetailSerializer(user).data
        response = Response(
            {"detail": "Login successfully!", "user": user_data},
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, access_token, refresh_token)


class LogoutView(APIView):
    """Revoke user refresh token and delete authentication cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist refresh token, clear cookies, and return success."""
        token = get_refresh_token_from_request(request)
        blacklist_refresh_token(token)
        msg = (
            "Log-Out successfully! All Tokens will be deleted. "
            "Refresh token is now invalid."
        )
        response = Response({"detail": msg}, status=status.HTTP_200_OK)
        return delete_auth_cookies(response)


class TokenRefreshCookieView(APIView):

    """Issue a renewed access token from a valid refresh token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Verify refresh token and return updated access cookie."""
        token = get_refresh_token_from_request(request)
        if not token:
            msg = {"detail": "Refresh token missing."}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)
        response, err = build_refreshed_response(token)
        if err:
            msg = {"detail": "Invalid or expired token."}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)
        return response
