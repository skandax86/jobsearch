"""Auth API integration tests (requires local Postgres + Redis)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_login_me_logout(client, unique_email):
    password = "securepass123"

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password, "display_name": "Test User"},
    )
    assert register.status_code == 201, register.text
    body = register.json()
    assert body["errors"] == []
    token = body["data"]["access_token"]
    assert body["data"]["user"]["email"] == unique_email
    assert body["data"]["candidate_profile"]["id"]

    me = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["data"]["user"]["email"] == unique_email
    assert me_body["data"]["candidate_profile"] is not None

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login.status_code == 200
    login_token = login.json()["data"]["access_token"]
    assert login_token

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_token}"},
    )
    assert logout.status_code == 200

    me_after = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {login_token}"},
    )
    assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client, unique_email):
    payload = {"email": unique_email, "password": "securepass123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["errors"][0]["code"] == "email_taken"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, unique_email):
    await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "securepass123"},
    )
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["errors"][0]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
