from careerpilot.domains.identity.passwords import hash_password, verify_password
from careerpilot.domains.identity.tokens import generate_session_token, hash_session_token


def test_password_hash_roundtrip():
    hashed = hash_password("securepass123")
    assert hashed != "securepass123"
    assert verify_password("securepass123", hashed)
    assert not verify_password("nope", hashed)


def test_session_token_hash_is_stable():
    token = generate_session_token()
    assert hash_session_token(token) == hash_session_token(token)
    assert hash_session_token(token) != token
