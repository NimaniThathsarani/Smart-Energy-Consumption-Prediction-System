from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_forecast():
    response = client.get("/forecast?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] <= 5
    assert isinstance(data["data"], list)


def test_peak():
    response = client.get("/peak?limit=3")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] <= 3
    assert isinstance(data["data"], list)


def test_anomalies():
    response = client.get("/anomalies?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] <= 5
    assert isinstance(data["data"], list)


def test_clusters():
    response = client.get("/clusters?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] <= 5
    assert "records" in data["data"]
    assert "cluster_info" in data["data"]


def test_recommendations():
    response = client.get("/recommendations?limit=3")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] <= 3
    assert isinstance(data["data"], list)


def test_model_performance():
    response = client.get("/model-performance")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert isinstance(data["data"], list)


def test_forecast_invalid_limit():
    response = client.get("/forecast?limit=0")

    assert response.status_code == 422


def test_peak_invalid_limit():
    response = client.get("/peak?limit=0")

    assert response.status_code == 422


def test_anomalies_invalid_limit():
    response = client.get("/anomalies?limit=0")

    assert response.status_code == 422


def test_clusters_invalid_limit():
    response = client.get("/clusters?limit=0")

    assert response.status_code == 422


def test_recommendations_invalid_limit():
    response = client.get("/recommendations?limit=0")

    assert response.status_code == 422