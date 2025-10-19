import requests
import base64
import json
from databricks.sdk.runtime import dbutils




class Auth:
    def __init__(self):
        self.client_id = dbutils.secrets.get(scope="spotify_secrets", key="user")
        self.client_secret = dbutils.secrets.get(scope="spotify_secrets", key="client_secret")
        

    def get_access_token(self):
        # 1. Codificare Base64 pentru Client ID și Client Secret
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        auth_url = "https://accounts.spotify.com/api/token"

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}
        response = requests.post(auth_url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception("Nu s-a putut reîmprospăta token-ul.")

    def get_authorization_header(self, token):
        return {"Authorization": f"Bearer {token}"}
