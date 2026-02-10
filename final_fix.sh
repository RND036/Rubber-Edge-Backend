#!/bin/bash
# Simple fix - Run this to complete deployment

echo "Connecting to EC2 and fixing imports..."

ssh -tt -i ~/Downloads/rubberedge-key.pem ubuntu@13.239.135.231 << 'EOF'
cd rubberedge/backend/api/rubber_chatbot
echo "Fixing imports..."
sed -i 's/langchain\.tools/langchain_core.tools/g' agents.py 
sed -i 's/langchain\.prompts/langchain_core.prompts/g' agents.py
echo "✅ Imports fixed!"

echo ""
echo "Restarting services..."
sudo systemctl restart gunicorn daphne celery celerybeat
sleep 5

echo ""
echo "Testing..."
curl -s http://localhost/health/

echo ""
echo ""
echo "Check from your browser: http://13.239.135.231/health/"
exit
EOF
