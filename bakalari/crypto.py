import base64

from Crypto import Random
from Crypto.Cipher import AES

from SchoolTools.settings import EMAIL_LINK_ENCRYPTION_KEY

BS = 16


def pad(b: bytes):
    l = BS - (len(b) % BS)
    if l == 0:
        l = 16
    return b + bytes([l] * l)


def unpad(b: bytes):
    return b[0:-b[-1]]


def encrypt(text: str) -> str:
    raw = pad(text.encode())
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(EMAIL_LINK_ENCRYPTION_KEY, AES.MODE_CFB, iv)
    return base64.b64encode(iv + cipher.encrypt(raw)).decode()


def decrypt(enc_b64: str) -> str:
    enc = base64.b64decode(enc_b64)
    iv = enc[:16]
    cipher = AES.new(EMAIL_LINK_ENCRYPTION_KEY, AES.MODE_CFB, iv)
    return unpad(cipher.decrypt(enc[16:])).decode()
