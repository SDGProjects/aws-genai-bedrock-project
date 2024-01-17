"""
Creates an Amazon Bedrock knowledge base using the Amazon Bedrock Runtime API.

AWS Resources Created:
- Amazon Bedrock knowledge base
- Amazon Bedrock data source
- Amazon OpenSearch Service collection
- Amazon OpenSearch Service collection index
- Amazon OpenSearch Service policies

# Important note
This script is not handling next tokens for pagination
from AWS Boto3 API calls. If you have more than 123 results
for your knowledge base and or data sources, you will need to
update this script to handle pagination.

Call with:
python create_knowledge_base.py
"""
import boto3
import json
import time
import utils

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from loguru import logger as log


# Enable Boto3 debug logging
DEBUG = False  # True
if DEBUG:
    boto3.set_stream_logger(name="botocore")

bedrock_client = boto3.client("bedrock-agent")
os_client = boto3.client("opensearchserverless")

# Constants
shared_consts = utils.get_shared_consts()
KB_NAME = shared_consts["KB_NAME"]
KB_DESCRIPTION = shared_consts["KB_DESCRIPTION"]
KB_BUCKET_NAME = shared_consts["KB_BUCKET_NAME"]
KB_BUCKET_ARN = shared_consts["KB_BUCKET_ARN"]
BEDROCK_FM = shared_consts["BEDROCK_FM"]
BEDROCK_EMBED_MODEL_ARN = shared_consts["BEDROCK_EMBED_MODEL_ARN"]
OS_COLLECTION_NAME = shared_consts["OS_COLLECTION_NAME"]
OS_VECTOR_PREFIX = shared_consts["OS_VECTOR_PREFIX"]
OS_POLICY_NAME = shared_consts["OS_POLICY_NAME"]
KB_ROLE_NAME = shared_consts["KB_ROLE_NAME"]
KB_ROLE_ARN = shared_consts["KB_ROLE_ARN"]

# Init AWS4Auth for OpenSearch
client = boto3.client("opensearchserverless")
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    "us-east-1",
    "aoss",
    session_token=credentials.token,
)


def create_opensearch_access_policy(name: str) -> None:
    if utils.check_if_os_policy_exists(os_client, name, "data"):
        log.info("OpenSearch access policy already exists... Skipping")
        return None
    policy = {
        "Rules": [
            {
                "Resource": ["collection/*"],
                "Permission": [
                    "aoss:DescribeCollectionItems",
                    "aoss:CreateCollectionItems",
                    "aoss:UpdateCollectionItems",
                ],
                "ResourceType": "collection",
            },
            {
                "Resource": ["index/*/*"],
                "Permission": [
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument",
                    "aoss:CreateIndex",
                ],
                "ResourceType": "index",
            },
        ],
        "Principal": [
            f"{KB_ROLE_ARN}",
            "arn:aws:sts::576720715620:assumed-role/AWSReservedSSO_AdministratorAccess_b2d69c4e698ab806/cooper.miller",
            "arn:aws:iam::576720715620:user/cm-cli-admin",
        ],
        "Description": "",
    }
    response = os_client.create_access_policy(
        description="Default access policy for Amazon OpenSearch Service",
        name="bedrock-security-policy",
        policy=f"[{json.dumps(policy)}]",
        type="data",
    )
    access_policy_name = response["accessPolicyDetail"]["name"]
    log.info(f"Created OpenSearch access policy: {access_policy_name}")


def create_opensearch_encryption_security_policy(name: str) -> None:
    if utils.check_if_os_policy_exists(os_client, name, "encryption"):
        log.info("OpenSearch encryption policy already exists... Skipping")
        return None
    response = os_client.create_security_policy(
        description="Default security policy for Amazon OpenSearch Service",
        name="bedrock-security-policy",
        policy='{"Rules": [{"Resource": ["collection/*"], "ResourceType": "collection"}], "AWSOwnedKey": true}',
        type="encryption",
    )
    policy_name = response["securityPolicyDetail"]["name"]
    log.info(f"Created OpenSearch encryption security policy: {policy_name}")


def create_opensearch_network_security_policy(name: str) -> None:
    if utils.check_if_os_policy_exists(os_client, name, "network"):
        log.info("OpenSearch network policy already exists... Skipping")
        return None
    response = os_client.create_security_policy(
        description="Default security policy for Amazon OpenSearch Service",
        name="bedrock-security-policy",
        policy='[{"Rules": [{"Resource": ["collection/*"], "ResourceType": "dashboard"}, {"Resource": ["collection/*"], "ResourceType": "collection"}], "AllowFromPublic": true}]',
        type="network",
    )
    policy_name = response["securityPolicyDetail"]["name"]
    log.info(f"Created OpenSearch network security policy: {policy_name}")


def create_opensearch_collection() -> str:
    os_client.create_collection(
        description=KB_DESCRIPTION,
        name=OS_COLLECTION_NAME,
        standbyReplicas="DISABLED",
        type="VECTORSEARCH",
    )
    collection_status = wait_for_collection_creation()
    if collection_status != "ACTIVE":
        log.error("Failed to successfully create collection...")
        exit(1)


def wait_for_collection_creation() -> bool:
    """Waits for the collection to become active"""
    response = os_client.batch_get_collection(names=[OS_COLLECTION_NAME])
    while (response["collectionDetails"][0]["status"]) == "CREATING":
        log.info("Creating collection...")
        time.sleep(30)
        response = os_client.batch_get_collection(names=[OS_COLLECTION_NAME])
    return response["collectionDetails"][0]["status"]


def index_opensearch_collection_data(host: str):
    """Create an index and add some sample data"""
    os_collection_client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300,
    )
    # It can take up to a minute for data access rules to be enforced
    log.info("Waiting for data access rules to be enforced (up to a minute)...")
    time.sleep(45)

    # Create index
    response = os_collection_client.indices.create(
        f"{OS_VECTOR_PREFIX}-index",
        body={
            "settings": {
                "index": {
                    "knn.algo_param": {"ef_search": "512"},
                    "knn": "true",
                }
            },
            "mappings": {
                "properties": {
                    "AMAZON_BEDROCK_METADATA": {"type": "text", "index": False},
                    "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "engine": "nmslib",
                            "space_type": "cosinesimil",
                            "name": "hnsw",
                            "parameters": {},
                        },
                    },
                }
            },
        },
    )
    log.info(f"Index response: {response}")


def create_knowledge_base(collection_arn: str) -> str:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent/client/create_knowledge_base.html
    storage_prefix = "bedrock-knowledge-base-default"
    response = bedrock_client.create_knowledge_base(
        name=KB_NAME,
        description=KB_DESCRIPTION,
        roleArn=KB_ROLE_ARN,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": BEDROCK_EMBED_MODEL_ARN
            },
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": collection_arn,
                "vectorIndexName": f"{storage_prefix}-index",
                "fieldMapping": {
                    "vectorField": f"{storage_prefix}-vector",
                    "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                    "metadataField": "AMAZON_BEDROCK_METADATA",
                },
            },
        },
    )
    if "failureReasons" in response:
        log.error(f"Error creating knowledge base: {response['failureReasons']}")
    return response["knowledgeBase"]["knowledgeBaseId"]


def create_data_source(kb_id: str) -> str:
    response = bedrock_client.create_data_source(
        knowledgeBaseId=kb_id,
        name=f"{KB_NAME}-data-source",
        description=f"{KB_NAME} data source",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": KB_BUCKET_ARN,
            },
        },
    )
    return response["dataSource"]["dataSourceId"]


def ingest_data_source_into_knowledge_base(kb_id: str, data_source_id: str) -> None:
    response = bedrock_client.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=data_source_id,
        description="Syncing S3 data source",
    )
    data = response["ingestionJob"]
    log.info(f"Ingestion Job Started...")
    log.info(f"Ingestion Job Status: {data['status']} ID: {data['ingestionJobId']}")

    utils.wait_for_operation(
        bedrock_client.get_ingestion_job,
        ["ingestionJob", "status"],
        "COMPLETE",
        500,
        knowledgeBaseId=kb_id,
        dataSourceId=data_source_id,
        ingestionJobId=data["ingestionJobId"],
    )


def main():
    log.info("Creating OpenSearch Security Policies...")
    create_opensearch_access_policy(OS_POLICY_NAME)
    create_opensearch_encryption_security_policy(OS_POLICY_NAME)
    create_opensearch_network_security_policy(OS_POLICY_NAME)
    log.success("Created OpenSearch Security Policies!")

    log.info("Creating OpenSearchServerless Collection...")
    collection_data = utils.get_opensearch_collection(os_client, OS_COLLECTION_NAME)
    if not collection_data:
        log.info("Collection not found... Creating it now")
        create_opensearch_collection()
        collection_data = utils.get_opensearch_collection(os_client, OS_COLLECTION_NAME)
    index_opensearch_collection_data(collection_data["host"])
    log.info("Waiting for index to be created...")
    time.sleep(30)

    log.info(f"Collection Host: {collection_data['host']}")
    log.info(f"Collection ARN: {collection_data['arn']}")

    kb_id = utils.get_knowledge_base_id(bedrock_client, KB_NAME)
    if not kb_id:
        log.info("Knowledge base not found... Creating it now")
        kb_id = create_knowledge_base(collection_data["arn"])
    log.info(f"Knowledge Base ID: {kb_id}")

    kb_ds_ids = utils.get_knowledge_base_data_source_ids(bedrock_client, kb_id)
    # Default to first ds since we only create one
    data_source_id = ""
    if kb_ds_ids:
        log.info("Data source found... Using it")
        data_source_id = kb_ds_ids[0]["id"]
    else:
        log.info("Data source not found... Creating it now")
        data_source_id = create_data_source(kb_id)
    log.info(f"Data Source ID: {data_source_id}")

    ingest_data_source_into_knowledge_base(kb_id, data_source_id)

    log.success("Successfully created all resources!!!")


if __name__ == "__main__":
    main()
