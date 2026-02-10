# AWS Free Tier - Quick Reference

## Free Tier Resources (12 months)

### EC2
- **Instance**: t2.micro (1 vCPU, 1 GB RAM)
- **Hours**: 750 hours/month
- **Usage**: Can run 1 instance 24/7 or multiple instances that total 750 hours
- **Storage**: 30 GB EBS (General Purpose SSD)

### RDS
- **Instance**: db.t2.micro or db.t3.micro
- **Hours**: 750 hours/month
- **Storage**: 20 GB
- **Backups**: 20 GB

### S3
- **Storage**: 5 GB
- **GET Requests**: 20,000 per month
- **PUT Requests**: 2,000 per month

### Data Transfer
- **Outbound**: 15 GB/month
- **Inbound**: Free

### CloudWatch
- **Alarms**: 10 alarms
- **Metrics**: Basic monitoring

## Cost Optimization Tips

### 1. Monitor Your Usage
```bash
# Set up billing alerts in AWS Console
# Console → Billing → Billing Preferences → Enable alerts
# Create CloudWatch alarm for billing
```

### 2. Stop Resources When Not Needed
```bash
# Stop EC2 instance (doesn't delete, just stops)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Start EC2 instance
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Stop RDS instance (for testing environments)
aws rds stop-db-instance --db-instance-identifier rubberedge-db
```

### 3. Clean Up Regularly
- Delete old RDS snapshots
- Remove unused S3 objects
- Clean up old AMIs
- Delete unused Elastic IPs

### 4. Use S3 Lifecycle Policies
```json
{
  "Rules": [{
    "Status": "Enabled",
    "Transitions": [{
      "Days": 90,
      "StorageClass": "GLACIER"
    }]
  }]
}
```

## Monthly Cost Estimates (After Free Tier)

### Typical Usage Costs
- **EC2 t2.micro**: ~$8.50/month
- **RDS db.t2.micro**: ~$15/month
- **S3 Storage (10 GB)**: ~$0.23/month
- **Data Transfer (20 GB)**: ~$1.80/month

**Total**: ~$25-30/month

### Ways to Reduce Costs
1. Use t3.micro instead of t2.micro (newer, cheaper)
2. Use Reserved Instances (1-year commitment = 40% discount)
3. Use Spot Instances for non-critical workloads (up to 90% discount)
4. Optimize RDS by using smaller instance types
5. Enable S3 Intelligent-Tiering

## Monitoring Commands

### Check EC2 Usage
```bash
# Get instance uptime
uptime

# Check instance type
curl -s http://169.254.169.254/latest/meta-data/instance-type
```

### Check RDS Usage
```bash
# Connect to RDS and check database size
psql -h your-rds-endpoint.rds.amazonaws.com -U postgres -d rubber_db
SELECT pg_size_pretty(pg_database_size('rubber_db'));
```

### Check S3 Usage
```bash
# Install AWS CLI
sudo apt install awscli

# Configure AWS CLI
aws configure

# Check S3 bucket size
aws s3 ls s3://rubberedge-media --recursive --summarize --human-readable
```

## Billing Alerts Setup

1. **Go to AWS Console** → Billing → Billing Preferences
2. **Enable**:
   - Receive PDF Invoice By Email
   - Receive Free Tier Usage Alerts
   - Receive Billing Alerts

3. **Create CloudWatch Alarm**:
   - Go to CloudWatch → Alarms → Create Alarm
   - Select Metric → Billing → Total Estimated Charge
   - Set threshold (e.g., $1, $5, $10)
   - Add email notification

## Free Tier Expiration

Your free tier expires **12 months** after AWS account creation.

### What Happens After Free Tier?
- You'll be charged standard rates
- Services continue running normally
- No automatic shutdown

### Preparation
1. Set up billing alerts **before** expiration
2. Review your usage patterns
3. Consider cheaper alternatives
4. Optimize resource usage

## Alternative Free Hosting (Always Free)

### Oracle Cloud Free Tier (Always Free!)
- 2 VM instances (1 GB RAM each)
- 2 Block Volumes (100 GB)
- Object Storage (10 GB)
- **No expiration!**

### Fly.io
- 3 VMs (256 MB RAM)
- 3 GB storage
- Good for hobby projects

### Railway.app
- $5 free credit/month
- Good for student projects

## Cost Comparison

| Service | AWS (after free tier) | Railway | Render | Oracle Cloud |
|---------|----------------------|---------|---------|--------------|
| Compute | $8.50/mo | $5 credit | Free (sleeps) | Free forever |
| Database | $15/mo | Included | Free (sleeps) | Free forever |
| Storage | ~$1/mo | Included | Limited | 10 GB free |
| Total | ~$25/mo | $5 credit | Free (slow) | Free forever |

## Emergency Cost Control

If your bill is unexpectedly high:

1. **Stop all resources immediately**:
   ```bash
   # Stop EC2
   aws ec2 stop-instances --instance-ids YOUR-INSTANCE-ID
   
   # Stop RDS
   aws rds stop-db-instance --db-instance-identifier rubberedge-db
   ```

2. **Check AWS Cost Explorer**:
   - Identify which service is causing high costs

3. **Delete unnecessary resources**:
   - Snapshots
   - Unused EBS volumes
   - Elastic IPs not attached to instances
   - S3 objects

4. **Contact AWS Support**:
   - Explain situation (student project)
   - Request one-time waiver if eligible

## Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/)
- [AWS Student Programs](https://aws.amazon.com/education/awseducate/)

## GitHub Student Developer Pack

If you're a student, get:
- AWS credits
- Free domain (.me domain)
- Free SSL certificates
- And many more benefits

Apply at: https://education.github.com/pack
