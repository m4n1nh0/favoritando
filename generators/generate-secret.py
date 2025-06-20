import os
import secrets

secret_key_exemplo_1 = os.urandom(16).hex()
print(f"(16 bytes): {secret_key_exemplo_1}")

secret_key_exemplo_2 = secrets.token_urlsafe(24)
print(f"(24 bytes): {secret_key_exemplo_2}")

secret_key_exemplo_3 = secrets.token_hex(32)
print(f"(32 bytes): {secret_key_exemplo_3}")