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
    
    # Extract product URLs from the page BEFORE removing elements
    extracted_urls = extract_product_urls_from_html(soup, WEBSITE_URL)
    
    # Remove 'Noise' (elements that don't help the AI answer questions)
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose() # Physically delete these from the parsed content
        
    # Extract the clean text, using a space to separate words
    clean_text = soup.get_text(separator=' ', strip=True)
    return clean_text, extracted_urls


def extract_product_urls_from_html(soup, base_url):
    """
    Extract product URLs from the HTML soup using link patterns
    
    Args:
        soup: BeautifulSoup object of the page
        base_url: Base URL for resolving relative links
        
    Returns:
        list: List of product URLs found in the page
    """
    product_urls = []
    product_patterns = [
        '/products/',      # Main product pattern (catches /products/product-name)
        '/product/',       # Alternative singular form
        '/item/',          # Item pages
        '/p/',             # Short product ID form
        '/sku/',           # SKU-based URLs
        '/buy/',           # Buy pages
    ]
    
    try:
        # Find all links in the page
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Check if URL matches product patterns
            url_lower = full_url.lower()
            for pattern in product_patterns:
                if pattern in url_lower:
                    # Avoid duplicates and filter out tracking params
                    if 'utm_' not in url_lower and full_url not in product_urls:
                        product_urls.append(full_url)
                    break
        
        logger.debug(f"🔗 Extracted {len(product_urls)} product URLs from {base_url}")
        return product_urls
    
    except Exception as e:
        logger.warning(f"⚠️ Error extracting URLs from {base_url}: {str(e)}")
        return []


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
    Filter URLs - keep valid pages, exclude duplicates and invalid URLs.
    Now includes individual product pages to enable product link responses.
    
    Args:
        urls: List of URLs from sitemap
        
    Returns:
        list: Filtered URLs (all valid pages including product pages)
    """
    filtered_urls = []
    
    # Patterns to SKIP (invalid or duplicate-prone URLs)
    skip_patterns = [
        'mailto:',           # Email links
        'tel:',              # Phone links
        '#',                 # Anchor-only links
        '?sort=',            # Sort/filter parameters that create duplicates
        '?filter=',          # Filter parameters
        '&utm_',             # Tracking parameters
        'logout',            # Logout pages
        'cart/delete',       # Shopping cart delete actions
    ]
    
    for url in urls:
        url_lower = url.lower()
        
        # Skip if matches skip patterns
        skip = False
        for pattern in skip_patterns:
            if pattern in url_lower:
                skip = True
                logger.debug(f"⏭️ Skipping invalid/duplicate URL: {url}")
                break
        
        if skip:
            continue
        
        # Keep valid URLs (including product pages now)
        filtered_urls.append(url)
        logger.debug(f"✅ Keeping page: {url}")
    
    logger.info(f"📊 Filtered: {len(urls)} URLs → {len(filtered_urls)} valid pages (including product pages)")
    return filtered_urls


def scrape_multiple_urls(urls, rate_limit_delay=1, max_urls=50):
    """
    Scrape multiple URLs and return dict of URL -> content, plus extracted product URLs
    
    Args:
        urls: List of URLs to scrape
        rate_limit_delay: Delay in seconds between requests to be respectful
        max_urls: Maximum number of URLs to scrape (prevents timeout on huge sitemaps)
        
    Returns:
        tuple: (url_contents dict, product_urls dict) where:
            - url_contents: Mapping of URL -> scraped text content
            - product_urls: Mapping of URL -> list of product URLs found in that page
    """
    # Limit to avoid scraping forever on huge sitemaps
    if len(urls) > max_urls:
        logger.warning(f"⚠️ Sitemap has {len(urls)} URLs, limiting to {max_urls} (most important pages)")
        urls = urls[:max_urls]
    
    url_contents = {}
    product_urls_per_page = {}
    successful_scrapes = 0
    failed_urls = []
    
    logger.info(f"🚀 Starting to scrape {len(urls)} URLs...")
    
    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"📄 [{idx}/{len(urls)}] Scraping: {url}")
            
            text, extracted_urls = scrape_website(url)
            url_contents[url] = text
            product_urls_per_page[url] = extracted_urls
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
    
    return url_contents, product_urls_per_page


def scrape_website_sitemap(base_url, rate_limit_delay=1, max_urls=50):
    """
    Scrape entire website using sitemap.xml - only main pages with product listings
    
    Args:
        base_url: The base website URL
        rate_limit_delay: Delay in seconds between requests (default: 1 second)
        max_urls: Maximum number of URLs to scrape (default: 50)
        
    Returns:
        tuple: (url_contents dict, product_urls_per_page dict)
    """
    logger.info(f"🌐 Starting whole website scrape for: {base_url}")
    
    # Fetch all URLs from sitemap
    urls = fetch_sitemap_urls(base_url)
    
    if not urls:
        logger.warning(f"⚠️ No URLs found in sitemap, falling back to scraping single URL")
        text_content, extracted_urls = scrape_website(base_url)
        return {base_url: text_content}, {base_url: extracted_urls}
    
    # Filter to keep only main pages, remove individual product pages
    urls = filter_product_pages(urls)
    
    # Scrape all URLs - now returns tuple
    url_contents, product_urls_per_page = scrape_multiple_urls(urls, rate_limit_delay, max_urls)
    
    return url_contents, product_urls_per_page