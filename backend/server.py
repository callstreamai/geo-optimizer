"""
CallStreamAI - LLM SEO / GEO Optimizer API Server v2
"""
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from analyzers.crawler import SiteCrawler
from analyzers.entity_analyzer import EntityAnalyzer
from analyzers.faq_analyzer import FAQAnalyzer
from analyzers.schema_analyzer import SchemaAnalyzer
from analyzers.content_analyzer import ContentAnalyzer
from analyzers.link_analyzer import LinkAnalyzer
from analyzers.remaining_analyzers import (
    ScenarioAnalyzer, StructureAnalyzer, TechnicalAnalyzer,
    TrustAnalyzer, GEOAnalyzer
)
from analyzers.scoring_engine import ScoringEngine

app = FastAPI(title="CallStreamAI LLM SEO Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


class AnalyzeRequest(BaseModel):
    url: str
    email: str = ""


@app.get("/")
async def serve_frontend():
    return FileResponse(str(frontend_path / "index.html"))


@app.post("/api/analyze")
async def analyze_url(request: AnalyzeRequest):
    url = request.url.strip()
    
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        # Crawl
        crawler = SiteCrawler(url, timeout=30)
        crawl_data = await crawler.crawl()
        
        if not crawl_data.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Could not access {url}: {crawl_data.get('error', 'Unknown error')}. Make sure the URL is correct and the site is accessible."
            )
        
        # Run all analyzers
        analyzers = [
            EntityAnalyzer(),
            FAQAnalyzer(),
            SchemaAnalyzer(),
            ContentAnalyzer(),
            LinkAnalyzer(),
            ScenarioAnalyzer(),
            StructureAnalyzer(),
            TechnicalAnalyzer(),
            TrustAnalyzer(),
            GEOAnalyzer(),
        ]
        
        results = []
        for analyzer in analyzers:
            try:
                result = analyzer.analyze(crawl_data)
                results.append(result)
            except Exception as e:
                results.append({
                    "name": getattr(analyzer, '__class__', type(analyzer)).__name__.replace("Analyzer", ""),
                    "icon": "⚠️",
                    "score": 0,
                    "weight": 0,
                    "error": str(e),
                    "findings": [f"Analysis error: {str(e)}"],
                    "recommendations": []
                })
        
        # Calculate overall score
        engine = ScoringEngine()
        final_score = engine.calculate(results)
        
        return {
            "success": True,
            "url": url,
            "overall_score": final_score["overall_score"],
            "overall_grade": final_score["overall_grade"],
            "summary": final_score["summary"],
            "categories": final_score["category_scores"],
            "priority_fixes": final_score["priority_fixes"],
            "score_breakdown": final_score["score_breakdown"],
            "all_recommendations": final_score["all_recommendations"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
