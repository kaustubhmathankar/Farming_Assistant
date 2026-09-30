import json
from datetime import date

import requests
from langchain_core.tools import tool

from app.config import settings
from app.services.rag_service import format_documents, retrieve


RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"


def _json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


@tool
def search_agricultural_knowledge(query: str) -> str:
    """Search the curated agricultural knowledge base for stable farming guidance."""
    docs = retrieve(query)
    context, sources = format_documents(docs)
    return _json({"data": context[:14000], "sources": sources})


@tool
def get_weather(location: str) -> str:
    """Get current weather and short forecast for a village, district, or city."""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1, "language": "en", "format": "json"},
        timeout=settings.request_timeout_seconds,
    )
    geo.raise_for_status()
    results = geo.json().get("results") or []
    if not results:
        return _json({"data": "Location not found", "sources": []})
    place = results[0]
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": place["latitude"], "longitude": place["longitude"], "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m", "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max", "timezone": "auto"},
        timeout=settings.request_timeout_seconds,
    )
    weather.raise_for_status()
    data = weather.json()
    return _json({
        "data": {"location": place.get("name"), "current": data.get("current"), "daily": data.get("daily")},
        "sources": [{"title": "Open-Meteo", "source": "Open-Meteo", "url": "https://open-meteo.com/", "type": "weather"}],
    })


@tool
def get_market_prices(state: str, commodity: str, district: str = "") -> str:
    """Get current mandi prices using the official Government OGD mandi resource."""
    params = {"api-key": settings.data_gov_api_key, "format": "json", "limit": 20, "filters[state.keyword]": state, "filters[commodity.keyword]": commodity}
    if district:
        params["filters[district.keyword]"] = district
    response = requests.get(f"https://api.data.gov.in/resource/{RESOURCE_ID}", params=params, timeout=settings.request_timeout_seconds)
    response.raise_for_status()
    return _json({"data": response.json().get("records", []), "sources": [{"title": "Government OGD Mandi Data", "source": "data.gov.in", "url": "https://www.data.gov.in/", "type": "market"}]})


@tool
def search_government_schemes(query: str) -> str:
    """Search official Indian government scheme pages for farmer schemes and eligibility."""
    if not settings.tavily_api_key:
        return _json({"data": "Government search is not configured", "sources": []})
    from tavily import TavilyClient
    client = TavilyClient(api_key=settings.tavily_api_key)
    result = client.search(query=query, include_domains=["myscheme.gov.in", "india.gov.in"], max_results=5)
    sources = [{"title": item.get("title", "Government scheme"), "source": item.get("url", ""), "url": item.get("url"), "type": "government"} for item in result.get("results", [])]
    return _json({"data": result.get("results", []), "sources": sources})


@tool
def web_search(query: str) -> str:
    """Search the public web for current agriculture information not covered by dedicated tools."""
    if not settings.tavily_api_key:
        return _json({"data": "Web search is not configured", "sources": []})
    from tavily import TavilyClient
    result = TavilyClient(api_key=settings.tavily_api_key).search(query=query, max_results=5)
    sources = [{"title": item.get("title", "Web source"), "source": item.get("url", ""), "url": item.get("url"), "type": "web"} for item in result.get("results", [])]
    return _json({"data": result.get("results", []), "sources": sources})


TOOLS = [search_agricultural_knowledge, get_weather, get_market_prices, search_government_schemes, web_search]
