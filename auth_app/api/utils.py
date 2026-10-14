from rest_framework_simplejwt.tokens import RefreshToken


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_auth_cookies(response, access_token, refresh_token):
    cookie_kwargs = {'httponly': True, 'samesite': 'Lax', 'secure': False}
    response.set_cookie('access_token', access_token, **cookie_kwargs)
    response.set_cookie('refresh_token', refresh_token, **cookie_kwargs)
    return response


def delete_auth_cookies(response):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


def blacklist_refresh_token(token_str):
    if token_str:
        token = RefreshToken(token_str)
        token.blacklist()