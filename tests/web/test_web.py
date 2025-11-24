from fastapi.testclient import TestClient


def test_home_page_renders(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Global Feed" in response.text


def test_new_article_requires_auth(client: TestClient) -> None:
    response = client.get("/article/new", allow_redirects=False)
    assert response.status_code in (302, 303)
    assert response.headers["location"].startswith("/login")
