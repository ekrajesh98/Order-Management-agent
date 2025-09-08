#!/bin/bash
set -e

# INFO: S3 Configuration
awslocal s3api create-bucket \
  --bucket event-bucket
