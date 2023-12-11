import os
import logging
from flask import Flask, request, Response, send_file
from flask_cors import CORS
from semantic_kernel.kernel_exception import KernelException

from sk_python_flask_chatgpt_plugin.kernel_utils import (
    create_kernel_for_request,
    create_context_variables_from_request,
)


app = Flask(__name__)
CORS(app)


@app.route("/skills/<skill_name>/functions/<function_name>", methods=["POST"])
def execute_semantic_function(skill_name, function_name):
    logging.info(
        f"Received request for skill {skill_name} and function {function_name}"
    )

    kernel, error = create_kernel_for_request(request.headers, skill_name)
    if error:
        return error
    try:
        sk_func = kernel.skills.get_function(skill_name, function_name)
    except KernelException:
        logging.exception(
            f"Could not find function {function_name} in skill {skill_name}"
        )
        return f"Could not find function {function_name} in skill {skill_name}", 404

    context_variables = create_context_variables_from_request(request)

    result = sk_func(variables=context_variables)

    logging.info(f"Result: {result}")
    return str(result)

@app.route("/joke", methods=["POST"])
def execute_joke():
    return execute_semantic_function("FunSkill", "Joke")

@app.route("/gorilla/queue-commands", methods=["POST"])
def queue_gorilla_commands():
    from .gorilla_plugin import GorillaPlugin
    import json
    import requests

    # Initialize GorillaPlugin with the path to the Gorilla CLI
    gorilla_plugin = GorillaPlugin(cli_path=os.getenv('GORILLA_CLI_PATH'))

    # Get the natural language command from the request
    data = request.get_json()
    natural_language_command = data.get('command', '')
    if api_endpoint_url := request.args.get('api_endpoint', None):
        # Send the natural language command to the provided API endpoint
        response = requests.post(api_endpoint_url, json={'command': natural_language_command})
        if response.status_code != 200:
            return f"Failed to get commands from API endpoint. Status code: {response.status_code}", 500
        queued_commands = response.json().get('commands', [])
    else:
        # Process the natural language command locally and queue CLI commands
        queued_commands = gorilla_plugin.queue_commands([natural_language_command])

    # Return the queued commands as a JSON response
    return json.dumps({'queued_commands': queued_commands}), 200

@app.route("/.well-known/ai-plugin.json", methods=["GET"])
def get_ai_plugin():
    with open("./.well-known/ai-plugin.json", "r") as f:
        text = f.read()
        return Response(text, status=200, mimetype="text/json")


@app.route("/logo.png")
def get_logo():
    return send_file("../logo.png", mimetype="image/png")


@app.route("/openapi.yaml", methods=["GET"])
def get_openapi():
    with open("./openapi.yaml", "r") as f:
        text = f.read()
        return Response(text, status=200, mimetype="text/yaml")
