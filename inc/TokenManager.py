from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib
import json
from config.settings import settings

SECRET_KEY = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()

def encrypt_token(data: str) -> str:
    try:
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return json.dumps({"status": "success", "iv": iv, "cipher_text": ct})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def decrypt_token(encrypted_data: str) -> str:
    try:
        b64 = json.loads(encrypted_data)
        iv = base64.b64decode(b64['iv'])
        ct = base64.b64decode(b64['cipher_text'])
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return json.dumps({"status": "success", "data": pt.decode()})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})