#!/bin/bash
set -e

# Default bucket name and region
BUCKET_NAME="${S3_SESSION__BUCKET:-user-sessions}"
REGION="${S3_SESSION__REGION_NAME:-us-east-1}"

echo "Creating bucket: $BUCKET_NAME in region: $REGION"

if [ "$REGION" = "us-east-1" ]; then
  awslocal s3api create-bucket \
    --bucket "$BUCKET_NAME"
else
  awslocal s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --create-bucket-configuration LocationConstraint="$REGION"
fi
