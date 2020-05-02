import json
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)


def test_hello_world():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World during \
the coronavirus pandemic!"}


def test_get_tracks():
    with TestClient(app) as client:
        response = client.get('/tracks?page=1&per_page=20')
        assert len(response.json()) == 20
        assert response.json()[0]['TrackId'] == 21
        assert response.status_code == 200


def test_get_composers_work():
    with TestClient(app) as client:
        response = client.get('/tracks/composers/?composer_name=Kurt Cobain')
        bad_response = client.get('/tracks/composers/?composer_name=x2137x')
        assert response.status_code == 200
        assert bad_response.status_code == 404


def test_add_album():
    with TestClient(app) as client:
        bad_response = client.post(
            '/albums',
            data=json.dumps(dict(title="test", artist_id="9999999")))
        assert bad_response.status_code == 404
        response = client.post(
            '/albums',
            data=json.dumps(dict(title="test", artist_id="1")))
        assert response.status_code == 201
        new_album_id = response.json()['AlbumId']
        response = client.get(f'/albums/{new_album_id}')
        assert response.status_code == 200


def test_edit_customer():
    with TestClient(app) as client:
        response = client.put(
            '/customers/1',
            data=json.dumps(dict(
                # company="TestCompany",
                # address="Street",
                city="SomeCity",
                state="Ohio",
                country="United States",
                postalcode="000001",
                fax="51515151"
            ))
        )
        assert response.status_code == 200

        bad_response = client.put(
            '/customers/9999999',
            data=json.dumps(dict(city="SimCity"))
        )

        assert bad_response.status_code == 404
