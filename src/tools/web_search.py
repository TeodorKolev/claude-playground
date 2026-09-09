def web_search(query: str) -> dict:
    return {
        "query": query,
        "results": [
            {
                "title": "Mock Result 1",
                "url": "https://example.com/1",
                "snippet": f"Mock search result for: {query}",
            },
            {
                "title": "Mock Result 2",
                "url": "https://example.com/2",
                "snippet": f"Another mock result for: {query}",
            },
        ],
    }
