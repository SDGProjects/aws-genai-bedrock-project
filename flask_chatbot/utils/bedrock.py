import boto3
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


def get_bedrock_client(region: str):
    return boto3.client("bedrock", region_name=region)


def get_bedrock_runtime_client(region: str):
    return boto3.client("bedrock-runtime", region_name=region)


def get_bedrock_agent_client(region: str):
    return boto3.client("bedrock-agent", region_name=region)


def get_bedrock_agent_runtime_client(region: str):
    return boto3.client("bedrock-agent-runtime", region_name=region)


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


def invoke_model(client, model_id: str, invoke_body: json) -> str:
    """
    Invokes the specified model with the given input text
    """
    accept = "application/json"
    content_type = "application/json"
    response = client.invoke_model(
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


def invoke_knowledge_base(client, prompt: str, kb_id: str, model_arn: str):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/retrieve_and_generate.html#AgentsforBedrockRuntime.Client.retrieve_and_generate
    response = client.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn,
            },
        },
    )
    return response


def get_knowledge_base_id(client, name: str) -> str:
    knowledge_bases = client.list_knowledge_bases()["knowledgeBaseSummaries"]
    if not knowledge_bases:
        log.error("No knowledge bases found")
        return ""

    knowledge_base_id = ""
    for kb in knowledge_bases:
        if kb["name"] == name:
            knowledge_base_id = kb["knowledgeBaseId"]
            break
    if not knowledge_base_id:
        log.error(f"Knowledge base '{name}' not found in {knowledge_bases}")

    log.info(f"Knowledge base ID: {knowledge_base_id}")
    return knowledge_base_id


def get_knowledge_base_config(client, knowledge_base_id: str) -> dict:
    response = client.get_knowledge_base(knowledgeBaseId=knowledge_base_id)
    return {
        "knowledgeBaseId": knowledge_base_id,
        "modelArn": response["knowledgeBase"]["knowledgeBaseArn"],
    }
