"""
A simple script to ask a question to an Amazon Bedrock
knowledge base and Bedrock FM.

Pre-requisites:
- Run the create_knowledge_base.py script to create a knowledge base

Call with:
python ask_bedrock_knowledge_base.py
"""
import boto3
import utils

from loguru import logger as log


# Update as needed
AWS_REGION = "us-east-1"
MODEL_ID = "anthropic.claude-v2"
KNOWLEDGE_BASE_NAME = "demo-rag"

br_agent_client = boto3.client("bedrock-agent")
br_agent_rt_client = boto3.client("bedrock-agent-runtime")
log.info("Amazon Bedrock clients created")


def main():
    log.info(f"Using Model ID: {MODEL_ID}")
    prompt = input("Enter your prompt: ")

    # Knowledge base created from the create_knowledge_base.py script
    kb_id = utils.get_knowledge_base_id(br_agent_client, KNOWLEDGE_BASE_NAME)
    model_arn = f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{MODEL_ID}"

    response = utils.invoke_knowledge_base(br_agent_rt_client, prompt, kb_id, model_arn)
    log.info(f"Response: {response}")
    log.info(f"Answer: {response['output']['text']}")


if __name__ == "__main__":
    main()
