from app.security import decode, hash_password, tokens, verify_password


def test_password_and_tokens():
    stored = hash_password("secret123")
    assert verify_password("secret123", stored)
    assert not verify_password("bad", stored)
    pair = tokens("user-id")
    assert decode(pair["access_token"], "access") == "user-id"

