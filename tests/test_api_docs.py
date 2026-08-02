"""Tests for the developer-facing API documentation."""


def test_openapi_spec_is_served(client):
    response = client.get("/api/openapi.yaml")

    assert response.status_code == 200
    assert response.mimetype == "application/yaml"
    assert b"openapi: 3.0.3" in response.data
    assert b"/health/live:" in response.data
    assert b"/api/v1/auth/register:" in response.data
    assert b"/api/v1/auth/login:" in response.data
    assert b"/api/v1/auth/me:" in response.data
    assert b"/api/v1/auth/protected:" in response.data
    assert b"/api/v1/auth/refresh:" in response.data
    assert b"/api/v1/auth/logout:" in response.data
    assert b"/api/v1/users/{user_id}:" in response.data
    assert b"/api/v1/authorization/roles:" in response.data
    assert b"/api/v1/authorization/permissions:" in response.data
    assert b"/api/v1/security/forgot-password:" in response.data
    assert b"/api/v1/security/audit-logs:" in response.data
    assert b"bearerAuth:" in response.data


def test_swagger_ui_uses_the_shared_openapi_spec(client):
    response = client.get("/api/docs")

    assert response.status_code == 200
    assert b'id="swagger-ui"' in response.data
    assert b"/api/openapi.yaml" in response.data
    assert b"swagger-ui-bundle.js" in response.data
