# Deploy code from /dist to AWS S3 bucket and invalidate CloudFront cache
# Usage: ./deploy.sh <bucket-name> <cloudfront-distribution-id>

#!/bin/bash
set -e
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <bucket-name> <cloudfront-distribution-id>"
    exit 1
fi

BUCKET_NAME=$1 # sfk-scheduler-web-992382661713-eu-north-1
DISTRIBUTION_ID=$2 # EBDGRJ1SFCCH0

# Sync the /dist directory to the S3 bucket
aws s3 sync ./dist s3://$BUCKET_NAME --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "Deployment complete. S3 bucket: $BUCKET_NAME, CloudFront distribution: $DISTRIBUTION_ID"


