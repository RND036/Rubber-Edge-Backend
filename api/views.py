from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import logging
import json

from .models import RubberPrice, MarketStats, ScrapingLog
from .scraper import scrape_rrisl_prices

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def get_rubber_prices(request):
    """REST API endpoint for fetching rubber prices"""
    try:
        logger.info("📊 API request: get_rubber_prices")

        latest_date = RubberPrice.objects.values_list('auction_date', flat=True).first()

        if latest_date:
            prices_qs = RubberPrice.objects.filter(auction_date=latest_date)
            prices = []

            for p in prices_qs:
                prices.append({
                    'gradeId': p.grade.lower().replace(' ', ''),
                    'grade': p.grade,
                    'price': float(p.price),
                    'unit': 'kg',
                    'change': float(p.change_percentage)
                })

            stats = MarketStats.objects.filter(date=latest_date).first()
            market_stats = {
                'weekHigh': float(stats.week_high) if stats else 0,
                'weekLow': float(stats.week_low) if stats else 0,
                'monthHigh': float(stats.month_high) if stats else 0,
                'monthLow': float(stats.month_low) if stats else 0,
                'avgVolume': stats.avg_volume if stats else 'N/A'
            }

            historical_labels = []
            historical_data = []

            for i in range(5, -1, -1):
                month_date = datetime.now() - timedelta(days=30 * i)
                historical_labels.append(month_date.strftime('%b'))

                month_prices = RubberPrice.objects.filter(
                    auction_date__year=month_date.year,
                    auction_date__month=month_date.month,
                    grade='RSS3'
                )

                if month_prices.exists():
                    avg = sum(float(p.price) for p in month_prices) / len(month_prices)
                    historical_data.append(round(avg, 2))
                else:
                    historical_data.append(580)  # Default fallback

            response_data = {
                'success': True,
                'lastUpdated': datetime.now().isoformat(),
                'auctionDate': str(latest_date),
                'currency': 'LKR',
                'exchangeRate': 325,
                'prices': prices,
                'historicalData': {
                    'labels': historical_labels,
                    'datasets': [{
                        'data': historical_data,
                        'color': '#F4D03F',
                        'strokeWidth': 3
                    }]
                },
                'marketStats': market_stats,
                'source': 'RRISL Database'
            }

            logger.info(f"✅ Returned {len(prices)} prices for {latest_date}")
            return JsonResponse(response_data)

        else:
            logger.warning("⚠️ No data in database, scraping live from RRISL...")
            data = scrape_rrisl_prices()

            if data.get('success'):
                data['historicalData'] = {
                    'labels': ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
                    'datasets': [{
                        'data': [520, 535, 555, 570, 575, 580],
                        'color': '#F4D03F',
                        'strokeWidth': 3
                    }]
                }
                data['marketStats'] = {
                    'weekHigh': 595,
                    'weekLow': 565,
                    'monthHigh': 610,
                    'monthLow': 520,
                    'avgVolume': '2,500 MT'
                }

            return JsonResponse(data)

    except Exception as e:
        logger.error(f"❌ Error in get_rubber_prices: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch rubber prices'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def trigger_scrape(request):
    """Manual trigger for scraping RRISL (for testing/admin)"""
    try:
        from .tasks import scrape_rrisl_prices_task

        logger.info("🔄 Manual scrape triggered via API")

        result = scrape_rrisl_prices_task.delay()

        return JsonResponse({
            'success': True,
            'message': '🔄 RRISL scraping started',
            'task_id': str(result.id),
            'note': 'Data will be available shortly and broadcast to connected clients'
        })

    except Exception as e:
        logger.error(f"❌ Error triggering scrape: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to trigger scrape. Make sure Celery is running.'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_market_stats(request):
    """Get latest market statistics"""
    try:
        latest_stats = MarketStats.objects.first()

        if latest_stats:
            return JsonResponse({
                'success': True,
                'date': str(latest_stats.date),
                'stats': {
                    'weekHigh': float(latest_stats.week_high),
                    'weekLow': float(latest_stats.week_low),
                    'monthHigh': float(latest_stats.month_high),
                    'monthLow': float(latest_stats.month_low),
                    'avgVolume': latest_stats.avg_volume
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No market statistics available'
            })

    except Exception as e:
        logger.error(f"Error in get_market_stats: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_historical_prices(request):
    """Get historical price data for charts"""
    try:
        grade = request.GET.get('grade', 'RSS3')
        months = int(request.GET.get('months', 6))

        labels = []
        data = []

        for i in range(months - 1, -1, -1):
            month_date = datetime.now() - timedelta(days=30 * i)
            labels.append(month_date.strftime('%b'))

            month_prices = RubberPrice.objects.filter(
                auction_date__year=month_date.year,
                auction_date__month=month_date.month,
                grade=grade
            )

            if month_prices.exists():
                avg_price = sum(float(p.price) for p in month_prices) / len(month_prices)
                data.append(round(avg_price, 2))
            else:
                data.append(None)

        return JsonResponse({
            'success': True,
            'grade': grade,
            'labels': labels,
            'data': data
        })

    except Exception as e:
        logger.error(f"Error in get_historical_prices: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_scraping_logs(request):
    """Get recent scraping logs"""
    try:
        logs = ScrapingLog.objects.all()[:20]

        logs_data = []
        for log in logs:
            logs_data.append({
                'timestamp': log.timestamp.isoformat(),
                'success': log.success,
                'grades_scraped': log.grades_scraped,
                'error_message': log.error_message,
                'source_url': log.source_url
            })

        return JsonResponse({
            'success': True,
            'logs': logs_data
        })

    except Exception as e:
        logger.error(f"Error in get_scraping_logs: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===================== NEW: AI AGENT ENDPOINT =====================

@csrf_exempt
@require_http_methods(["POST"])
def llm_chat_with_tools(request):
    """
    Endpoint used by frontend DiseaseAIAgent.callLLMWithTools.

    Request JSON:
    {
      "messages": [ { "role": "user"|"assistant"|"system", "content": "..." }, ... ],
      "tools": [ ... ],
      "diseasecontext": "Black Pod",
      "usermessage": "What are the symptoms?"
    }

    Response JSON (matches AgentResponse mapping in AIAgent.tsx):
    {
      "message": "answer text",
      "toolcalls": [],
      "thinking": "",
      "iscomplete": true
    }
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Invalid JSON in llm_chat_with_tools: {e}")
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    messages = body.get("messages", [])
    tools = body.get("tools", [])
    disease_context = body.get("diseasecontext", "")
    user_message = body.get("usermessage")

    if not user_message:
        return JsonResponse({"error": "usermessage is required"}, status=400)

    lower = user_message.lower()
    disease = disease_context or "this disease"

    # Simple rule-based agent for now (no external LLM call)
    if "symptom" in lower or "sign" in lower:
        answer = (
            f"The main symptoms of {disease} include leaf spots, discoloration, "
            f"and premature leaf drop. Early detection is important for good control."
        )
    elif "treat" in lower or "cure" in lower:
        answer = (
            f"Treatment for {disease} commonly uses fungicide sprays combined with "
            f"better drainage, pruning, and removal of infected material."
        )
    elif "prevent" in lower or "avoid" in lower:
        answer = (
            f"Prevention of {disease} focuses on correct spacing, drainage, "
            f"sanitation, and preventive fungicide applications during high‑risk periods."
        )
    elif "cost" in lower or "expensive" in lower:
        answer = (
            f"The cost of managing {disease} depends on plantation size and products used, "
            f"but preventive management is usually cheaper than treating severe outbreaks."
        )
    else:
        answer = (
            f"You can ask about symptoms, treatment, prevention, management schedule, "
            f"or cost for {disease}. Please tell what you need help with."
        )

    response = {
        "message": answer,
        "toolcalls": [],   # you can later return real tool calls if you move tools to backend
        "thinking": "",
        "iscomplete": True,
    }
    return JsonResponse(response, status=200)
