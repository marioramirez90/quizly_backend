"""Authentication helper utilities for token lifecycle and cookie handling."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def generate_tokens_for_user(user):
    """Generate and return new access and refresh token strings for a user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_single_cookie(response, key, value):
    """Set a single secure HttpOnly cookie on the response."""
    response.set_cookie(
        key,
        value,
        httponly=True,
        samesite='Lax',
        secure=False,
    )
    return response


def set_auth_cookies(response, access_token, refresh_token):
    """Attach access and refresh tokens as HttpOnly cookies to response."""
    set_single_cookie(response, 'access_token', access_token)
    set_single_cookie(response, 'refresh_token', refresh_token)
    return response


def delete_auth_cookies(response):
    """Delete access and refresh authentication cookies from response."""
    response.delete_cookie('access_token', samesite='Lax')
    response.delete_cookie('refresh_token', samesite='Lax')
    return response


def blacklist_refresh_token(token_str):
    """Blacklist the provided refresh token string if valid."""
    if not token_str:
        return
    try:
        token = RefreshToken(token_str)
        token.blacklist()
    except Exception:
        pass


def get_refresh_token_from_request(request):
    """Extract refresh token from cookies or request payload."""
    cookie_token = request.COOKIES.get('refresh_token')
    if cookie_token:
        return cookie_token
    payload = getattr(request, 'data', None)
    if payload is None:
        payload = getattr(request, 'POST', {})
    return payload.get('refresh_token') or payload.get('refresh')


def refresh_access_token_from_cookie(refresh_token):

    """Validate refresh token and return a newly issued access token."""
    token = RefreshToken(refresh_token)
    return str(token.access_token)


def build_refreshed_response(refresh_token):
    """Build response with refreshed access token or return error flag."""
    try:
        new_access = refresh_access_token_from_cookie(refresh_token)
        response = Response(
            {"detail": "Token refreshed"}, status=status.HTTP_200_OK
        )
        return set_single_cookie(response, "access_token", new_access), False
    except Exception:
        return None, True
