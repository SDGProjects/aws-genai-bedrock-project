import json

from loguru import logger as log


# Temporarily hardcoding model IDs but this is not being used
# The get_foundation_model_ids gets this list dynamically
# keeping this for verbosity and clarity
BEDROCK_MODEL_IDS = [
    "amazon.titan-tg1-large",
    "amazon.titan-text-lite-v1",
    "amazon.titan-text-express-v1",
    "ai21.j2-grande-instruct",
    "ai21.j2-jumbo-instruct",
    "ai21.j2-mid",
    "ai21.j2-mid-v1",
    "ai21.j2-ultra",
    "ai21.j2-ultra-v1",
    "anthropic.claude-instant-v1",
    "anthropic.claude-v1",
    "anthropic.claude-v2:1",
    "anthropic.claude-v2",
    "cohere.command-text-v14",
    "cohere.command-light-text-v14",
    "meta.llama2-13b-chat-v1",
    "meta.llama2-70b-chat-v1",
]

# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html
MODEL_INVOKE_BODY_MAP = {
    "amazon.titan": {
        "inputText": "${{message}}",
        "textGenerationConfig": {
            "maxTokenCount": 4096,
            "stopSequences": [],
            "temperature": 0,
            "topP": 1,
        },
    },
    "ai21.j2": {
        "prompt": "${{message}}",
        "maxTokens": 200,
        "temperature": 0.5,
        "topP": 0.5,
    },
    "anthropic.claude": {
        "prompt": "\n\nHuman: ${{message}}\n\nAssistant:",
        "max_tokens_to_sample": 300,
        "temperature": 0.1,
        "top_p": 0.9,
    },
    "cohere.command": {
        "prompt": "${{message}}",
        "max_tokens": 200,
        "temperature": 0.5,
        "p": 0.5,
    },
    "meta.llama2": {
        "prompt": "${{message}}",
        "max_gen_len": 128,
        "temperature": 0.1,
        "top_p": 0.9,
    },
}


def get_model_id_key(model_id: str) -> str:
    return model_id.split("-")[0]


def get_foundation_model_ids(client) -> list:
    """
    Returns the IDs of all the text based foundation models
    """
    response = client.list_foundation_models(
        byOutputModality="TEXT",
        byInferenceType="ON_DEMAND",
    )
    return [model["modelId"] for model in response["modelSummaries"]]


def get_model_invoke_body(model_id: str, message: str) -> json:
    body_key = get_model_id_key(model_id)
    if body_key not in MODEL_INVOKE_BODY_MAP:
        raise ValueError(f"Model ID {model_id} not found in MODEL_INVOKE_BODY_MAP")

    invoke_body = dict(MODEL_INVOKE_BODY_MAP[body_key])
    if "prompt" in invoke_body:
        invoke_body["prompt"] = invoke_body["prompt"].replace("${{message}}", message)
    elif "inputText" in invoke_body:
        invoke_body["inputText"] = invoke_body["inputText"].replace(
            "${{message}}", message
        )
    return json.dumps(invoke_body)


def invoke_model(client_runtime, model_id: str, invoke_body: json) -> str:
    """
    Invokes the specified model with the given input text
    """
    accept = "application/json"
    content_type = "application/json"
    response = client_runtime.invoke_model(
        modelId=model_id,
        body=invoke_body,
        accept=accept,
        contentType=content_type,
    )
    model_key = get_model_id_key(model_id)
    response_body = json.loads(response.get("body").read())

    if model_key == "amazon.titan":
        return response_body["results"][0]["outputText"]
    if model_key == "ai21.j2":
        return response_body["completions"][0]["data"]["text"]
    if model_key == "anthropic.claude":
        return response_body["completion"]
    if model_key == "cohere.command":
        return response_body["generations"][0]["text"]
    if model_key == "meta.llama2":
        return response_body["generation"]
    return None
