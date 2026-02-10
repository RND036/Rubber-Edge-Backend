from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .scraper import scrape_rrisl_prices
from .models import RubberPrice, MarketStats, ScrapingLog
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import traceback


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_rrisl_prices_task(self):
    """
    Periodic task: Scrape RRISL and broadcast to all WebSocket clients
    """
    logger.info("🔄 Starting RRISL price scrape task...")
    
    try:
        # Scrape RRISL website
        data = scrape_rrisl_prices()
        
        # Check if scraping was successful
        is_success = data.get('success') or data.get('status') == 'success'
        
        # Log the scraping attempt
        log = ScrapingLog.objects.create(
            success=is_success,
            grades_scraped=len(data.get('prices', [])),
            error_message=data.get('error', ''),
            source_url=data.get('sourceUrl', 'https://www.rrisl.lk')
        )
        
        if is_success:
            auction_date = data.get('auctionDate') or data.get('auction_date')
            prices_data = data.get('prices', [])
            
            if not prices_data:
                logger.warning("⚠️ No prices found in scrape data")
                return {
                    'success': False,
                    'status': 'failed',
                    'error': 'No prices found in scrape data',
                    'count': 0,
                    'prices': []
                }
            
            # Save prices to database
            saved_count = 0
            saved_prices = []
            
            for price_data in prices_data:
                try:
                    price_obj, created = RubberPrice.objects.update_or_create(
                        grade=price_data['grade'],
                        auction_date=auction_date,
                        defaults={
                            'price': Decimal(str(price_data['price'])),
                            'currency': data.get('currency', 'LKR')
                        }
                    )
                    
                    # Calculate change from previous auction
                    price_obj.calculate_change()
                    saved_count += 1
                    saved_prices.append(price_obj)
                    
                    action = "Created" if created else "Updated"
                    logger.info(f"  {action}: {price_obj}")
                    
                except Exception as e:
                    logger.error(f"❌ Error saving {price_data['grade']}: {e}")
            
            # Calculate and save market statistics
            calculate_market_stats(auction_date)
            
            # Prepare broadcast data with calculated changes
            broadcast_data = prepare_broadcast_data(data)
            
            # Broadcast to all connected WebSocket clients
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "rrisl_live",
                    {
                        "type": "price_update",
                        "data": broadcast_data
                    }
                )
                logger.info(f"✅ Broadcast sent to WebSocket clients")
            except Exception as e:
                logger.error(f"❌ Error broadcasting: {e}")
            
            logger.info(f"✅ Task completed: {saved_count} grades saved and broadcast to clients")
            
            # Return both 'success' and 'status' for compatibility
            return {
                'success': True,
                'status': 'success',
                'count': saved_count,
                'grades_count': saved_count,
                'auction_date': auction_date,
                'prices': [
                    {
                        'grade': p.grade,
                        'price': float(p.price),
                        'change': float(p.change_percentage)
                    }
                    for p in saved_prices
                ]
            }
        else:
            error_msg = data.get('error', 'Unknown error during scraping')
            logger.error(f"❌ Scrape task failed: {error_msg}")
            
            # Retry on failure
            try:
                raise self.retry(countdown=300)  # Retry after 5 minutes
            except self.MaxRetriesExceededError:
                logger.error("❌ Max retries exceeded for scraping task")
            
            return {
                'success': False,
                'status': 'error',
                'error': error_msg,
                'count': 0,
                'prices': []
            }
    
    except Exception as e:
        error_trace = traceback.format_exc()
        error_msg = f'{type(e).__name__}: {str(e)}'
        logger.error(f"❌ Exception in scrape task: {error_msg}\n{error_trace}")
        
        # Log exception
        ScrapingLog.objects.create(
            success=False,
            grades_scraped=0,
            error_message=f'{error_msg}\n\n{error_trace}',
            source_url='https://www.rrisl.lk'
        )
        
        return {
            'success': False,
            'status': 'error',
            'error': error_msg,
            'traceback': error_trace,
            'count': 0,
            'prices': []
        }


def calculate_market_stats(auction_date):
    """Calculate market statistics for the given date"""
    try:
        all_prices = RubberPrice.objects.filter(auction_date=auction_date)
        
        if all_prices.exists():
            prices_list = [float(p.price) for p in all_prices]
            
            # Get week range
            week_ago = datetime.strptime(auction_date, '%Y-%m-%d').date() - timedelta(days=7)
            week_prices = RubberPrice.objects.filter(
                auction_date__gte=week_ago,
                auction_date__lte=auction_date
            )
            
            # Get month range
            month_ago = datetime.strptime(auction_date, '%Y-%m-%d').date() - timedelta(days=30)
            month_prices = RubberPrice.objects.filter(
                auction_date__gte=month_ago,
                auction_date__lte=auction_date
            )
            
            week_prices_list = [float(p.price) for p in week_prices] if week_prices.exists() else prices_list
            month_prices_list = [float(p.price) for p in month_prices] if month_prices.exists() else prices_list
            
            MarketStats.objects.update_or_create(
                date=auction_date,
                defaults={
                    'week_high': max(week_prices_list),
                    'week_low': min(week_prices_list),
                    'month_high': max(month_prices_list),
                    'month_low': min(month_prices_list),
                    'avg_volume': '2,500 MT'  # Static for now, can be scraped
                }
            )
            
            logger.info(f"✅ Market stats calculated for {auction_date}")
            
    except Exception as e:
        logger.error(f"❌ Error calculating market stats: {e}")


def prepare_broadcast_data(scrape_data):
    """Prepare data for WebSocket broadcast with calculated changes"""
    try:
        auction_date = scrape_data.get('auctionDate') or scrape_data.get('auction_date')
        prices = RubberPrice.objects.filter(auction_date=auction_date)
        
        prices_list = []
        for p in prices:
            prices_list.append({
                'gradeId': p.grade.lower().replace(' ', ''),
                'grade': p.grade,
                'price': float(p.price),
                'unit': 'kg',
                'change': float(p.change_percentage)
            })
        
        return {
            'success': True,
            'lastUpdated': datetime.now().isoformat(),
            'auctionDate': auction_date,
            'currency': scrape_data.get('currency', 'LKR'),
            'exchangeRate': scrape_data.get('exchangeRate', 325),
            'prices': prices_list,
            'source': 'RRISL'
        }
    except Exception as e:
        logger.error(f"Error preparing broadcast data: {e}")
        return scrape_data


@shared_task
def calculate_market_stats_task():
    """
    Periodic task: Calculate market statistics
    """
    try:
        from django.db.models import Max, Min, Avg
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Get weekly stats
        weekly_stats = RubberPrice.objects.filter(
            auction_date__gte=week_ago
        ).aggregate(
            week_high=Max('price'),
            week_low=Min('price')
        )
        
        # Get monthly stats
        monthly_stats = RubberPrice.objects.filter(
            auction_date__gte=month_ago
        ).aggregate(
            month_high=Max('price'),
            month_low=Min('price'),
            avg_volume=Avg('price')
        )
        
        # Create or update stats
        MarketStats.objects.update_or_create(
            date=today,
            defaults={
                'week_high': weekly_stats['week_high'] or Decimal('0'),
                'week_low': weekly_stats['week_low'] or Decimal('0'),
                'month_high': monthly_stats['month_high'] or Decimal('0'),
                'month_low': monthly_stats['month_low'] or Decimal('0'),
                'avg_volume': monthly_stats['avg_volume'] or Decimal('0')
            }
        )
        
        logger.info(f"✅ Market stats task completed for {today}")
        
        return {
            'success': True,
            'status': 'success',
            'date': str(today),
            'stats': {
                'week_high': float(weekly_stats['week_high'] or 0),
                'week_low': float(weekly_stats['week_low'] or 0),
                'month_high': float(monthly_stats['month_high'] or 0),
                'month_low': float(monthly_stats['month_low'] or 0)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in market stats task: {e}")
        return {
            'success': False,
            'status': 'error',
            'error': str(e)
        }
