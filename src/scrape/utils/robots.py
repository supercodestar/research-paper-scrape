"""
Robots.txt compliance utilities using urllib.robotparser.
"""
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from typing import Optional
from loguru import logger


class RobotsChecker:
    """Check robots.txt compliance for different domains."""
    
    def __init__(self):
        self._parsers = {}  # Cache parsers by domain
        self._user_agent = "ResearchScrapeBot/0.1"
    
    def set_user_agent(self, user_agent: str):
        """Set the user agent for robots.txt checking."""
        self._user_agent = user_agent
        # Clear cache when user agent changes
        self._parsers.clear()
    
    def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool:
        """
        Check if the given URL can be fetched according to robots.txt.
        
        Args:
            url: The URL to check
            user_agent: User agent to use (defaults to instance user agent)
            
        Returns:
            True if the URL can be fetched, False otherwise
        """
        if user_agent is None:
            user_agent = self._user_agent
            
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get or create parser for this domain
            if domain not in self._parsers:
                self._parsers[domain] = self._get_robots_parser(domain)
            
            parser = self._parsers[domain]
            if parser is None:
                # If we can't get robots.txt, assume it's allowed
                logger.debug(f"No robots.txt found for {domain}, allowing access")
                return True
            
            can_fetch = parser.can_fetch(user_agent, url)
            if not can_fetch:
                logger.warning(f"Robots.txt disallows {user_agent} from accessing {url}")
            else:
                logger.debug(f"Robots.txt allows {user_agent} to access {url}")
            
            return can_fetch
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If there's an error, assume it's allowed to avoid blocking legitimate requests
            return True
    
    def _get_robots_parser(self, domain: str) -> Optional[urllib.robotparser.RobotFileParser]:
        """Get a robots.txt parser for the given domain."""
        try:
            robots_url = urljoin(domain, "/robots.txt")
            logger.debug(f"Fetching robots.txt from {robots_url}")
            
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            parser.read()
            
            return parser
            
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {domain}: {e}")
            return None
    
    def get_crawl_delay(self, url: str, user_agent: Optional[str] = None) -> float:
        """
        Get the crawl delay for the given URL according to robots.txt.
        
        Args:
            url: The URL to check
            user_agent: User agent to use (defaults to instance user agent)
            
        Returns:
            Crawl delay in seconds, or 0 if not specified
        """
        if user_agent is None:
            user_agent = self._user_agent
            
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if domain not in self._parsers:
                self._parsers[domain] = self._get_robots_parser(domain)
            
            parser = self._parsers[domain]
            if parser is None:
                return 0.0
            
            # Get crawl delay for this user agent
            delay = parser.crawl_delay(user_agent)
            if delay is not None:
                logger.debug(f"Crawl delay for {user_agent} on {domain}: {delay}s")
                return float(delay)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error getting crawl delay for {url}: {e}")
            return 0.0


# Global instance
robots_checker = RobotsChecker()
