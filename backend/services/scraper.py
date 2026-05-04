# Website crawling logic
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

def scrape_website(WEBSITE_URL):
    """Scrape a single website URL and return clean text"""
    headers = {"User-Agent": "Mozilla/5.0"} # Pretend to be a real user browser
    response = requests.get(WEBSITE_URL, headers=headers, timeout=10)
    
    # Parse the HTML code
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove 'Noise' (elements that don't help the AI answer questions)
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose() # Physically delete these from the parsed content
        
    # Extract the clean text, using a space to separate words
    clean_text = soup.get_text(separator=' ', strip=True)
    return clean_text


def fetch_sitemap_urls(base_url):
    """
    Fetch and parse sitemap.xml to extract all URLs from a website
    Handles both regular sitemaps and sitemapindex (parent sitemaps)
    
    Args:
        base_url: The base website URL (e.g., https://example.com)
        
    Returns:
        list: List of URLs found in the sitemap(s)
    """
    try:
        # Construct sitemap URL
        parsed_url = urlparse(base_url)
        sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
        
        logger.info(f"🔍 Fetching sitemap from: {sitemap_url}")
        
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse XML sitemap
        root = ET.fromstring(response.content)
        
        # Define namespace for sitemap
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check if this is a sitemapindex (contains links to other sitemaps)
        sitemap_links = root.findall('.//ns:sitemap/ns:loc', namespaces)
        if not sitemap_links:
            sitemap_links = root.findall('.//sitemap/loc')
        
        # If this is a sitemapindex, fetch all child sitemaps
        if sitemap_links:
            logger.info(f"📑 Detected sitemapindex with {len(sitemap_links)} child sitemaps")
            all_urls = []
            
            for sitemap_link_elem in sitemap_links:
                child_sitemap_url = sitemap_link_elem.text
                logger.info(f"🔍 Fetching child sitemap: {child_sitemap_url}")
                
                try:
                    child_response = requests.get(child_sitemap_url, headers=headers, timeout=10)
                    child_response.raise_for_status()
                    child_root = ET.fromstring(child_response.content)
                    
                    # Extract URLs from child sitemap
                    child_urls = child_root.findall('.//ns:url/ns:loc', namespaces)
                    if not child_urls:
                        child_urls = child_root.findall('.//url/loc')
                    
                    for url_elem in child_urls:
                        all_urls.append(url_elem.text)
                    
                    logger.info(f"✅ Found {len(child_urls)} URLs in {child_sitemap_url}")
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching child sitemap {child_sitemap_url}: {str(e)}")
            
            logger.info(f"✅ Total URLs found across all sitemaps: {len(all_urls)}")
            return all_urls
        
        # Otherwise, extract URLs directly from the regular sitemap
        urls = []
        url_elements = root.findall('.//ns:url/ns:loc', namespaces)
        if not url_elements:
            url_elements = root.findall('.//url/loc')
        
        for url_elem in url_elements:
            urls.append(url_elem.text)
        
        logger.info(f"✅ Found {len(urls)} URLs in sitemap")
        return urls
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Could not fetch sitemap: {str(e)}")
        return []
    except ET.ParseError as e:
        logger.warning(f"⚠️ Error parsing sitemap XML: {str(e)}")
        return []


def filter_product_pages(urls):
    """
    Filter out individual product pages, keep only listing/category pages
    
    Args:
        urls: List of URLs from sitemap
        
    Returns:
        list: Filtered URLs (only main pages with product listings)
    """
    filtered_urls = []
    
    # Patterns that indicate individual product pages to SKIP
    skip_patterns = [
        '/product/',          # /product/123 or /product/name
        '/products/p/',       # /products/p/123
        '/item/',             # /item/123
        '/p/',                # Short product URL
        '/sku/',              # /sku/12345
        'product-id=',        # Query parameter
        'productid=',         # Query parameter
        '/buy/',              # /buy/product-name
        '?id=',               # Product ID query
        '?product=',          # Product query
    ]
    
    # Patterns that indicate listing/category pages to KEEP
    keep_patterns = [
        '/collections/',      # Category pages
        '/categories/',       # Category pages
        '/shop',              # Shop page
        '/products',          # Product listing (not individual)
        '/pages/',            # Static pages
        '/blog',              # Blog pages
        '/search',            # Search results
        '/?page=',            # Paginated listings
    ]
    
    for url in urls:
        url_lower = url.lower()
        
        # Skip if matches skip patterns
        skip = False
        for pattern in skip_patterns:
            if pattern in url_lower:
                skip = True
                logger.debug(f"⏭️ Skipping product page: {url}")
                break
        
        if skip:
            continue
        
        # Keep if matches keep patterns or is root/home page
        keep = False
        if url_lower.endswith('.lk/') or url_lower.endswith('.com/') or url_lower.endswith('.com'):
            keep = True  # Root/home page
        else:
            for pattern in keep_patterns:
                if pattern in url_lower:
                    keep = True
                    break
        
        if keep:
            filtered_urls.append(url)
            logger.debug(f"✅ Keeping page: {url}")
    
    logger.info(f"📊 Filtered: {len(urls)} URLs → {len(filtered_urls)} main pages")
    return filtered_urls


def scrape_multiple_urls(urls, rate_limit_delay=1, max_urls=50):
    """
    Scrape multiple URLs and combine their content
    
    Args:
        urls: List of URLs to scrape
        rate_limit_delay: Delay in seconds between requests to be respectful
        max_urls: Maximum number of URLs to scrape (prevents timeout on huge sitemaps)
        
    Returns:
        str: Combined clean text from all URLs
    """
    # Limit to avoid scraping forever on huge sitemaps
    if len(urls) > max_urls:
        logger.warning(f"⚠️ Sitemap has {len(urls)} URLs, limiting to {max_urls} (most important pages)")
        urls = urls[:max_urls]
    
    combined_text = ""
    successful_scrapes = 0
    failed_urls = []
    
    logger.info(f"🚀 Starting to scrape {len(urls)} URLs...")
    
    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"📄 [{idx}/{len(urls)}] Scraping: {url}")
            
            text = scrape_website(url)
            combined_text += f"\n\n--- Page: {url} ---\n{text}"
            successful_scrapes += 1
            
            # Rate limiting - be respectful to the server
            if idx < len(urls):  # Don't sleep after last URL
                time.sleep(rate_limit_delay)
            
        except requests.exceptions.Timeout:
            logger.warning(f"❌ Timeout on {url}")
            failed_urls.append(url)
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Failed to scrape {url}: {str(e)}")
            failed_urls.append(url)
        except Exception as e:
            logger.warning(f"❌ Error processing {url}: {str(e)}")
            failed_urls.append(url)
    
    logger.info(f"✅ Scraping complete: {successful_scrapes}/{len(urls)} successful")
    if failed_urls:
        logger.info(f"⚠️ Failed URLs: {len(failed_urls)}")
    
    return combined_text


def scrape_website_sitemap(base_url, rate_limit_delay=1, max_urls=50):
    """
    Scrape entire website using sitemap.xml - only main pages with product listings
    
    Args:
        base_url: The base website URL
        rate_limit_delay: Delay in seconds between requests (default: 1 second)
        max_urls: Maximum number of URLs to scrape (default: 50)
        
    Returns:
        str: Combined clean text from all website pages
    """
    logger.info(f"🌐 Starting whole website scrape for: {base_url}")
    
    # Fetch all URLs from sitemap
    urls = fetch_sitemap_urls(base_url)
    
    if not urls:
        logger.warning(f"⚠️ No URLs found in sitemap, falling back to scraping single URL")
        return scrape_website(base_url)
    
    # Filter to keep only main pages, remove individual product pages
    urls = filter_product_pages(urls)
    
    # Scrape all URLs
    combined_text = scrape_multiple_urls(urls, rate_limit_delay, max_urls)
    
    return combined_text