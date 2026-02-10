import json
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CoreConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """When client connects to WebSocket"""
        # Add this client to the RRISL broadcast group
        await self.channel_layer.group_add("rrisl_live", self.channel_name)
        
        # Accept the connection
        await self.accept()
        
        # Send welcome message
        await self.send(json.dumps({
            "type": "connection",
            "message": "✅ Connected to rubber farming backend - RRISL live data enabled",
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"✅ Client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """When client disconnects"""
        # Remove from broadcast group
        await self.channel_layer.group_discard("rrisl_live", self.channel_name)
        logger.info(f"❌ Client disconnected: {self.channel_name} (code: {close_code})")

    async def receive(self, text_data):
        """Handle incoming messages from client"""
        try:
            data = json.loads(text_data)
            action = data.get("action")
            
            logger.debug(f"📥 Received action: {action} from {self.channel_name}")

            if action == "ping":
                # Respond to heartbeat
                await self.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif action == "get_prices":
                # Client requesting latest prices from database
                await self.send_latest_prices()
            
            elif action == "subscribe":
                # Explicitly subscribe to price updates
                await self.send(json.dumps({
                    "type": "subscribed",
                    "message": "✅ Subscribed to RRISL price updates",
                    "timestamp": datetime.now().isoformat()
                }))
            
            else:
                # Unknown action
                await self.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                }))
                
        except json.JSONDecodeError:
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
            logger.error(f"Invalid JSON received from {self.channel_name}")
            
        except Exception as e:
            await self.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
            logger.error(f"Error handling message: {e}")

    async def price_update(self, event):
        """
        Receive broadcast from Celery task and send to WebSocket client
        This is called when Celery broadcasts new RRISL prices
        """
        await self.send(json.dumps({
            "type": "price_update",
            "data": event["data"],
            "timestamp": datetime.now().isoformat()
        }))
        logger.info(f"📤 Sent price update to {self.channel_name}")
    
    async def send_latest_prices(self):
        """Send latest prices from database to client"""
        try:
            from .models import RubberPrice, MarketStats
            from django.db.models import Max
            
            # Get latest auction date
            latest_date = await self.get_latest_date()
            
            if latest_date:
                prices = await self.get_prices_for_date(latest_date)
                stats = await self.get_stats_for_date(latest_date)
                
                await self.send(json.dumps({
                    "type": "latest_prices",
                    "data": {
                        "success": True,
                        "lastUpdated": datetime.now().isoformat(),
                        "auctionDate": str(latest_date),
                        "currency": "LKR",
                        "exchangeRate": 325,
                        "prices": prices,
                        "marketStats": stats,
                        "source": "Database"
                    }
                }))
                logger.info(f"📊 Sent latest prices ({len(prices)} grades) to {self.channel_name}")
            else:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "No prices available in database"
                }))
                
        except Exception as e:
            logger.error(f"Error sending latest prices: {e}")
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to fetch latest prices"
            }))
    
    @staticmethod
    async def get_latest_date():
        """Get latest auction date from database"""
        from .models import RubberPrice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def _get_date():
            return RubberPrice.objects.values_list('auction_date', flat=True).first()
        
        return await _get_date()
    
    @staticmethod
    async def get_prices_for_date(date):
        """Get all prices for a specific date"""
        from .models import RubberPrice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def _get_prices():
            prices_qs = RubberPrice.objects.filter(auction_date=date)
            return [
                {
                    'gradeId': p.grade.lower().replace(' ', ''),
                    'grade': p.grade,
                    'price': float(p.price),
                    'unit': 'kg',
                    'change': float(p.change_percentage)
                }
                for p in prices_qs
            ]
        
        return await _get_prices()
    
    @staticmethod
    async def get_stats_for_date(date):
        """Get market stats for a specific date"""
        from .models import MarketStats
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def _get_stats():
            stats = MarketStats.objects.filter(date=date).first()
            if stats:
                return {
                    'weekHigh': float(stats.week_high),
                    'weekLow': float(stats.week_low),
                    'monthHigh': float(stats.month_high),
                    'monthLow': float(stats.month_low),
                    'avgVolume': stats.avg_volume
                }
            return None
        
        return await _get_stats()
