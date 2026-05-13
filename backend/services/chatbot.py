import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from core.config import Config

# ============================================================================
# MANUAL API CONTROL FOR CHAT (Backend Configuration)
# ============================================================================
# Change this value to switch which API is used for chat responses
# Options: "google" or "openrouter"
# CHAT_API_PROVIDER = "google"
CHAT_API_PROVIDER = "openrouter"
# ============================================================================

def is_product_url(url):
    """
    Check if a URL is a product page URL
    
    Args:
        url: URL to check
    
    Returns:
        bool: True if URL matches product page patterns
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Product URL patterns
    product_patterns = [
        '/product/',
        '/products/p/',
        '/item/',
        '/p/',
        '/sku/',
        'product-id=',
        'productid=',
        '/buy/',
    ]
    
    for pattern in product_patterns:
        if pattern in url_lower:
            return True
    
    return False


def extract_product_urls(text):
    """
    Extract product URLs from retrieved context text.
    
    Looks for URLs that contain product-related patterns:
    /product/, /item/, /sku/, /p/, /products/p/, product-id=, productid=, etc.
    
    Args:
        text: Text that may contain URL markers like "--- Page: https://example.com/product/123 ---"
    
    Returns:
        list: Unique product URLs found in the text
    """
    # Product URL patterns
    product_patterns = [
        r'/product/[^/\s\?]+',      # /product/name or /product/123
        r'/products/p/[^\s\?]+',    # /products/p/123
        r'/item/[^/\s\?]+',         # /item/123
        r'/p/[^/\s\?]+',            # /p/123
        r'/sku/[^/\s\?]+',          # /sku/12345
        r'product[?&]id=[^\s&]+',   # ?product-id=123 or &product-id=123
        r'productid[?&]id=[^\s&]+', # ?productid=123 or &productid=123
        r'/buy/[^/\s\?]+',          # /buy/product-name
    ]
    
    product_urls = []
    
    # Extract all URLs from the text (including those marked with "--- Page: URL ---")
    # Look for URLs in the "--- Page: URL ---" markers
    page_marker_pattern = r'---\s*Page:\s*(https?://[^\s\-]+)\s*---'
    urls_from_markers = re.findall(page_marker_pattern, text)
    
    # Also look for standalone URLs
    url_pattern = r'https?://[^\s\)<>\[\]"\'{}]+'
    urls_found = re.findall(url_pattern, text)
    
    all_urls = urls_from_markers + urls_found
    
    # Filter to only product URLs and remove duplicates while preserving order
    seen = set()
    for url in all_urls:
        url_lower = url.lower()
        
        # Check if URL matches any product pattern
        is_product = False
        for pattern in product_patterns:
            if re.search(pattern, url_lower):
                is_product = True
                break
        
        if is_product and url not in seen:
            product_urls.append(url)
            seen.add(url)
    
    return product_urls


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _extract_product_names_from_answer(answer):
    if not answer:
        return []

    names = []
    bold_pattern = r"\*\*(.+?)\*\*"
    for match in re.findall(bold_pattern, answer):
        name = match.strip()
        if name:
            names.append(name)

    if names:
        return names

    line_pattern = r"^\s*\d+\.\s+([^\n:-]+)"
    for match in re.findall(line_pattern, answer, flags=re.MULTILINE):
        name = match.strip()
        if name:
            names.append(name)

    return names


def _extract_query_tokens(query):
    if not query:
        return []

    stopwords = {
        "the", "and", "for", "with", "from", "this", "that", "these", "those",
        "give", "show", "list", "top", "cheap", "cheapest", "price", "prices",
        "include", "including", "link", "links", "please", "best"
    }
    tokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if t]
    filtered = [t for t in tokens if t not in stopwords and len(t) >= 4]

    if "power" in tokens and "bank" in tokens:
        filtered.append("power-bank")
    if "powerbank" in tokens:
        filtered.append("powerbank")

    return list(dict.fromkeys(filtered))


def _filter_product_links(product_links, answer, user_query, max_links=5):
    if not product_links:
        return []

    unique_links = []
    seen = set()
    for link in product_links:
        if link and link not in seen:
            unique_links.append(link)
            seen.add(link)

    product_names = _extract_product_names_from_answer(answer)
    if product_names:
        slugs = [_slugify(name) for name in product_names]
        matched = []
        for link in unique_links:
            link_lower = link.lower()
            for slug in slugs:
                if slug and slug in link_lower:
                    matched.append(link)
                    break
        if matched:
            return matched[:max_links]

    query_tokens = _extract_query_tokens(user_query)
    if query_tokens:
        matched = [
            link for link in unique_links
            if any(token in link.lower() for token in query_tokens)
        ]
        if matched:
            return matched[:max_links]

    return unique_links[:max_links]


def _wants_links(user_query):
    if not user_query:
        return False
    query = user_query.lower()
    keywords = [
        "link", "links", "url", "website", "buy", "purchase", "order",
        "where to buy", "product link", "product links"
    ]
    return any(k in query for k in keywords)


def _is_store_info_query(user_query):
    if not user_query:
        return False
    query = user_query.lower()
    keywords = [
        "shop name", "store name", "shop", "store", "company name",
        "contact", "address", "phone", "email", "about"
    ]
    return any(k in query for k in keywords)


def _is_product_query(user_query):
    if not user_query:
        return False
    query = user_query.lower()
    keywords = [
        "product", "products", "power bank", "powerbank", "price", "prices",
        "cheapest", "top", "best", "list", "recommend"
    ]
    return any(k in query for k in keywords)


def _remove_link_lines(answer):
    if not answer:
        return answer
    cleaned_lines = []
    for line in str(answer).splitlines():
        if re.search(r"https?://", line):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _extract_shop_name(answer):
    if not answer:
        return answer
    text = str(answer).strip()
    if ":" in text:
        after_colon = text.split(":", 1)[1].strip()
        if after_colon:
            return after_colon.splitlines()[0].strip()
    return text.splitlines()[0].strip()


def _answer_contains_links(answer, links):
    if not answer or not links:
        return False
    return any(link in answer for link in links)


def _extract_product_links_from_db(db, user_query, client_id):
    product_links = []
    try:
        search_results = db.similarity_search_with_score(
            user_query,
            k=10,
            filter={'client_id': client_id}
        )

        seen_urls = set()
        for doc, score in search_results:
            if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                product_links_str = doc.metadata.get("product_links", "")
                if product_links_str:
                    for url in product_links_str.split("|"):
                        url = url.strip()
                        if url and url not in seen_urls:
                            product_links.append(url)
                            seen_urls.add(url)

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ChromaDB search returned {len(search_results)} results")
        logger.info(f"Extracted {len(product_links)} product URLs from metadata")
        if search_results:
            logger.info(
                f"First result metadata: {search_results[0][0].metadata if hasattr(search_results[0][0], 'metadata') else 'No metadata'}"
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error extracting product URLs: {str(e)}")
        product_links = []

    return product_links


def get_chatbot_response(user_query, client_id):
    """
    Get response from chatbot using the configured API provider.
    Returns both the answer and any product links found in the retrieved context.
    
    API provider is set by CHAT_API_PROVIDER constant at the top of this file.
    To switch APIs, edit CHAT_API_PROVIDER = "google" or "openrouter"
    
    Returns:
        tuple: (answer, product_links) where:
            - answer: str - The AI-generated response
            - product_links: list - URLs to product pages found in the context
    """
    # Get LLM based on configured provider
    if CHAT_API_PROVIDER == "openrouter":
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("❌ OPENROUTER_API_KEY not configured for chat")
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="openrouter/auto",
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        # Default to Google
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",convert_system_message_to_human=True)
    
    # Using gemini-embedding-001 - the standard embedding model for Google Generative AI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Use client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    db = Chroma(persist_directory=client_db_path, embedding_function=embeddings, collection_name=client_id)
    
    # Setup the retriever with your multi-tenant filter
    retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})

    wants_links = _wants_links(user_query)
    is_store_info = _is_store_info_query(user_query)
    is_product_query = _is_product_query(user_query)

    raw_product_links = _extract_product_links_from_db(db, user_query, client_id)
    available_links = _filter_product_links(raw_product_links, "", user_query, max_links=5)
    links_block = "None"
    if available_links and wants_links and is_product_query:
        links_block = "\n".join([f"{idx + 1}. {url}" for idx, url in enumerate(available_links)])

    if is_store_info:
        system_prompt = (
            "You are a helpful assistant. Answer only the shop name with no extra text. "
            "Do not list products or links.\n\n"
            "{context}"
        )
    elif is_product_query:
        system_prompt = (
            "You are a helpful assistant. Use the following pieces of retrieved "
            "context to answer the question. If you don't know the answer, say that "
            "you don't know. Do not claim you cannot provide links. If product links "
            "are provided, use them.\n\n"
            "Format the response exactly like this for each item:\n"
            "1. **Product name**\n"
            "Description: ...\n"
            "Price: Rs X,XXX\n"
            "Link: https://example.com\n\n"
            "If links are not provided, omit the Link line.\n\n"
            "Available product links:\n{product_links}\n\n"
            "{context}"
        )
    else:
        system_prompt = (
            "You are a helpful assistant. Use the following pieces of retrieved "
            "context to answer the question. If you don't know the answer, say that "
            "you don't know. Do not include product lists or links unless the user asks for links.\n\n"
            "{context}"
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Create the modern chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # Invoke the chain
    response = rag_chain.invoke({"input": user_query, "product_links": links_block})
    
    answer = response["answer"]
    filtered_links = _filter_product_links(raw_product_links, answer, user_query, max_links=5)
    if not filtered_links and available_links:
        filtered_links = available_links

    if is_store_info:
        answer = _extract_shop_name(answer)
        return answer, []

    if not wants_links:
        answer = _remove_link_lines(answer)
        return answer, []

    if not is_product_query:
        return answer, []
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Product links extracted: {len(raw_product_links)}")
    logger.info(f"Filtered links: {len(filtered_links)}")
    logger.info(f"Links: {filtered_links}")

    if _answer_contains_links(answer, filtered_links):
        return answer, []

    return answer, filtered_links
