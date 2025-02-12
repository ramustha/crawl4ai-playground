import json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape_web(request: ScrapeRequest):
    try:
        schema = {
            "name": "Questions",
            "baseSelector": "ol.semua > li.nomor",
            "fields": [
                {
                    "name": "question",
                    "selector": "div > p",
                    "type": "text"
                },
                {
                    "name": "options",
                    "selector": "ol.opsinya li",
                    "type": "list",
                    "fields": [
                        {
                            "name": "option",
                            "type": "text"
                        }
                    ]
                },
                {
                    "name": "explanation",
                    "selector": "div.jawaban",
                    "type": "html",
                }
            ]
        }

        browser_cfg = BrowserConfig(
            headless=True,
            light_mode=True,
            verbose=True,
            user_agent_mode="random"
        )

        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(schema, verbose=True),
            scan_full_page=True,
            simulate_user=True,
            magic=True,
        )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(
                url=request.url,
                config=run_cfg
            )

            data = json.loads(result.extracted_content)
        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
