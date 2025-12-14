import requests
from django.conf import settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_exchange_code(code):
    data = {
        "code": code,
        "client_id": settings.SOCIAL_AUTH["GOOGLE_CLIENT_ID"],
        "client_secret": settings.SOCIAL_AUTH["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": settings.SOCIAL_AUTH["GOOGLE_REDIRECT_URI"],
        "grant_type": "authorization_code",
    }

    res = requests.post(GOOGLE_TOKEN_URL, data=data)
    return res.json()


def google_get_userinfo(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    return res.json()
