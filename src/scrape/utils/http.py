import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from .rate import RateLimiter

def make_client(user_agent: str) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": user_agent},
        timeout=httpx.Timeout(30.0, connect=30.0),
        http2=True,
        follow_redirects=True,
    )

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=30))
def get(client: httpx.Client, url: str) -> httpx.Response:
    return client.get(url)
