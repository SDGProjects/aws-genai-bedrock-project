import boto3

from flask import Flask, render_template, request
from loguru import logger as log

# Local imports
from bedrock_utils import get_foundation_model_ids, invoke_model, get_model_invoke_body


def page_not_found(e):
    return render_template("404.html"), 404


app = Flask(__name__)
app.register_error_handler(404, page_not_found)

client = boto3.client("bedrock")
client_runtime = boto3.client("bedrock-runtime")


@app.route("/get_bedrock_response")
def get_bedrock_response() -> str:
    # Make a request to the Amazon Bedrock API
    model_id = request.args.get("model_id")
    message = request.args.get("chat_input_val")
    invoke_body = get_model_invoke_body(model_id, message)

    log.info(f"Querying Amazon Bedrock - Model: {model_id} Message: '{invoke_body}'")
    response = invoke_model(client_runtime, model_id, invoke_body)
    log.info(f"Response from Amazon Bedrock: '{response}'")
    if response is None:
        return "No response from Amazon Bedrock"
    return response


@app.route("/", methods=["POST", "GET"])
def index():
    models = get_foundation_model_ids(client)
    log.debug(f"Available models: {models}")
    return render_template("index.html", models=models)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5100", debug=True)
