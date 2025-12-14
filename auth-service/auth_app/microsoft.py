import msal
import requests
from django.conf import settings

def microsoft_exchange_code(code):
    client = msal.ConfidentialClientApplication(
        client_id=settings.SOCIAL_AUTH["MICROSOFT_CLIENT_ID"],
        client_credential=settings.SOCIAL_AUTH["MICROSOFT_CLIENT_SECRET"],
        authority=f"https://login.microsoftonline.com/{settings.SOCIAL_AUTH['MICROSOFT_TENANT_ID']}"
    )

    result = client.acquire_token_by_authorization_code(
        code=code,
        scopes=["openid", "profile", "email"],
        redirect_uri=settings.SOCIAL_AUTH["MICROSOFT_REDIRECT_URI"]
    )
    return result


def microsoft_get_userinfo(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    return res.json()
