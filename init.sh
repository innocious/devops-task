#!/bin/bash

# Set variables
BUCKET_NAME="cious-pulumi-backend-state-v1"
REGION="us-west-2"
ENVIRONMENT="Dev"

# Function to check if a command fails
handle_error() {
    if [ $? -ne 0 ]; then
        echo "Error occurred. Exiting script."
        exit 1
    fi
}

# Step 1: Test AWS connectivity
echo "Testing AWS connectivity..."
aws sts get-caller-identity --output text
if [ $? -ne 0 ]; then
    echo "Error: Unable to verify AWS connectivity."
    echo "Possible reasons:"
    echo "1. AWS CLI credentials are not configured."
    echo "2. Your AWS profile is not set correctly."
    echo "3. There is a network connectivity issue."
    echo ""
    echo "To fix this issue:"
    echo "- Run 'aws configure' to set up your credentials."
    echo "- Or set the AWS_PROFILE environment variable to a valid profile, e.g.,"
    echo "  export AWS_PROFILE=your-profile-name"
    echo "- Ensure your IAM user or role has sufficient permissions to run AWS CLI commands."
    exit 1
fi
echo "AWS connectivity verified successfully."

# Step 2: Create the S3 bucket
echo "Creating S3 bucket: $BUCKET_NAME in region: $REGION"
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $REGION \
    --create-bucket-configuration LocationConstraint=$REGION
handle_error
echo "S3 bucket created successfully."

# Step 3: Enable versioning
echo "Enabling versioning on the bucket..."
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled
handle_error
echo "Versioning enabled."

# Step 4: Enable default encryption (AES256)
echo "Enabling default encryption (AES256)..."
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{
      "Rules": [
        {
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }
      ]
    }'
handle_error
echo "Default encryption enabled."

# Step 5: Block public access
echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration '{
      "BlockPublicAcls": true,
      "IgnorePublicAcls": true,
      "BlockPublicPolicy": true,
      "RestrictPublicBuckets": true
    }'
handle_error
echo "Public access blocked."

# Step 6: Add bucket tags
echo "Adding tags to the bucket..."
aws s3api put-bucket-tagging \
    --bucket $BUCKET_NAME \
    --tagging '{
      "TagSet": [
        {"Key": "Environment", "Value": "'$ENVIRONMENT'"},
        {"Key": "Project", "Value": "Pulumi-Backend"}
      ]
    }'
handle_error
echo "Tags added successfully."

# Step 7: Confirm the bucket configuration
echo "Verifying bucket settings..."
aws s3api get-bucket-versioning --bucket $BUCKET_NAME
aws s3api get-bucket-encryption --bucket $BUCKET_NAME
aws s3api get-public-access-block --bucket $BUCKET_NAME

echo "S3 bucket $BUCKET_NAME created and configured successfully!"
