import time
import random
import logging
import requests

logger = logging.getLogger(__name__)

def rate_limited_request(method: str, url: str, retries: int = 5, backoff_factor: float = 2.0, **kwargs) -> requests.Response:
    """
    Executes an HTTP request with exponential backoff on connection errors, 
    server errors (5xx), or rate-limiting (429).
    Also includes a small mandatory jitter delay to prevent slamming target servers.
    """
    delay = 1.0
    for attempt in range(retries):
        try:
            # Respectful rate limiting: small sleep between requests to avoid burst overload
            time.sleep(random.uniform(0.2, 0.6))
            
            response = requests.request(method, url, **kwargs)
            
            if response.status_code == 429:
                # Rate limited by external service
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    sleep_time = int(retry_after)
                else:
                    sleep_time = delay * (backoff_factor ** attempt) + random.uniform(0.1, 1.0)
                logger.warning(f"Rate limit (429) hit for URL: {url}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
                
            if response.status_code >= 500:
                sleep_time = delay * (backoff_factor ** attempt) + random.uniform(0.1, 1.0)
                logger.warning(f"Server error ({response.status_code}) for URL: {url}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
                
            return response
            
        except (requests.exceptions.RequestException, Exception) as e:
            sleep_time = delay * (backoff_factor ** attempt) + random.uniform(0.1, 1.0)
            logger.warning(f"Request exception '{e}' for URL: {url}. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt+1}/{retries})")
            if attempt == retries - 1:
                raise e
            time.sleep(sleep_time)
            
    raise requests.exceptions.RequestException(f"Failed to fetch {url} after {retries} retries due to rate limiting or server issues.")
