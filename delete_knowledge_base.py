"""
Cleans up Amazon Bedrock knowledge base resources created
by the create_knowledge_base.py script

# Important note
This script is not handling next tokens for pagination
from AWS Boto3 API calls. If you have more than 123 results
for your knowledge base and or data sources, you will need to
update this script to handle pagination.

Call with:
python delete_knowledge_base.py
"""
import boto3
import time
import utils

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


def delete_knowledge_base_data_sources(kb_id: str, data_source_ids: list[str]):
    for ds in data_source_ids:
        response = bedrock_client.delete_data_source(
            knowledgeBaseId=kb_id, dataSourceId=ds["id"]
        )
        log.info(f"Data source {ds['name']} status: {response['status']}")

    utils.wait_for_operation(
        bedrock_client.list_data_sources,
        ["dataSourceSummaries"],
        [],
        500,
        knowledgeBaseId=kb_id,
        maxResults=123,
    )


def delete_knowledge_base(kb_id: str):
    response = bedrock_client.delete_knowledge_base(knowledgeBaseId=kb_id)
    log.info(f"Knowledge base {KB_NAME} status: {response['status']}")
    utils.wait_for_resource_to_not_exist(
        bedrock_client,
        bedrock_client.get_knowledge_base,
        ["knowledgeBase","status"],
        "DELETING",
        500,
        knowledgeBaseId=kb_id,
    )


def delete_opensearch_collection(name: str, os_collection_id: str):
    response = os_client.delete_collection(
        id=os_collection_id,
    )
    log.info(f"OpenSearch collection {name} deleted: {response}")
    utils.wait_for_operation(
        os_client.list_collections,
        ["collectionSummaries"],
        [],
        500,
        collectionFilters={"name": name},
        maxResults=100,
    )


def delete_opensearch_access_policy(name: str) -> None:
    policy_type = "data"
    if utils.check_if_os_policy_exists(os_client, name, policy_type):
        log.info("OpenSearch access policy already exists... Deleting")
        response = os_client.delete_access_policy(
            name=name,
            type=policy_type,
        )
        log.info(f"OpenSearch access policy deleted: {response}")
    else:
        log.info("OpenSearch access policy not found... Already deleted")


def delete_opensearch_encryption_security_policy(name: str) -> None:
    policy_type = "encryption"
    if utils.check_if_os_policy_exists(os_client, name, policy_type):
        log.info("OpenSearch encryption policy already exists... Deleting")
        response = os_client.delete_security_policy(
            name=name,
            type=policy_type,
        )
        log.info(f"OpenSearch encryption policy deleted: {response}")
    else:
        log.info("OpenSearch encryption policy not found... Already deleted")


def delete_opensearch_network_security_policy(name: str) -> None:
    policy_type = "network"
    if utils.check_if_os_policy_exists(os_client, name, policy_type):
        log.info("OpenSearch network policy already exists... Deleting")
        response = os_client.delete_security_policy(
            name=name,
            type=policy_type,
        )
        log.info(f"OpenSearch network policy deleted: {response}")
    else:
        log.info("OpenSearch network policy not found... Already deleted")


def main():
    log.info("Cleaning up Amazon Bedrock knowledge base resources...")

    kb_id = utils.get_knowledge_base_id(bedrock_client, KB_NAME)
    if kb_id:
        kb_data_source_ids = utils.get_knowledge_base_data_source_ids(
            bedrock_client, kb_id
        )
        if kb_data_source_ids:
            log.info("Deleting knowledge base data sources...")
            log.info(f"Data source IDs: {kb_data_source_ids}")
            delete_knowledge_base_data_sources(kb_id, kb_data_source_ids)
        else:
            log.info("No knowledge base data sources found... Already deleted")
        log.info("Deleting knowledge base...")
        delete_knowledge_base(kb_id)
    else:
        log.info(f"Knowledge base {KB_NAME} not found... Already deleted")

    log.info("Deleting OpenSearch resources...")
    os_collection = utils.get_opensearch_collection(os_client, OS_COLLECTION_NAME)
    if "id" in os_collection:
        delete_opensearch_collection(OS_COLLECTION_NAME, os_collection["id"])
    else:
        log.info(
            f"OpenSearch collection {OS_COLLECTION_NAME} not found... Already deleted"
        )

    # Delete OpenSearch policies if they exist otherwise skip
    delete_opensearch_access_policy(OS_POLICY_NAME)
    delete_opensearch_encryption_security_policy(OS_POLICY_NAME)
    delete_opensearch_network_security_policy(OS_POLICY_NAME)

    log.success("Clean up complete...")


if __name__ == "__main__":
    main()
