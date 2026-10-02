import base64, hashlib, hmac, json, time
from .config import APP_SECRET

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def create_token(subject: str) -> str:
    payload = _b64(json.dumps({'sub': subject, 'exp': int(time.time()) + 60*60*24}).encode())
    sig = _b64(hmac.new(APP_SECRET.encode(), payload.encode(), hashlib.sha256).digest())
    return f'{payload}.{sig}'

def read_token(token: str) -> str | None:
    try:
        payload, signature = token.split('.', 1)
        expected = _b64(hmac.new(APP_SECRET.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): return None
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        return data['sub'] if data['exp'] > time.time() else None
    except Exception:
        return None
