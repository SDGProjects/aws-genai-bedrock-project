import boto3
import time

from loguru import logger as log

# Constants
AWS_REGION = "us-east-1"
KB_NAME = "demo-rag"
KB_DESCRIPTION = "Demo knowledge base for RAG"
BEDROCK_FM = "amazon.titan-embed-text-v1"
BEDROCK_EMBED_MODEL_ARN = f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{BEDROCK_FM}"
OS_COLLECTION_NAME = f"{KB_NAME}-os-collection"
OS_VECTOR_PREFIX = "bedrock-knowledge-base-default"
OS_POLICY_NAME = "bedrock-security-policy"

# Output from ./terraform apply
KB_ROLE_NAME = "AmazonBedrockExecutionRoleForKnowledgeBase_Default"


def get_bedrock_s3_bucket_name() -> str:
  client = boto3.client("s3")
  response = client.list_buckets()
  for bucket in response["Buckets"]:
    if bucket["Name"].startswith("amazon-bedrock-knowledge-base"):
      return bucket["Name"]
  return ""


def get_aws_iam_role_arn(name: str) -> str:
    client = boto3.client("iam")
    response = client.get_role(RoleName=name)
    return response["Role"]["Arn"]


def get_shared_consts() -> dict:
    kb_role_arn = get_aws_iam_role_arn(KB_ROLE_NAME)
    kb_bucket_name = get_bedrock_s3_bucket_name()
    kb_bucket_arn = f"arn:aws:s3:::{kb_bucket_name}"
    return {
        "AWS_REGION": AWS_REGION,
        "KB_NAME": KB_NAME,
        "KB_DESCRIPTION": KB_DESCRIPTION,
        "KB_BUCKET_NAME": kb_bucket_name,
        "KB_BUCKET_ARN": kb_bucket_arn,
        "BEDROCK_FM": BEDROCK_FM,
        "BEDROCK_EMBED_MODEL_ARN": BEDROCK_EMBED_MODEL_ARN,
        "OS_COLLECTION_NAME": OS_COLLECTION_NAME,
        "OS_VECTOR_PREFIX": OS_VECTOR_PREFIX,
        "OS_POLICY_NAME": OS_POLICY_NAME,
        "KB_ROLE_NAME": KB_ROLE_NAME,
        "KB_ROLE_ARN": kb_role_arn,
    }


#############################################
# Helper Functions
#############################################
def wait_for_operation(method, check_keys, expected_value, timeout, **kwargs):
    """
    Waits for an AWS operation to complete by checking a specific key in the response.

    :param client: The boto3 client
    :param method: The client method to call (e.g., client.list_data_sources)
    :param check_key: The key in the response to check (e.g., "dataSourceSummaries")
    :param expected_value: The value of the check_key that indicates completion (e.g., empty list)
    :param timeout: Timeout in seconds
    :param kwargs: Additional arguments to pass to the method
    """
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            log.error(f"Wait operation failed to complete after '{timeout}' seconds")
            exit(1)
        response = method(**kwargs)
        val = (
            response[check_keys[0]]
            if len(check_keys) == 1
            else response[check_keys[0]][check_keys[1]]
        )
        if val == expected_value:
            log.info("Operation completed successfully")
            break
        else:
            log.info("Operation is still in progress...")
            time.sleep(10)


def wait_for_resource_to_not_exist(
    client, method, check_keys, expected_value, timeout, **kwargs
):
    """
    Waits for an AWS resource to be deleted by checking it's not found.
    """
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            log.error(f"Delete operation failed to complete after '{timeout}' seconds")
            exit(1)
        try:
            response = method(**kwargs)
            val = (
                response[check_keys[0]]
                if len(check_keys) == 1
                else response[check_keys[0]][check_keys[1]]
            )
            if val == expected_value:
                log.info("Resource is still deleting...")
                time.sleep(10)
        except client.exceptions.ResourceNotFoundException:
            log.info("Resource successfully deleted")
            break


#############################################
# Amazon Bedrock Functions
#############################################
def get_knowledge_base_id(client, name: str) -> str:
    response = client.list_knowledge_bases(maxResults=123)
    for kb in response["knowledgeBaseSummaries"]:
        if kb["name"] == name:
            return kb["knowledgeBaseId"]
    return ""


def get_knowledge_base_data_source_ids(client, kb_id: str) -> list[dict[str, str]]:
    response = client.list_data_sources(knowledgeBaseId=kb_id, maxResults=123)
    results = list()
    for ds in response["dataSourceSummaries"]:
        results.append(
            {
                "id": ds["dataSourceId"],
                "name": ds["name"],
            }
        )
    return results


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


#############################################
# Amazon OpenSearch Functions
#############################################
def check_if_os_policy_exists(client, policy_name: str, policy_type) -> bool:
    if policy_type == "data":
        try:
            response = client.get_access_policy(name=policy_name, type=policy_type)
            if response["accessPolicyDetail"]["name"] == policy_name:
                return True
        except client.exceptions.ResourceNotFoundException:
            log.info(f"OpenSearch access policy '{policy_name}' not found")
            return False
    elif policy_type in ["encryption", "network"]:
        try:
            response = client.get_security_policy(name=policy_name, type=policy_type)
            if response["securityPolicyDetail"]["name"] == policy_name:
                return True
        except client.exceptions.ResourceNotFoundException:
            log.info(f"OpenSearch security policy '{policy_name}' not found")
            return False


def get_opensearch_collection(client, name: str):
    response = client.batch_get_collection(names=[name])
    for collection in response["collectionDetails"]:
        if collection["name"] == name:
            endpoint = collection["collectionEndpoint"].replace("https://", "")
            return {
                "host": endpoint,
                "arn": collection["arn"],
                "id": collection["id"],
            }
    log.info(f"OpenSearch collection {name} not found")
    return {}
