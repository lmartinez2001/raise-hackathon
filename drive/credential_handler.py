import os
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired


class CredentialHandler:
    def __init__(
        self,
        scopes,
        client_secrets_file,
        session_duration,
        redirect_uri,
    ):
        self.client_secrets_file = client_secrets_file
        self.redirect_uri = redirect_uri
        self.token_file = "token.json"
        self.scopes = scopes
        self.signer = TimestampSigner("super-secret-key")
        self.session_duration = session_duration

    def get_auth_url(self):
        """Generate authorization URL for OAuth flow"""

        flow = Flow.from_client_secrets_file(
            self.client_secrets_file, scopes=self.scopes, redirect_uri=self.redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="false",
            prompt="consent",
        )

        return authorization_url, state, flow

    def fetch_token(self, authorization_response, flow):
        """Exchange authorization code for access token"""
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        return credentials

    def fetch_user_info(self, credentials: Credentials):
        """Fetch user information from Google UserInfo API"""
        try:

            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return {}

    def get_credentials(self, request: Request) -> dict | None:
        session_token = request.cookies.get("session_token")
        if session_token is None:
            return None
        try:
            data = self.signer.unsign(session_token, max_age=self.session_duration)
            token = json.loads(data)
            creds = Credentials.from_authorized_user_info(token)
            return creds
        except (BadSignature, SignatureExpired):
            return None

    def create_session_token(self, token_data: dict) -> str:
        """Create a signed session token"""
        data = json.dumps(token_data).encode()
        return self.signer.sign(data).decode()

    # def _save_credentials(self, credentials):
    #     """Save credentials to token file"""
    #     with open(self.token_file, "w") as token_file:
    #         token_file.write(credentials.to_json())
