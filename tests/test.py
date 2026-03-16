import requests
import time
from src.utils import simplify_semantic_scholar_results

def search_semantic_scholar(query: str, limit: int = 3, max_retries: int = 5, year: int = None):
    # Construir a URL base
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    # Parâmetros da query
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,url,externalIds,citationStyles"
    }

    # Adicionar filtro de ano se fornecido
    if year:
        params["year"] = year

    headers = {
        "User-Agent": "AcademicMultiAgent/1.0",
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 429:
                wait = 2 ** attempt
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json().get("data", [])
            answer = {"status": "success", "papers": data}

            if limit>=3:
                answer = simplify_semantic_scholar_results(answer)

            return answer
        except requests.Timeout:
            return {"status": "timeout", "papers": []}

        except requests.HTTPError as e:
            return {
                "status": "error",
                "message": str(e),
                "papers": []
            }

    return {
        "status": "error",
        "message": "Rate limit exceeded after retries",
        "papers": []
    }

print(search_semantic_scholar(query="LLMs software testing"))
