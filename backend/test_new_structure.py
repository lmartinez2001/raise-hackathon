"""
Quick validation test for the new modular FastAPI structure.
Tests that all endpoints are accessible and return expected responses.
"""

from fastapi.testclient import TestClient
from server_new import app

client = TestClient(app)


def test_health_endpoint():
    """Test the new health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hackathon-backend"
    print("✅ Health endpoint working")


def test_main_page():
    """Test the main page renders."""
    response = client.get("/")
    assert response.status_code == 200
    # Should return HTML
    assert "text/html" in response.headers["content-type"]
    print("✅ Main page accessible")


def test_auth_endpoints_structure():
    """Test auth endpoints are accessible (but will need auth)."""
    # Login endpoint should redirect
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 302  # Redirect to Google OAuth
    print("✅ Auth login redirect working")

    # Status endpoint should work without auth
    response = client.get("/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data
    assert data["authenticated"] == False
    print("✅ Auth status endpoint working")


def test_drive_endpoints_need_auth():
    """Test drive endpoints properly require authentication."""
    endpoints = ["/drive/files", "/drive/tree", "/drive/videos"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401  # Unauthorized
        print(f"✅ {endpoint} properly requires auth")


def test_api_docs():
    """Test that API documentation is accessible."""
    # OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    print("✅ OpenAPI spec accessible")

    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    print("✅ Swagger UI accessible")


def run_all_tests():
    """Run all validation tests."""
    print("🧪 Testing New Modular FastAPI Structure")
    print("=" * 45)

    try:
        test_health_endpoint()
        test_main_page()
        test_auth_endpoints_structure()
        test_drive_endpoints_need_auth()
        test_api_docs()

        print("\n🎉 All tests passed!")
        print("✅ New modular structure is working correctly")
        print("✅ All endpoints accessible with proper auth handling")
        print("✅ API documentation generated successfully")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
