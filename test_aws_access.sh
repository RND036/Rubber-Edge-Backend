#!/bin/bash

echo "Testing AWS Permissions..."
echo "=========================="
echo ""

echo "1. Testing S3 access..."
if aws s3 ls > /dev/null 2>&1; then
    echo "✓ S3 access: OK"
else
    echo "✗ S3 access: FAILED"
fi

echo ""
echo "2. Testing EC2 access..."
if aws ec2 describe-instances --region ap-southeast-2 > /dev/null 2>&1; then
    echo "✓ EC2 access: OK"
else
    echo "✗ EC2 access: FAILED"
fi

echo ""
echo "3. Testing RDS access..."
if aws rds describe-db-instances --region ap-southeast-2 > /dev/null 2>&1; then
    echo "✓ RDS access: OK"
else
    echo "✗ RDS access: FAILED"
fi

echo ""
echo "=========================="
echo "If all show OK, you're ready to deploy!"
