#!/bin/bash
# EC2 Connection Troubleshooting

echo "🔍 EC2 Connection Diagnostics"
echo "=============================="
echo ""

# Test 1: Basic network connectivity
echo "Test 1: Checking if EC2 IP is reachable..."
if ping -c 3 13.239.135.231 >/dev/null 2>&1; then
    echo "✅ EC2 IP responds to ping"
else
    echo "❌ EC2 IP does not respond to ping (ICMP may be blocked)"
fi
echo ""

# Test 2: Check if SSH port is open
echo "Test 2: Checking if SSH port (22) is accessible..."
if nc -z -w 5 13.239.135.231 22 2>/dev/null; then
    echo "✅ Port 22 is open"
else
    echo "❌ Port 22 is not accessible"
    echo "   Possible reasons:"
    echo "   - EC2 instance is stopped"
    echo "   - Security group doesn't allow SSH from your IP"
    echo "   - Network firewall blocking connection"
fi
echo ""

# Test 3: Check HTTP port
echo "Test 3: Checking if HTTP port (80) is accessible..."
if nc -z -w 5 13.239.135.231 80 2>/dev/null; then
    echo "✅ Port 80 is open"
    echo "   Trying to fetch health endpoint..."
    HTTP_RESPONSE=$(curl -s -m 10 -w "\nHTTP_CODE:%{http_code}" http://13.239.135.231/health/ 2>&1 | tail -1)
    echo "   Response: $HTTP_RESPONSE"
else
    echo "❌ Port 80 is not accessible"
fi
echo ""

# Test 4: Check AWS CLI config
echo "Test 4: Checking AWS CLI configuration..."
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is installed"
    
    # Check if we can query EC2
    echo "   Checking EC2 instance status..."
    INSTANCE_STATE=$(aws ec2 describe-instances \
        --instance-ids i-0f916b881089a752f \
        --region ap-southeast-2 \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>&1)
    
    if [[ $INSTANCE_STATE == "running" ]]; then
        echo "   ✅ EC2 instance is RUNNING"
        
        # Get public IP
        PUBLIC_IP=$(aws ec2 describe-instances \
            --instance-ids i-0f916b881089a752f \
            --region ap-southeast-2 \
            --query 'Reservations[0].Instances[0].PublicIpAddress' \
            --output text 2>&1)
        echo "   Current IP: $PUBLIC_IP"
        
        if [[ $PUBLIC_IP != "13.239.135.231" ]]; then
            echo "   ⚠️  WARNING: IP address has changed!"
            echo "   Old IP: 13.239.135.231"
            echo "   New IP: $PUBLIC_IP"
            echo ""
            echo "   Update your scripts with the new IP"
        fi
    elif [[ $INSTANCE_STATE == "stopped" ]]; then
        echo "   ❌ EC2 instance is STOPPED"
        echo ""
        echo "   To start it:"
        echo "   aws ec2 start-instances --instance-ids i-0f916b881089a752f --region ap-southeast-2"
    else
        echo "   Status: $INSTANCE_STATE"
    fi
else
    echo "⚠️  AWS CLI not found"
    echo "   Can't check instance status automatically"
    echo "   Please check EC2 console: https://ap-southeast-2.console.aws.amazon.com/ec2/"
fi
echo ""

# Test 5: Check SSH key
echo "Test 5: Checking SSH key file..."
if [[ -f ~/Downloads/rubberedge-key.pem ]]; then
    echo "✅ SSH key exists"
    PERMS=$(stat -f %A ~/Downloads/rubberedge-key.pem 2>/dev/null || stat -c %a ~/Downloads/rubberedge-key.pem 2>/dev/null)
    if [[ $PERMS == "400" || $PERMS == "600" ]]; then
        echo "   ✅ Permissions are correct ($PERMS)"
    else
        echo "   ⚠️  Permissions may be too open ($PERMS)"
        echo "   Run: chmod 400 ~/Downloads/rubberedge-key.pem"
    fi
else
    echo "❌ SSH key not found at ~/Downloads/rubberedge-key.pem"
fi
echo ""

echo "=============================="
echo "Summary"
echo "=============================="
echo ""
echo "If EC2 is running but SSH times out:"
echo "  1. Check Security Group in AWS Console"
echo "  2. Verify your current IP: curl ifconfig.me"
echo "  3. Add your IP to Security Group SSH rule"
echo ""
echo "Alternative connection methods:"
echo "  1. AWS Systems Manager Session Manager (no SSH required)"
echo "  2. EC2 Instance Connect from AWS Console"
echo "  3. Connect from a different network"
echo ""
echo "AWS Console Quick Links:"
echo "  EC2 Instance: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#InstanceDetails:instanceId=i-0f916b881089a752f"
echo "  Security Groups: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#SecurityGroups:"
echo ""
