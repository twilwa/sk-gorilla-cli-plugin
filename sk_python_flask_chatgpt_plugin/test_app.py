from unittest import mock

import pytest
from flask import json
from sk_python_flask_chatgpt_plugin.app import app


@pytest.mark.parametrize("skill_name,function_name,request_data,expected_response", [
    ("TestSkill", "TestFunction", {"headers": {"x-skill-name": "TestSkill"}}, "Test response"),
    ("InvalidSkill", "TestFunction", {"headers": {"x-skill-name": "InvalidSkill"}}, "Could not find function TestFunction in skill InvalidSkill"),
])
def test_execute_semantic_function(skill_name, function_name, request_data, expected_response):
    with mock.patch("sk_python_flask_chatgpt_plugin.app.create_kernel_for_request") as mock_create_kernel:
        mock_create_kernel.return_value = (mock.MagicMock(), None)
        with app.test_client() as client:
            response = client.post(f"/skills/{skill_name}/functions/{function_name}", headers=request_data.get("headers"))
            assert response.data.decode() == expected_response

def test_execute_joke():
    with mock.patch("sk_python_flask_chatgpt_plugin.app.execute_semantic_function") as mock_execute:
        mock_execute.return_value = "Test joke"
        with app.test_client() as client:
            response = client.post("/joke")
            assert response.data.decode() == "Test joke"

@pytest.mark.parametrize("request_data,expected_response", [
    ({"command": "Test command"}, {"queued_commands": ["Test command"]}),
    ({"command": "Invalid command"}, {"queued_commands": []}),
])
def test_queue_gorilla_commands(request_data, expected_response):
    with mock.patch("sk_python_flask_chatgpt_plugin.app.GorillaPlugin") as mock_gorilla:
        mock_gorilla.return_value.queue_commands.return_value = expected_response
        with app.test_client() as client:
            response = client.post("/gorilla/queue-commands", data=json.dumps(request_data), content_type="application/json")
            assert json.loads(response.data.decode()) == expected_response

def test_get_ai_plugin():
    with app.test_client() as client:
        response = client.get("/.well-known/ai-plugin.json")
        assert response.status_code == 200

def test_get_logo():
    with app.test_client() as client:
        response = client.get("/logo.png")
        assert response.status_code == 200

def test_get_openapi():
    with app.test_client() as client:
        response = client.get("/openapi.yaml")
        assert response.status_code == 200
