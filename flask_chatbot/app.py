from flask import Flask, render_template, request
from loguru import logger as log

# Local imports
import utils.bedrock as bedrock


def page_not_found(e):
    return render_template("404.html"), 404


app = Flask(__name__)
app.register_error_handler(404, page_not_found)


AWS_REGION = "us-east-1"
br_agent_client = bedrock.get_bedrock_agent_client(AWS_REGION)
br_agent_rt_client = bedrock.get_bedrock_agent_runtime_client(AWS_REGION)

BEDROCK_KNOWLEDGE_BASE_NAME = "demo-rag"


# Update ./templates/index.html from `url: "/get_bedrock_rag_response"`
# to `url: "/get_bedrock_response"` to use the Bedrock API without RAG
@app.route("/get_bedrock_response")
def get_bedrock_response() -> str:
    # Make a request to the Amazon Bedrock API
    model_id = request.args.get("model_id")
    message = request.args.get("chat_input_val")
    invoke_body = bedrock.get_model_invoke_body(model_id, message)

    log.info(f"Querying Amazon Bedrock - Model: {model_id} Message: '{invoke_body}'")
    client_runtime = bedrock.get_bedrock_runtime_client(AWS_REGION)
    response = bedrock.invoke_model(client_runtime, model_id, invoke_body)
    log.info(f"Response from Amazon Bedrock: '{response}'")
    if response is None:
        return "No response from Amazon Bedrock"
    return response


@app.route("/get_bedrock_rag_response")
def get_bedrock_rag_response() -> str:
    # Make a request to the Amazon Bedrock API
    model_id = request.args.get("model_id")
    message = request.args.get("chat_input_val")

    kb_id = bedrock.get_knowledge_base_id(br_agent_client, BEDROCK_KNOWLEDGE_BASE_NAME)
    log.info(f"Knowledge base ID: {kb_id}")
    model_arn = f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{model_id}"

    log.info(f"Querying Amazon Bedrock - Model: {model_id} Message: '{message}'")
    response = bedrock.invoke_knowledge_base(
        br_agent_rt_client,
        message,
        kb_id,
        model_arn,
    )

    log.info(f"Response from Amazon Bedrock: '{response}'")
    log.info(f"Answer: {response['output']['text']}")
    return response["output"]["text"]


@app.route("/", methods=["POST", "GET"])
def index():
    client = bedrock.get_bedrock_client(AWS_REGION)
    models = bedrock.get_foundation_model_ids(client)
    log.debug(f"Available models: {models}")
    return render_template("index.html", models=models)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5100", debug=True)
