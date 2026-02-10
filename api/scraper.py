"""
Improved Rubber Price Scraper for RRISL (Rubber Research Institute of Sri Lanka)
Fixed URL patterns and enhanced OCR parsing
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
import re
import logging
import os

logger = logging.getLogger(__name__)

# OCR libraries
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    from io import BytesIO
    
    # Auto-detect Tesseract path
    tesseract_paths = [
        '/opt/homebrew/bin/tesseract',  # macOS Homebrew ARM
        '/usr/local/bin/tesseract',      # macOS Homebrew Intel
        '/usr/bin/tesseract',            # Linux
        'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',  # Windows
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"⚠️ OCR not available: {e}")


def scrape_rrisl_prices():
    """
    Scrapes REAL rubber prices from RRISL using OCR on price image.
    
    Returns:
        dict: Contains success status, prices, and metadata
    """
    # Try multiple URL patterns
    urls_to_try = [
        "http://www.rrisl.gov.lk/price_e.php?last=1",
        "http://www.rrisl.gov.lk/price_e.php",
        "https://www.rrisl.gov.lk/price_e.php?last=1",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    for url in urls_to_try:
        try:
            logger.info(f"🔄 Trying RRISL URL: {url}")
            
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract auction date
            auction_date = extract_auction_date(soup)
            logger.info(f"📅 Auction date: {auction_date}")
            
            # Extract image URL using multiple strategies
            image_url = extract_price_image_url(soup, url)
            
            if not image_url:
                logger.warning(f"⚠️ No image found at {url}, trying next...")
                continue
            
            logger.info(f"📸 Found price image: {image_url}")
            
            # Extract prices using OCR
            if not OCR_AVAILABLE:
                logger.error("❌ OCR not available")
                return {
                    'success': False, 
                    'error': 'OCR not configured. Install: pip install pytesseract pillow && brew install tesseract (or apt install tesseract-ocr)',
                    'imageUrl': image_url
                }
            
            prices = extract_prices_from_image(image_url, headers)
            
            if not prices:
                logger.warning("⚠️ No prices extracted from image")
                # Return partial success with image URL so user can debug
                return {
                    'success': False,
                    'error': 'OCR could not extract prices from image',
                    'imageUrl': image_url,
                    'auctionDate': auction_date.isoformat() if auction_date else None,
                    'suggestion': 'Check the image at the URL above - it may be low quality or format changed'
                }
            
            logger.info(f"✅ Successfully extracted {len(prices)} prices")
            
            return {
                'success': True,
                'lastUpdated': datetime.now().isoformat(),
                'auctionDate': auction_date.isoformat() if auction_date else None,
                'currency': 'LKR',
                'prices': prices,
                'source': 'RRISL',
                'sourceUrl': url,
                'priceImageUrl': image_url
            }
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Request failed for {url}: {e}")
            continue
        except Exception as e:
            logger.error(f"❌ Error with {url}: {e}", exc_info=True)
            continue
    
    return {
        'success': False,
        'error': 'All RRISL URLs failed',
        'lastUpdated': datetime.now().isoformat()
    }


def extract_auction_date(soup):
    """
    Extract auction date from HTML using multiple strategies.
    """
    try:
        # Strategy 1: Look for h5 with "Date of Auction"
        for h5 in soup.find_all('h5'):
            text = h5.get_text()
            if 'date' in text.lower() and 'auction' in text.lower():
                # Try DD-MM-YYYY format
                date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', text)
                if date_match:
                    day, month, year = date_match.groups()
                    return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
                
                # Try YYYY-MM-DD format
                date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
                if date_match:
                    year, month, day = date_match.groups()
                    return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
        
        # Strategy 2: Look for any element containing date pattern near "auction"
        page_text = soup.get_text()
        date_match = re.search(r'(?:auction|price)[^\d]*(\d{1,2})-(\d{1,2})-(\d{4})', page_text, re.I)
        if date_match:
            day, month, year = date_match.groups()
            return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
        
        # Strategy 3: Extract from image filename
        for img in soup.find_all('img'):
            src = img.get('src', '')
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', src)
            if date_match:
                year, month, day = date_match.groups()
                return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
                
    except Exception as e:
        logger.error(f"Error extracting date: {e}")
    
    return datetime.now().date()


def extract_price_image_url(soup, base_url):
    """
    Extract price image URL from HTML using multiple strategies.
    """
    base_domain = "http://www.rrisl.gov.lk"
    
    try:
        # Strategy 1: Look for images in content/images/prices/ path (current format)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'content/images/prices' in src.lower():
                return make_absolute_url(src, base_domain)
        
        # Strategy 2: Look for images in prices/ path
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if '/prices/' in src.lower() and src.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return make_absolute_url(src, base_domain)
        
        # Strategy 3: Look for images with price-related names
        for img in soup.find_all('img'):
            src = img.get('src', '')
            src_lower = src.lower()
            if any(keyword in src_lower for keyword in ['price', 'auction', 'rubber']):
                if src_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    return make_absolute_url(src, base_domain)
        
        # Strategy 4: Look for date-formatted image names (YYYY-MM-DD.jpg)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if re.search(r'\d{4}-\d{2}-\d{2}\.(jpg|jpeg|png)', src, re.I):
                return make_absolute_url(src, base_domain)
        
        # Strategy 5: Check page source for image URLs
        page_text = str(soup)
        patterns = [
            r'content/images/prices/[^"\']+\.(jpg|jpeg|png)',
            r'prices/\d{4}-\d{2}-\d{2}\.(jpg|jpeg|png)',
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                return make_absolute_url(match.group(0), base_domain)
                
    except Exception as e:
        logger.error(f"Error extracting image URL: {e}")
    
    return None


def make_absolute_url(url, base_domain):
    """Convert relative URL to absolute URL."""
    if url.startswith('http'):
        return url
    if url.startswith('//'):
        return 'http:' + url
    if url.startswith('/'):
        return base_domain + url
    return base_domain + '/' + url


def extract_prices_from_image(image_url, headers=None):
    """
    Extract prices from image using enhanced OCR.
    """
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        logger.info(f"🔍 Downloading image: {image_url}")
        
        response = requests.get(image_url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Check if we actually got an image
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type and 'octet-stream' not in content_type:
            logger.error(f"❌ URL did not return an image. Content-Type: {content_type}")
            return []
        
        img = Image.open(BytesIO(response.content))
        logger.info(f"📷 Image loaded: {img.size}, mode: {img.mode}")
        
        return extract_prices_with_ocr(img)
        
    except Exception as e:
        logger.error(f"❌ Error downloading/processing image: {e}", exc_info=True)
        return []


def extract_prices_with_ocr(img):
    """
    Extract prices from PIL Image using multiple OCR strategies.
    """
    try:
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Try multiple image enhancement strategies
        enhancement_strategies = [
            ('original', lambda x: x),
            ('enhanced', enhance_image_for_ocr),
            ('high_contrast', enhance_high_contrast),
            ('binarized', binarize_image),
        ]
        
        all_prices = []
        
        for strategy_name, enhance_func in enhancement_strategies:
            try:
                enhanced_img = enhance_func(img.copy())
                
                # Try multiple PSM modes
                psm_modes = [6, 4, 3, 11]  # Different page segmentation modes
                
                for psm in psm_modes:
                    try:
                        config = f'--psm {psm} --oem 3'
                        text = pytesseract.image_to_string(enhanced_img, config=config)
                        
                        if text.strip():
                            prices = parse_ocr_text(text)
                            if prices:
                                logger.info(f"✅ Found {len(prices)} prices with {strategy_name} + PSM {psm}")
                                all_prices.extend(prices)
                    except Exception as e:
                        logger.debug(f"OCR failed with PSM {psm}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Enhancement strategy {strategy_name} failed: {e}")
                continue
        
        # Deduplicate prices (keep first occurrence)
        seen_grades = set()
        unique_prices = []
        for price in all_prices:
            if price['gradeId'] not in seen_grades:
                seen_grades.add(price['gradeId'])
                unique_prices.append(price)
        
        return unique_prices
        
    except Exception as e:
        logger.error(f"❌ OCR error: {e}", exc_info=True)
        return []


def enhance_image_for_ocr(img):
    """Standard enhancement for OCR."""
    # Convert to grayscale
    img = img.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    
    # Apply median filter to reduce noise
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # Resize for better OCR (scale up 2x)
    new_size = (img.width * 2, img.height * 2)
    img = img.resize(new_size, Image.LANCZOS)
    
    return img


def enhance_high_contrast(img):
    """High contrast enhancement."""
    img = img.convert('L')
    
    # Auto contrast
    img = ImageOps.autocontrast(img, cutoff=2)
    
    # High contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3.0)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)
    
    return img


def binarize_image(img):
    """Convert to binary (black and white) for cleaner OCR."""
    img = img.convert('L')
    
    # Apply threshold to get binary image
    threshold = 128
    img = img.point(lambda x: 255 if x > threshold else 0, mode='1')
    
    return img.convert('L')


def parse_ocr_text(ocr_text):
    """
    Parse OCR text to extract grades and prices.
    Handles various OCR errors and formats.
    """
    prices = []
    
    # Normalize text - fix common OCR errors
    ocr_text = ocr_text.replace('|', '1').replace('l', '1').replace('O', '0')
    ocr_text = ocr_text.replace('Rs.', '').replace('RS.', '').replace('Rs', '')
    ocr_text = re.sub(r'\s+', ' ', ocr_text)
    
    logger.debug(f"Normalized OCR text:\n{ocr_text}")
    
    # Grade patterns - ordered from most specific to least specific
    # Format: (regex_pattern, grade_display_name)
    patterns = [
        # LATEX CREPE grades
        (r'LATEX\s*CREPE\s*[1Ii|]\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'LATEX CREPE 1X'),
        (r'LATEX\s*CREPE\s*1\s*[:\-]?\s*([\d,]+\.?\d*)', 'LATEX CREPE 1'),
        (r'LATEX\s*CREPE\s*2\s*[:\-]?\s*([\d,]+\.?\d*)', 'LATEX CREPE 2'),
        (r'LATEX\s*CREPE\s*3\s*[:\-]?\s*([\d,]+\.?\d*)', 'LATEX CREPE 3'),
        (r'LATEX\s*CREPE\s*4\s*[:\-]?\s*([\d,]+\.?\d*)', 'LATEX CREPE 4'),
        
        # SC.CR. grades (Sole Crepe)
        (r'SC[\.\s]*CR[\.\s]*[1Ii|]\s*[XxN]\s*[\(\[]?\s*BR\s*[\)\]]?\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 1X(BR)'),
        (r'SC[\.\s]*CR[\.\s]*2\s*[XxN]\s*[\(\[]?\s*BR\s*[\)\]]?\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 2X(BR)'),
        (r'SC[\.\s]*CR[\.\s]*3\s*[XxN]\s*[\(\[]?\s*BR\s*[\)\]]?\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 3X(BR)'),
        (r'SC[\.\s]*CR[\.\s]*4\s*[XxN]\s*[\(\[]?\s*BR\s*[\)\]]?\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 4X(BR)'),
        (r'SC[\.\s]*CR[\.\s]*[1Ii|]\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 1X'),
        (r'SC[\.\s]*CR[\.\s]*2\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 2X'),
        (r'SC[\.\s]*CR[\.\s]*3\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 3X'),
        (r'SC[\.\s]*CR[\.\s]*4\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SC.CR. 4X'),
        
        # SOLE CREPE (alternative naming)
        (r'SOLE\s*CREPE\s*[1Ii|]\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SOLE CREPE 1X'),
        (r'SOLE\s*CREPE\s*2\s*[XxN]\s*[:\-]?\s*([\d,]+\.?\d*)', 'SOLE CREPE 2X'),
        
        # SKIM CREPE
        (r'SKIM\s*CREPE\s*[:\-]?\s*([\d,]+\.?\d*)', 'SKIM CREPE'),
        
        # FLAT BARK
        (r'FLAT\s*BARK\s*[:\-]?\s*([\d,]+\.?\d*)', 'FLAT BARK'),
        
        # CREPE (generic)
        (r'(?:^|\s)CREPE\s*[:\-]?\s*([\d,]+\.?\d*)', 'CREPE'),
        
        # RSS grades (Ribbed Smoked Sheet)
        (r'RSS\s*[1Ii|]\s*[:\-]?\s*([\d,]+\.?\d*)', 'RSS 1'),
        (r'RSS\s*2\s*[:\-]?\s*([\d,]+\.?\d*)', 'RSS 2'),
        (r'RSS\s*3\s*[:\-]?\s*([\d,]+\.?\d*)', 'RSS 3'),
        (r'RSS\s*4\s*[:\-]?\s*([\d,]+\.?\d*)', 'RSS 4'),
        (r'RSS\s*5\s*[:\-]?\s*([\d,]+\.?\d*)', 'RSS 5'),
        
        # TSR grades (Technically Specified Rubber) - if applicable
        (r'TSR\s*10\s*[:\-]?\s*([\d,]+\.?\d*)', 'TSR 10'),
        (r'TSR\s*20\s*[:\-]?\s*([\d,]+\.?\d*)', 'TSR 20'),
    ]
    
    for pattern, grade_name in patterns:
        matches = re.finditer(pattern, ocr_text, re.I | re.M)
        
        for match in matches:
            try:
                price_str = match.group(1).replace(',', '').strip()
                
                # Skip if price string is empty or too short
                if not price_str or len(price_str) < 2:
                    continue
                
                price = float(price_str)
                
                # Validate price range (Rs. 100 - 2500 per kg is realistic)
                if 100 <= price <= 2500:
                    grade_id = grade_name.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                    
                    # Avoid duplicates
                    if not any(p['gradeId'] == grade_id for p in prices):
                        prices.append({
                            'gradeId': grade_id,
                            'grade': grade_name,
                            'price': price,
                            'unit': 'kg',
                            'change': 0  # Could calculate if previous prices available
                        })
                        logger.debug(f"✅ Matched: {grade_name} = Rs.{price}")
                        
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse price for {grade_name}: {e}")
                continue
    
    # Sort by grade name for consistent output
    prices.sort(key=lambda x: x['grade'])
    
    return prices


# =============================================================================
# Alternative: Line-by-line parsing (more robust for tabular data)
# =============================================================================

def parse_ocr_text_line_by_line(ocr_text):
    """
    Alternative parser that processes OCR text line by line.
    Better for tabular price data.
    """
    prices = []
    lines = ocr_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for lines with both grade keywords and numbers
        grade_keywords = [
            'LATEX', 'CREPE', 'SC.CR', 'SCCR', 'SOLE', 'SKIM', 
            'FLAT', 'BARK', 'RSS', 'TSR'
        ]
        
        has_keyword = any(kw in line.upper() for kw in grade_keywords)
        
        if has_keyword:
            # Extract all numbers from the line
            numbers = re.findall(r'[\d,]+\.?\d*', line)
            
            # Filter to plausible prices
            for num_str in numbers:
                try:
                    price = float(num_str.replace(',', ''))
                    if 100 <= price <= 2500:
                        # Try to extract grade name
                        grade_match = re.search(
                            r'(LATEX\s*CREPE\s*\d*\s*[XxN]?|SC\.?CR\.?\s*\d*\s*[XxN]?(?:\s*\(?BR\)?)?|'
                            r'SOLE\s*CREPE\s*\d*\s*[XxN]?|SKIM\s*CREPE|FLAT\s*BARK|RSS\s*\d+|TSR\s*\d+)',
                            line, re.I
                        )
                        
                        if grade_match:
                            grade_name = grade_match.group(1).upper().strip()
                            grade_name = re.sub(r'\s+', ' ', grade_name)
                            grade_id = grade_name.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                            
                            if not any(p['gradeId'] == grade_id for p in prices):
                                prices.append({
                                    'gradeId': grade_id,
                                    'grade': grade_name,
                                    'price': price,
                                    'unit': 'kg',
                                    'change': 0
                                })
                        break  # Use first valid price found in line
                        
                except ValueError:
                    continue
    
    return prices


# =============================================================================
# Debug/Test Function
# =============================================================================

def test_scraper():
    """Test the scraper and print detailed debug output."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("RRISL Rubber Price Scraper - Test Run")
    print("=" * 60)
    
    result = scrape_rrisl_prices()
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Source: {result.get('source', 'N/A')}")
    print(f"   Image URL: {result.get('priceImageUrl', 'N/A')}")
    print(f"   Auction Date: {result.get('auctionDate', 'N/A')}")
    
    if result.get('success'):
        print(f"\n💰 Prices ({len(result.get('prices', []))} grades):")
        for price in result.get('prices', []):
            print(f"   • {price['grade']}: Rs. {price['price']}/kg")
    else:
        print(f"\n❌ Error: {result.get('error')}")
        if result.get('suggestion'):
            print(f"💡 Suggestion: {result.get('suggestion')}")
    
    return result


if __name__ == '__main__':
    test_scraper()