#!/bin/bash

# Variables
BUCKET_NAME="elk-monitoring-setup"
FILE_PATH="setup.sh"
REGION="us-west-2"

# Function to check if a command fails
handle_error() {
    if [ $? -ne 0 ]; then
        echo "Error occurred. Exiting script."
        exit 1
    fi
}

# Step 1: Verify AWS CLI Authentication
echo "Checking AWS CLI authentication..."
aws sts get-caller-identity --output text
if [ $? -ne 0 ]; then
    echo "AWS CLI is not authenticated. Please configure your AWS CLI."
    echo "Run 'aws configure' to set up credentials."
    exit 1
fi
echo "AWS CLI authenticated successfully."

# Step 2: Check if the S3 bucket exists
echo "Checking if bucket $BUCKET_NAME exists..."
aws s3api head-bucket --bucket $BUCKET_NAME 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Bucket $BUCKET_NAME does not exist. Creating the bucket..."
    aws s3api create-bucket \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --create-bucket-configuration LocationConstraint=$REGION
    handle_error
    echo "Bucket $BUCKET_NAME created successfully."
else
    echo "Bucket $BUCKET_NAME exists."
fi

# Step 3: Upload the file
echo "Uploading $FILE_PATH to bucket $BUCKET_NAME..."
aws s3 cp $FILE_PATH s3://$BUCKET_NAME/
handle_error
echo "File $FILE_PATH uploaded successfully to s3://$BUCKET_NAME/."

# Verify upload
echo "Verifying upload..."
aws s3 ls s3://$BUCKET_NAME/ | grep $(basename $FILE_PATH)
handle_error
echo "Upload verified successfully."
