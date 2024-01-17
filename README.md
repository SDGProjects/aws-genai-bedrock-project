# Amazon Bedrock RAG Python Flask Chatbot

Use the Amazon Bedrock FMs to generate responses to user input based on Retrieval Augmented Generation (RAG) data.

![Amazon Bedrock Flask Chatbot](images/amazon-bedrock-flask-chatbot.png)

## Pre-requisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installing/)
- [AWS Account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)
- [Amazon Bedrock foundation model access](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html)

## Notes

- Terraform and CloudFormation Amazon Bedrock resources are not available as of 1/16/24. I've created Python scripts that leverage Boto3 to create and delete the missing AWS resources
  - create_knowledge_base.py
  - delete_knowledge_base.py

## Getting Started

1. Clone or fork this repo and `cd` into the project directory
   ```bash
   git clone https://github.com/cxmiller21/aws-bedrock-flask-chatbot.git
   ```
2. Copy your PDF, Text, CSV, or JSON files to the `rag_data` directory (These files will be uploaded to Amazon S3 with Terraform in the next step)
2. Create Terraform AWS IAM and S3 resources
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```
3. Create Amazon Bedrock and AWS OpenSearch resources
   ```bash
   # Change back to the project root directory
   cd ../
   python create_knowledge_base.py
   # Validate the knowledge base was created successfully
   # either through the script logs and or the AWS Console
   ```
4. Install flaks app dependencies
   ```bash
    cd flask_chatbot
    # Create a virtual environment
    python -m venv venv
    # Activate the virtual environment
    source venv/bin/activate
    python -m pip install -r requirements.txt
    ```
5. Run the app
   ```bash
   python app.py
   ```
6. Open a browser and navigate to `http://localhost:5100`
7. Ask the chatbot a question based on the RAG data you uploaded and validate the response is relevant

## Acknowledgements

Flask App foundation from [skolo-online's chat-gpt-starter repository](https://github.com/skolo-online/chat-gpt-starter)
