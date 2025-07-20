```python
import pytest
from flask import Flask
from unittest.mock import patch

@pytest.fixture
def client():
    """Create test client"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/api/test', methods=['GET'])
    def test_get():
        return {"message": "success"}
    
    @app.route('/api/test', methods=['POST'])
    def test_post():
        return {"message": "created"}
    
    with app.test_client() as client:
        yield client

class TestFlaskEndpoints:
    
    def test_get_endpoint_should_return_success(self, client):
        """Test GET endpoint"""
        response = client.get('/api/test')
        assert response.status_code == 200
        assert response.json['message'] == 'success'

    def test_post_endpoint_should_accept_data(self, client):
        """Test POST endpoint"""
        response = client.post('/api/test', json={"test": "data"})
        assert response.status_code == 200
        assert response.json['message'] == 'created'

    def test_endpoint_error_handling(self, client):
        """Test error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
```