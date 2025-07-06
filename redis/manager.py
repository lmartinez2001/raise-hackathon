import json
import uuid
import redis
from google.oauth2.credentials import Credentials


class RedisManager:
    def __init__(self, host="localhost", port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, decode_responses=True
        )

    def generate_client_id(self):
        return str(uuid.uuid4())

    def store_client_token(self, client_id: str, token_data: dict, ttl: int):
        key = f"client:{client_id}:token"
        self.redis_client.setex(key, ttl, json.dumps(token_data))

    def get_client_token(self, client_id: str) -> dict | None:
        key = f"client:{client_id}:token"
        token_data = self.redis_client.get(key)
        if token_data:
            return json.loads(token_data)
        return None

    def delete_client_token(self, client_id: str):
        key = f"client:{client_id}:token"
        self.redis_client.delete(key)

    def refresh_client_token_ttl(self, client_id: str, ttl: int):
        key = f"client:{client_id}:token"
        self.redis_client.expire(key, ttl)

    def client_exists(self, client_id: str) -> bool:
        key = f"client:{client_id}:token"
        return self.redis_client.exists(key) > 0

    def get_client_credentials(self, client_id: str) -> Credentials | None:
        token_data = self.get_client_token(client_id)
        if token_data:
            return Credentials.from_authorized_user_info(token_data)
        return None


if __name__ == "__main__":
    # Example usage
    manager = RedisManager()
    client_id = manager.generate_client_id()
    token_data = {
        "token": "example_token",
        "refresh_token": "example_refresh_token",
        "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/drive",
        "token_type": "Bearer",
    }
    manager.store_client_token(client_id, token_data, ttl=3600)
    print(f"Stored token for client {client_id}: {manager.get_client_token(client_id)}")
    print(f"Client exists: {manager.client_exists(client_id)}")
    manager.refresh_client_token_ttl(client_id, ttl=7200)
    print(f"Token after refresh: {manager.get_client_token(client_id)}")
    manager.delete_client_token(client_id)
    print(f"Client exists after deletion: {manager.client_exists(client_id)}")
    print(f"Credentials: {manager.get_client_credentials(client_id)}")
