# Define variables
AWS_ACCOUNT_ID := 625910292984
AWS_REGION := eu-north-1
ECR_REPOSITORY_NAME := aws-lambda-yfinance-gateway-repository
IMAGE_NAME := $(ECR_REPOSITORY_NAME)
IMAGE_TAG := latest
ECR_FULL_URI := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPOSITORY_NAME):$(IMAGE_TAG)

.PHONY: all build tag push clean

all: build push

build: # Build the Docker image
	@echo "--- Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG) ---"
	podman build -t $(IMAGE_NAME):$(IMAGE_TAG) .

tag: build # Tag the Docker image for ECR
	@echo "--- Tagging Docker image: $(ECR_FULL_URI) ---"
	podman tag $(IMAGE_NAME):$(IMAGE_TAG) $(ECR_FULL_URI)

push: tag # Authenticate Docker and push the image to ECR
	@echo "--- Authenticating Docker to ECR in $(AWS_REGION) ---"
	aws ecr get-login-password --region $(AWS_REGION) | podman login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	@echo "--- Pushing Docker image to ECR: $(ECR_FULL_URI) ---"
	podman push $(ECR_FULL_URI)


clean: # Clean up local Docker images
	@echo "--- Cleaning up local Docker images ---"
	-podman rmi $(IMAGE_NAME):$(IMAGE_TAG) $(ECR_FULL_URI) 2>/dev/null || true