from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_hash():
    hashed = hash_password("Secure123")
    assert hashed != "Secure123"
    assert verify_password("Secure123", hashed)


def test_access_token():
    assert decode_token(create_token(42)) == 42
