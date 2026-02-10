#!/bin/bash
# Fix langchain imports and restart services

set -e

EC2_IP="13.239.135.231"
SSH_KEY="$HOME/Downloads/rubberedge-key.pem"

echo "🔧 Fixing langchain imports on EC2..."

ssh -i $SSH_KEY ubuntu@$EC2_IP bash << 'REMOTE'
cd ~/rubberedge/backend/api/rubber_chatbot
sed -i 's/from langchain\.tools import tool/from langchain_core.tools import tool/' agents.py
sed -i 's/from langchain\.prompts import/from langchain_core.prompts import/' agents.py
echo "✅ Imports fixed"

echo ""
echo "🔄 Restarting services..."
sudo systemctl restart gunicorn daphne celery celerybeat
sleep 5

echo ""
echo "📊 Checking services..."
systemctl is-active gunicorn daphne celery celerybeat nginx

echo ""
echo "🧪 Testing API..."
curl -s http://localhost/health/ | head -5

echo ""
echo "✅ All services restarted!"
REMOTE

echo ""
echo "=================================================="
echo "✅ Deployment Fixed!"
echo "=================================================="
echo ""
echo "🌐 Your application is now live at:"
echo "   API: http://$EC2_IP/api/"
echo "   Admin: http://$EC2_IP/admin/"
echo "   Health: http://$EC2_IP/health/"
echo ""
echo "📝 Test it:"
echo "   curl http://$EC2_IP/health/"
echo ""
