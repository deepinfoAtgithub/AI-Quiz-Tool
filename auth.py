# auth.py
import msal
import streamlit as st

# Load credentials from secrets
CLIENT_ID = st.secrets["ENTRA_CLIENT_ID"]
CLIENT_SECRET = st.secrets["ENTRA_CLIENT_SECRET"]
TENANT_NAME = st.secrets["ENTRA_TENANT_NAME"]

# The modern CIAM endpoints use .ciamlogin.com
AUTHORITY = f"https://{TENANT_NAME}.ciamlogin.com/{TENANT_NAME}.onmicrosoft.com"
REDIRECT_URI = st.secrets["ENTRA_REDIRECT_URI"]

# auth.py
# Use the full URL-style scopes which are often safer in CIAM/B2C environments
SCOPE = ["User.Read"]

def get_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID, 
        authority=AUTHORITY, 
        client_credential=CLIENT_SECRET
    )

def get_login_url():
    app = get_msal_app()
    auth_url = app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    return auth_url

def get_token_from_code(code):
    app = get_msal_app()
    result = app.acquire_token_by_authorization_code(code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
    return result