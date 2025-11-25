"""
Search Service for web search using Tavily API.
"""

import httpx
from typing import List, Dict, Any


class SearchError(Exception):
    """Search service error."""
    pass


async def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function for web search using default API key.
    
    Args:
        query: Search query string
        num_results: Number of results to return
        
    Returns:
        List of search results with title, url, content
    """
    from app.core.config import settings
    service = SearchService(api_key=settings.SEARCH_API_KEY)
    return await service.search(query, num_results)


class SearchService:
    """Service for web search using Tavily API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily API.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of search results with title, url, content
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": num_results,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0.0)
                    })
                
                return results
                
        except httpx.HTTPStatusError as e:
            # Graceful fallback on 4xx/5xx (e.g., 403)
            return []
        except Exception as e:
            return []
