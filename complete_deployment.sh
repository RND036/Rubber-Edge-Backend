#!/bin/bash
# Complete Deployment Script - Fixes all remaining issues

set -e

KEY_FILE="$HOME/Downloads/rubberedge-key.pem"
SERVER="ubuntu@13.239.135.231"

echo "🚀 Completing AWS Deployment"
echo "================================"
echo ""

# Step 1: Copy the fixed agents.py file
echo "Step 1: Uploading fixed agents.py file..."
scp -i "$KEY_FILE" -o ConnectTimeout=15 \
    "./api/rubber_chatbot/agents.py" \
    "$SERVER:~/rubberedge/backend/api/rubber_chatbot/agents.py" || {
    echo "⚠️  SCP failed, trying alternative SSH method..."
    
    # Alternative: Use SSH with cat to write file
    ssh -i "$KEY_FILE" -o ConnectTimeout=15 "$SERVER" \
        "cat > ~/rubberedge/backend/api/rubber_chatbot/agents.py" < "./api/rubber_chatbot/agents.py"
}

echo "✅ File uploaded"
echo ""

# Step 2: Restart services
echo "Step 2: Restarting all services..."
ssh -i "$KEY_FILE" -o ConnectTimeout=15 "$SERVER" << 'ENDCOMMANDS'
cd ~/rubberedge/backend
echo "Restarting services..."
sudo systemctl restart gunicorn
sleep 2
sudo systemctl restart daphne
sudo systemctl restart celery
sudo systemctl restart celerybeat
ENDCOMMANDS

echo "✅ Services restarted"
echo ""

# Step 3: Verify deployment
echo "Step 3: Verifying deployment..."
sleep 3

ssh -i "$KEY_FILE" -o ConnectTimeout=15 "$SERVER" << 'ENDVERIFY'
echo "=== Service Status ==="
systemctl is-active gunicorn daphne celery celerybeat

echo ""
echo "=== Testing Health Endpoint ==="
curl -s http://localhost/health/ | head -20

echo ""
echo "=== Checking Gunicorn Errors (last 10 lines) ==="
sudo tail -10 /var/log/gunicorn/error.log 2>/dev/null || echo "No errors logged"
ENDVERIFY

echo ""
echo "================================"
echo "✅ Deployment Complete!"
echo ""
echo "Test your API:"
echo "  http://13.239.135.231/health/"
echo "  http://13.239.135.231/api/"
echo ""
