import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .rate import RateLimiter
from .robots import robots_checker
from loguru import logger

def make_client(user_agent: str) -> httpx.Client:
    """Create an HTTP client with proper configuration."""
    # Set user agent for robots.txt checking
    robots_checker.set_user_agent(user_agent)
    
    return httpx.Client(
        headers={"User-Agent": user_agent},
        timeout=httpx.Timeout(30.0, connect=30.0),
        http2=True,
        follow_redirects=True,
    )

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException))
)
def get_with_retry(client: httpx.Client, url: str, rate_limiter: RateLimiter = None) -> httpx.Response:
    """
    Make a GET request with retries and robots.txt compliance.
    
    Args:
        client: HTTP client
        url: URL to fetch
        rate_limiter: Optional rate limiter
        
    Returns:
        HTTP response
    """
    # Check robots.txt compliance
    if not robots_checker.can_fetch(url):
        raise httpx.HTTPStatusError(
            "Robots.txt disallows this request",
            request=httpx.Request("GET", url),
            response=httpx.Response(403)
        )
    
    # Apply rate limiting
    if rate_limiter:
        rate_limiter.wait()
        
        # Check for crawl delay
        crawl_delay = robots_checker.get_crawl_delay(url)
        if crawl_delay > 0:
            logger.debug(f"Respecting crawl delay of {crawl_delay}s")
            import time
            time.sleep(crawl_delay)
    
    logger.debug(f"Making GET request to {url}")
    response = client.get(url)
    response.raise_for_status()
    
    # Reset backoff on successful request
    if rate_limiter:
        rate_limiter.reset_backoff()
    
    return response

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException))
)
def post_with_retry(client: httpx.Client, url: str, json_data: dict = None, params: dict = None, 
                   rate_limiter: RateLimiter = None) -> httpx.Response:
    """
    Make a POST request with retries and robots.txt compliance.
    
    Args:
        client: HTTP client
        url: URL to post to
        json_data: JSON data to send
        params: Query parameters
        rate_limiter: Optional rate limiter
        
    Returns:
        HTTP response
    """
    # Check robots.txt compliance
    if not robots_checker.can_fetch(url):
        raise httpx.HTTPStatusError(
            "Robots.txt disallows this request",
            request=httpx.Request("POST", url),
            response=httpx.Response(403)
        )
    
    # Apply rate limiting
    if rate_limiter:
        rate_limiter.wait()
        
        # Check for crawl delay
        crawl_delay = robots_checker.get_crawl_delay(url)
        if crawl_delay > 0:
            logger.debug(f"Respecting crawl delay of {crawl_delay}s")
            import time
            time.sleep(crawl_delay)
    
    logger.debug(f"Making POST request to {url}")
    response = client.post(url, json=json_data, params=params)
    response.raise_for_status()
    
    # Reset backoff on successful request
    if rate_limiter:
        rate_limiter.reset_backoff()
    
    return response

# Backward compatibility
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=30))
def get(client: httpx.Client, url: str) -> httpx.Response:
    """Legacy function for backward compatibility."""
    return client.get(url)
