from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_function1():
# testing function to insert a single dataset
    
