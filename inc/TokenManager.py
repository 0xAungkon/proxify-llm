from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib
import json
from config.settings import settings

SECRET_KEY = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()


def _restore_padding(value: str) -> str:
    return value + ("=" * (-len(value) % 4))

def encrypt_token(data: str) -> str:
    try:
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        payload = {
            "iv": base64.urlsafe_b64encode(cipher.iv).decode("utf-8"),
            "cipher_text": base64.urlsafe_b64encode(ct_bytes).decode("utf-8"),
        }
        token = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        return {"status": "success", "token": token}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def decrypt_token(encrypted_data: str) -> str:
    try:
        decoded_payload = base64.urlsafe_b64decode(
            _restore_padding(encrypted_data).encode("utf-8")
        ).decode("utf-8")
        b64 = json.loads(decoded_payload)
        iv = base64.urlsafe_b64decode(_restore_padding(b64["iv"]))
        ct = base64.urlsafe_b64decode(_restore_padding(b64["cipher_text"]))
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return {"status": "success", "data": pt.decode()}
    except Exception as e:
        return {"status": "error", "message": str(e)}