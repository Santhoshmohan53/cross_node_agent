"""
DEEP RESEARX // Autonomous Research & Annotation Hub
FastAPI Backend serving Dual-Pane Web Canvas, Real-Time Web Scraping, and Local Ollama Inference.
"""

import os
import sys
import json
import time
import re
import asyncio
import logging
import base64
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Include project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)

from src.research_pipeline.deep_research_pipe import (
    DeepResearchPipeline,
    ParallelScraperAgent,
    PlannerAgent,
    SynthesizerAgent,
    OllamaClient,
    ResearchPlan,
    ResearchSource
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResearchHub")

app = FastAPI(title="Deep ResearX Hub", version="2.0.0")

WEB_UI_DIR = os.path.join(ROOT_DIR, "web_ui")
ollama_client = OllamaClient(base_url="http://127.0.0.1:11434")


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "installed_models": ollama_client.get_installed_models()
    }


def extract_search_keywords(topic: str) -> List[str]:
    """Deterministically extracts clean keyword queries from any short or paragraph-long prompt."""
    noise_patterns = [
        r"find me (the|a)?", r"what i want is", r"are we clear on this", r"curate(r)? your results",
        r"main focus to be on", r"for all of the above mentioned objectives", r"segregate them as below",
        r"can you (please)?", r"tell me about", r"i want to know"
    ]
    cleaned = topic
    for pat in noise_patterns:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)
    
    words = [w for w in re.findall(r"\b[A-Za-z0-9\+\-\.]+\b", cleaned) if len(w) > 1]
    stop_words = {
        "the", "and", "or", "of", "in", "on", "for", "with", "to", "at", "by", "from", "as",
        "is", "that", "are", "this", "them", "they", "it", "be", "an", "we", "you", "me", "my",
        "all", "below", "up", "above", "daily", "activity", "limited"
    }
    key_terms = [w for w in words if w.lower() not in stop_words]
    
    if len(key_terms) <= 6:
        base = " ".join(key_terms)
        return [
            f"{base} overview benchmarks",
            f"{base} latest breakthroughs 2025 2026",
            f"{base} performance metrics comparison",
            f"{base} real world user feedback reddit"
        ]
    else:
        chunk1 = " ".join(key_terms[:5])
        chunk2 = " ".join(key_terms[5:10]) if len(key_terms) > 5 else chunk1
        chunk3 = " ".join(key_terms[-5:])
        return [
            f"{chunk1} benchmarks comparison 2025",
            f"{chunk2} hardware requirements forum",
            f"{chunk3} user feedback reddit",
            f"{chunk1} open source models"
        ]


@app.post("/api/deep_research/stream")
async def stream_deep_research(request: Request):
    """
    Streams multi-agent research stages:
    1. Plan
    2. Parallel Scrape (10-15 sources)
    3. Matrix extraction
    4. Real-time token synthesis
    """
    body = await request.json()
    topic = body.get("topic", "").strip()
    requested_model = body.get("model", "deepseek-r1:7b")

    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    async def event_stream():
        # Step 1: Formulate Plan
        yield f"data: {json.dumps({'type': 'status', 'msg': 'Decomposing research query...'})}\n\n"
        
        search_queries = extract_search_keywords(topic)
        sub_questions = [
            f"What are the top-performing architectures, parameter tiers, and specifications for: {search_queries[0]}?",
            f"What are the hardware footprints, VRAM budgets, and quantization levels for: {search_queries[1]}?",
            f"What do real-world practitioner benchmarks and community user feedbacks indicate for: {search_queries[2]}?",
            f"What are the trade-offs, uncensored availability, and multimodal capabilities for: {search_queries[3]}?"
        ]
        plan = ResearchPlan(
            topic=topic,
            sub_questions=sub_questions,
            search_queries=search_queries,
            focus_areas=["Architecture & SOTA", "Hardware Limits", "User Feedback", "Trade-offs"]
        )

        yield f"data: {json.dumps({'type': 'plan', 'sub_questions': plan.sub_questions, 'queries': plan.search_queries})}\n\n"

        # Step 2: Parallel Web Scraping
        scraper = ParallelScraperAgent(max_sources_per_query=4, max_tokens_per_source=2500)
        yield f"data: {json.dumps({'type': 'status', 'msg': 'Scraping live web sources in parallel...'})}\n\n"

        # Execute concurrent scraping in threadpool
        loop = asyncio.get_event_loop()
        sources = await loop.run_in_executor(None, scraper.execute_research_gathering, plan.search_queries)

        domains = list(set(s.domain for s in sources if s.domain))[:8]
        yield f"data: {json.dumps({'type': 'scraping', 'sources_count': len(sources), 'domains': domains})}\n\n"

        # Step 3: Stream Instant Evidence Matrix & Source Table
        yield f"data: {json.dumps({'type': 'matrix', 'metric_count': len(sources)})}\n\n"
        await asyncio.sleep(0.01)

        # Construct Instant Header and Scraped Sources Table
        instant_header = (
            f"# Research Dossier: {topic}\n\n"
            f"> 🌐 **Autonomous Multi-Agent Telemetry**: Gathered **{len(sources)}** live web articles across `{', '.join(domains[:6])}` in parallel.\n\n"
            "## 🔗 Verified Scraped Sources & Real-World Intelligence\n\n"
            "| # | Source Title | Domain / Publication | Live Verified URL |\n"
            "| :--- | :--- | :--- | :--- |\n"
        )
        for i, src in enumerate(sources, 1):
            clean_title = (src.title or "Web Source").replace("|", "-").strip()
            instant_header += f"| **[{i}]** | {clean_title} | `{src.domain}` | [{src.url}]({src.url}) |\n"

        instant_header += "\n---\n\n## 📊 Live Scraped Performance & Corporate Intelligence Highlights\n\n"
        
        # Extract high-value factual quotes from scraped sources
        for i, src in enumerate(sources[:5], 1):
            if src.content:
                # Find sentences with metrics or companies
                sentences = [s.strip() for s in src.content.split("\n") if len(s.strip()) > 40][:2]
                if sentences:
                    instant_header += f"- **[{i}] {src.domain}**: " + " ".join(sentences) + "\n"

        instant_header += "\n---\n\n## 🔬 In-Depth Analytical Synthesis & Strategic Breakdown\n\n"

        # Stream the instant table and highlights to UI immediately (0ms wait!)
        yield f"data: {json.dumps({'type': 'token', 'token': instant_header})}\n\n"
        await asyncio.sleep(0.01)

        # Step 4: Live Synthesis
        yield f"data: {json.dumps({'type': 'synthesis_start'})}\n\n"
        await asyncio.sleep(0.01)

        evidence_blocks = []
        for i, src in enumerate(sources[:6], 1):
            excerpt = (src.content[:400] if src.content else src.snippet[:250]).strip()
            evidence_blocks.append(f"[{i}] {src.title} ({src.domain}): {excerpt}")
        evidence_text = "\n".join(evidence_blocks) if evidence_blocks else "No live articles retrieved."

        active_synthesis_model = ollama_client.resolve_model(requested_model, ["deepseek-r1:7b", "llava:7b"])

        system_prompt = (
            "You are a Lead Technology Research Analyst. Based on the provided real web sources, "
            "write an analytical breakdown in Markdown. "
            "REQUIRED SECTIONS:\n"
            "1. ### Executive Summary & Key Milestones\n"
            "2. ### Quantitative Performance Matrix (Table with Wh/kg, Wh/L, Cycle Life, Charging Speed, and Cost $/kWh)\n"
            "3. ### Corporate Prototypes & Commercial Roadmaps (Toyota, QuantumScape, CATL, Factorial, Samsung SDI)\n"
            "4. ### Critical Technical Bottlenecks & Physics Hurdles\n"
            "Cite all claims with [1], [2] referencing the verified sources above."
        )

        prompt = (
            f"# RESEARCH TOPIC: {topic}\n\n"
            f"## LIVE EVIDENCE:\n{evidence_text}\n\n"
            "Synthesize the analytical sections now starting directly with ### Executive Summary."
        )

        gen_url = f"{ollama_client.base_url}/api/generate"
        gen_payload = {
            "model": active_synthesis_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "num_ctx": 2048,
                "num_thread": 6
            }
        }

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", gen_url, json=gen_payload) as stream_resp:
                    async for line in stream_resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'token', 'token': f'\\n\\n[Synthesis Notice: {str(e)}]'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/chat/stream")
async def stream_chat(request: Request):
    """
    Direct model Q&A endpoint supporting text + multimodal images.
    """
    body = await request.json()
    message = body.get("message", "")
    requested_model = body.get("model", "deepseek-r1:7b")
    image_base64 = body.get("image", None)

    active_model = ollama_client.resolve_model(requested_model, ["deepseek-r1:7b", "llava:7b", "qwen2.5:7b"])
    
    # If image attached, use multimodal model
    if image_base64:
        active_model = ollama_client.resolve_model("llava:7b", ["llava:7b", "qwen2.5-vl:7b"])

    async def chat_stream():
        url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": active_model,
            "prompt": message,
            "stream": True,
            "options": {
                "temperature": 0.4,
                "num_ctx": 4096,
                "num_thread": 6
            }
        }
        if image_base64 and "," in image_base64:
            clean_b64 = image_base64.split(",")[1]
            payload["images"] = [clean_b64]

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, json=payload) as stream_resp:
                    async for line in stream_resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return StreamingResponse(chat_stream(), media_type="text/plain")


# Static Files Mount
if os.path.exists(WEB_UI_DIR):
    app.mount("/static", StaticFiles(directory=WEB_UI_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(WEB_UI_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "UI files not found."}

@app.get("/style.css")
def serve_css():
    css_file = os.path.join(WEB_UI_DIR, "style.css")
    return FileResponse(css_file)

@app.get("/app.js")
def serve_js():
    js_file = os.path.join(WEB_UI_DIR, "app.js")
    return FileResponse(js_file)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    port = int(os.getenv("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  [*] DEEP RESEARX HUB RUNNING ON http://localhost:{port}")
    print(f"=======================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
