import os, base64, urllib.parse, webbrowser, requests, json, time
from databricks.sdk.runtime import dbutils



CLIENT_ID =  "9c22135f704248acb4c79520646559c3"
CLIENT_SECRET ="7d81b48def1e427580328769dd1349df"
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPES = "user-read-recently-played user-read-playback-state user-read-currently-playing"
TOKENS_PATH = "/Workspace/Users/pacioianu4@gmail.com/spotify-end-to-end-api-project/src/config/spotify_tokens.json"



def build_authorize_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "show_dialog": "true"
    }
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)



def exchange_code_for_tokens(code: str) -> dict:
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
        timeout=20,
    )
    r.raise_for_status()
    tok = r.json()
    tok["expires_at"] = int(time.time()) + int(tok.get("expires_in", 3600)) - 30
    return tok



def refresh_access_token(refresh_token: str) -> dict:
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=15,
    )
    r.raise_for_status()
    j = r.json()
    j["expires_at"] = int(time.time()) + int(j.get("expires_in", 3600)) - 30
    if "refresh_token" not in j:
        j["refresh_token"] = refresh_token  # păstrează-l dacă nu s-a rotit
    return j




def get_valid_token() -> str:
    # Încarcă/obține token valabil; face refresh automat.
    if not os.path.exists(TOKENS_PATH):
        raise RuntimeError("Nu există spotify_tokens.json. Rulează întâi flow-ul de autorizare.")
    with open(TOKENS_PATH, "r", encoding="utf-8") as f:
        tok = json.load(f)
    if tok.get("expires_at", 0) <= int(time.time()):
        tok_new = refresh_access_token(tok["refresh_token"])
        tok.update(tok_new)
        with open(TOKENS_PATH, "w", encoding="utf-8") as f:
            json.dump(tok, f, indent=2)
    return tok["access_token"]


