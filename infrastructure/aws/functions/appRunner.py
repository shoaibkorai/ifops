import boto3

# Configuration
SERVICE_NAME = "my-apprunner-service"
ECR_REPOSITORY = "my-app"
ECR_IMAGE_TAG = "latest"
ECR_ACCOUNT_ID = "123456789012"
ECR_REGION = "us-east-1"
ROLE_ARN = "arn:aws:iam::123456789012:role/AppRunnerECRAccessRole"

# Initialize App Runner client
client = boto3.client("apprunner", region_name=ECR_REGION)

def create_apprunner_service():
    try:
        response = client.create_service(
            serviceName=SERVICE_NAME,
            sourceConfiguration={
                "imageRepository": {
                    "imageIdentifier": f"{ECR_ACCOUNT_ID}.dkr.ecr.{ECR_REGION}.amazonaws.com/{ECR_REPOSITORY}:{ECR_IMAGE_TAG}",
                    "imageRepositoryType": "ECR",
                    "imageConfiguration": {
                        "port": "8080"
                    }
                },
                "authenticationConfiguration": {
                    "accessRoleArn": ROLE_ARN
                },
                "autoDeploymentsEnabled": True
            },
            instanceConfiguration={
                "cpu": "1024",
                "memory": "2048"
            }
        )

        print("✅ App Runner service is being created.")
        print(f"Service ARN: {response['service']['serviceArn']}")
        print(f"Status: {response['service']['status']}")

    except Exception as e:
        print("❌ Failed to create App Runner service")
        print(e)

if __name__ == "__main__":
    create_apprunner_service()
