import os
import json
import secrets
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired


class CredentialHandler:
    def __init__(
        self, scopes, client_secrets_file, session_duration, redirect_uri, secret_key
    ):
        self.client_secrets_file = client_secrets_file
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.signer = TimestampSigner(secret_key)
        self.session_duration = session_duration

    def get_auth_url(self):
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file, scopes=self.scopes, redirect_uri=self.redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="false",
            prompt="consent",
        )

        flow_state = {
            "client_id": flow.client_config["client_id"],
            "client_secret": flow.client_config["client_secret"],
            "redirect_uri": self.redirect_uri,
            "scopes": self.scopes,
        }
        signed_flow_state = self.signer.sign(json.dumps(flow_state).encode()).decode()
        return authorization_url, state, signed_flow_state

    def create_flow_from_state(self, flow_state):
        try:
            state_data = json.loads(self.signer.unsign(flow_state, max_age=300))
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": state_data["client_id"],
                        "client_secret": state_data["client_secret"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [state_data["redirect_uri"]],
                    }
                },
                scopes=state_data["scopes"],
                redirect_uri=state_data["redirect_uri"],
            )
            return flow
        except (BadSignature, SignatureExpired):
            return None

    def fetch_token(self, authorization_response, flow_state):
        flow = self.create_flow_from_state(flow_state)
        if not flow:
            return None

        flow.fetch_token(authorization_response=authorization_response)
        return flow.credentials

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
