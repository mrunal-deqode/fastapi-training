import jwt

from utils.jwt import (
    create_access_token,
    create_refresh_token,
)
from config import JWT_SECRET_KEY, JWT_ALGORITHM

from utils.jwt import verify_token


data = {
    "sub": "15",
    "role": "super_admin",
}

access_token = create_access_token(data)
refresh_token = create_refresh_token(data)

print("Access Token:", access_token)
print("Refresh Token:", refresh_token)

decoded = jwt.decode(
    access_token,
    JWT_SECRET_KEY,
    algorithms=[JWT_ALGORITHM],
)

print("\nDecoded Access Token:")
print(decoded)

assert decoded["type"] == "access"
assert decoded["sub"] == "15"
assert decoded["role"] == "super_admin"

print("\nJWT generation and verification successful!")

payload = verify_token(access_token)

print("Verified User ID:", payload["sub"])
print("Verified Role:", payload["role"])
print("Verified Token Type:", payload["type"])
