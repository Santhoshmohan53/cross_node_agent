"""
OpenAI-Compatible Microservice for Autonomous Deep Research.
Exposes standard /v1/models and /v1/chat/completions endpoints.
Allows Open WebUI to connect directly to the Multi-Agent Research Loop as a native model.
"""

import os
import sys
import time
import json
import re
import base64
import logging
import requests
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

# Include current directory in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.research_pipeline.deep_research_pipe import DeepResearchPipeline

app = FastAPI(title="Autonomous Deep Research Agent Server", version="1.0.0")
logger = logging.getLogger("ResearchServer")

pipeline = DeepResearchPipeline(
    ollama_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    planner_model=os.getenv("PLANNER_MODEL", "deepseek-r1:7b"),
    synthesis_model=os.getenv("SYNTHESIS_MODEL", "qwen2.5-vl:7b")
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "deep_research_agent"}


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "autonomous-deep-research",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-agent",
                "permission": [],
                "root": "autonomous-deep-research",
                "parent": None
            }
        ]
    }


def resolve_image_to_base64(img_ref: str) -> Optional[str]:
    """Resolves an image URL, relative URL, base64 string, or disk path to clean base64."""
    if not img_ref:
        return None
    # 1. If it's already a base64 data URL
    if "base64," in img_ref:
        return img_ref.split("base64,")[1].strip()

    # 2. Check if it's an Open WebUI file UUID or upload path
    uuid_match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", str(img_ref), re.IGNORECASE)
    if uuid_match:
        file_uuid = uuid_match.group(1)
        upload_dir = r"C:\Users\user\AppData\Local\Programs\Python\Python312\Lib\site-packages\open_webui\data\uploads"
        if os.path.exists(upload_dir):
            for fname in os.listdir(upload_dir):
                if file_uuid in fname:
                    full_path = os.path.join(upload_dir, fname)
                    try:
                        with open(full_path, "rb") as f:
                            return base64.b64encode(f.read()).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Error reading image file {full_path}: {e}")

    # 3. If it's a relative URL to Open WebUI
    if str(img_ref).startswith("/"):
        try:
            full_url = f"http://127.0.0.1:3000{img_ref}"
            resp = requests.get(full_url, timeout=5)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode("utf-8")
        except Exception:
            pass

    # 4. If it's an HTTP URL
    if str(img_ref).startswith("http://") or str(img_ref).startswith("https://"):
        try:
            resp = requests.get(img_ref, timeout=5)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode("utf-8")
        except Exception:
            pass

    # 5. Raw base64 string
    if len(str(img_ref)) > 100 and not str(img_ref).startswith("http") and "/" not in str(img_ref)[:20]:
        return str(img_ref).strip()

    return None


def clean_user_query(raw_query: str) -> str:
    """Strips file metadata, JSON artifacts, and UUIDs from query so search engines don't scrape noise."""
    clean = re.sub(r"\{[^{}]*?(?:file|image)[^{}]*?\}", " ", raw_query, flags=re.IGNORECASE)
    clean = re.sub(r"/api/v1/files/\S+", " ", clean)
    clean = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bimage\.(?:png|jpg|jpeg|webp)\b", " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(file\s+type|file\s+id|url)\b", " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean if len(clean) > 5 else raw_query


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    stream = body.get("stream", True)
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages array cannot be empty.")

    latest_msg = messages[-1].get("content", "")
    attached_images = []

    # Check top-level files array in body or message
    for f in body.get("files", []) + messages[-1].get("files", []):
        if isinstance(f, dict):
            url = f.get("url") or f.get("id") or ""
            if url:
                attached_images.append(url)

    if isinstance(latest_msg, list):
        # Handle multimodal payload if array of text/image
        text_parts = []
        for p in latest_msg:
            if isinstance(p, dict):
                if p.get("type") == "text":
                    text_parts.append(p.get("text", ""))
                elif p.get("type") == "image_url":
                    url = p.get("image_url", {}).get("url", "")
                    if url:
                        attached_images.append(url)
        raw_user_query = " ".join(text_parts) if text_parts else "Deep Research"
    else:
        raw_user_query = str(latest_msg)

    # Check if image UUIDs are in the query string itself
    uuid_matches = re.findall(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", raw_user_query, re.IGNORECASE)
    for u in uuid_matches:
        if u not in attached_images:
            attached_images.append(u)

    user_query = clean_user_query(raw_user_query)
    created_time = int(time.time())

    def sse_chunk(text: str) -> str:
        payload = {
            "id": f"chatcmpl-research-{created_time}",
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": "autonomous-deep-research",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": text},
                    "finish_reason": None
                }
            ]
        }
        return f"data: {json.dumps(payload)}\n\n"

    def sse_finish() -> str:
        payload = {
            "id": f"chatcmpl-research-{created_time}",
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": "autonomous-deep-research",
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        return f"data: {json.dumps(payload)}\ndata: [DONE]\n\n"

    # Fast short-circuit for Open WebUI background utility tasks (title, tags, follow-ups)
    is_utility = (
        raw_user_query.strip().startswith("Task:") or
        "Generate concise title" in raw_user_query or
        "Generate 1-3 broad tags" in raw_user_query or
        "Suggest 3-5 relevant follow-up" in raw_user_query
    )
    if is_utility:
        logger.info(f"Handling Open WebUI utility task rapidly: {raw_user_query[:50]}...")
        if "title" in raw_user_query.lower():
            res_text = "Open Source AI Models & 2026 Benchmarks"
        elif "tags" in raw_user_query.lower():
            res_text = "AI Models, Benchmarks, Open Source"
        elif "follow-up" in raw_user_query.lower():
            res_text = "1. Which model matches your GPU VRAM?\n2. Would you like quantization setup steps?\n3. Would you like coding or vision recommendations?"
        else:
            res_text = "Completed."
        
        if stream:
            def util_stream():
                yield sse_chunk(res_text)
                yield sse_finish()
            return StreamingResponse(util_stream(), media_type="text/event-stream")
        else:
            return {
                "id": f"chatcmpl-util-{created_time}",
                "object": "chat.completion",
                "created": created_time,
                "model": "autonomous-deep-research",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": res_text}, "finish_reason": "stop"}]
            }

    def stream_generator():
        try:
            yield sse_chunk("🔍 **[Autonomous Multimodal Deep Research Agent Initialized]**\n\n")

            # Phase 0: Multimodal Vision Extraction if image/table is attached
            visual_context = ""
            if attached_images:
                yield sse_chunk("> 📸 **Phase 0: Multimodal Vision Ingestion (llava:7b)**\n")
                for idx, img_ref in enumerate(attached_images, 1):
                    clean_b64 = resolve_image_to_base64(img_ref)
                    if clean_b64:
                        vis_analysis = pipeline.vision.analyze_image(
                            clean_b64,
                            prompt="Extract and summarize all visible table columns, headers, metrics, benchmarks, and model names from this image to guide research:"
                        )
                        if vis_analysis:
                            visual_context += f"\n\n[ATTACHED VISUAL REFERENCE #{idx} EXTRACTED CONTEXT]:\n{vis_analysis}\n"
                            yield sse_chunk(f"> • Extracted visual table structure from Image #{idx}.\n")
                yield sse_chunk("\n")

            effective_query = f"{user_query}\n\n{visual_context}" if visual_context else user_query

            yield sse_chunk("> 🧩 **Phase 1: Research Planning & Decomposition**\n")
            
            # 1. Planner Step
            plan = pipeline.planner.formulate_plan(effective_query)
            for q in plan.sub_questions:
                yield sse_chunk(f"> • *{q}*\n")
            
            yield sse_chunk("\n> 🌐 **Phase 2: Executing Parallel Web Scraping...**\n")
            
            # 2. Scraper Step
            sources = pipeline.scraper.execute_research_gathering(plan.search_queries)
            domains = list(set(s.domain for s in sources if s.domain))
            domains_str = ", ".join(domains[:6]) if domains else "general web"
            yield sse_chunk(f"> 📚 Retrieved **{len(sources)}** cited sources across: `{domains_str}`\n\n")

            # Stream the Verified Sources Table immediately into Open WebUI
            table_md = (
                "## 🔗 Verified Scraped Sources & Live Intelligence\n\n"
                "| # | Source Title | Domain / Publication | Live Verified URL |\n"
                "| :--- | :--- | :--- | :--- |\n"
            )
            for i, src in enumerate(sources, 1):
                clean_title = (src.title or "Web Source").replace("|", "-").strip()
                table_md += f"| **[{i}]** | {clean_title} | `{src.domain}` | [{src.url}]({src.url}) |\n"

            table_md += "\n---\n\n## 📊 Live Scraped Highlights & Community Signals\n\n"
            for i, src in enumerate(sources[:5], 1):
                if src.content:
                    sentences = [s.strip() for s in src.content.split("\n") if len(s.strip()) > 40][:2]
                    if sentences:
                        table_md += f"- **[{i}] {src.domain}**: " + " ".join(sentences) + "\n"

            table_md += "\n---\n\n## 🔬 In-Depth Analytical Synthesis & Strategic Breakdown\n\n"
            yield sse_chunk(table_md)

            # 3. Synthesizer Step
            for token in pipeline.synthesizer.compile_report_stream(effective_query, plan, sources):
                yield sse_chunk(token)
            yield sse_finish()
        finally:
            logger.info("Research processing completed. Offloading models from system memory...")
            pipeline.offload_models()

    if stream:
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Non-streaming fallback
        try:
            visual_context = ""
            if attached_images:
                for idx, img in enumerate(attached_images, 1):
                    clean_b64 = resolve_image_to_base64(img)
                    if clean_b64:
                        vis_analysis = pipeline.vision.analyze_image(
                            clean_b64,
                            prompt=f"Extract table columns, headers, and structure from this image preview for:\n{user_query}"
                        )
                        if vis_analysis:
                            visual_context += f"\n\n[ATTACHED VISUAL REFERENCE #{idx} EXTRACTED CONTEXT]:\n{vis_analysis}\n"
            
            effective_query = f"{user_query}\n\n{visual_context}" if visual_context else user_query
            plan = pipeline.planner.formulate_plan(effective_query)
            sources = pipeline.scraper.execute_research_gathering(plan.search_queries)
            report = pipeline.synthesizer.compile_report(effective_query, plan, sources)
            return {
                "id": f"chatcmpl-research-{created_time}",
                "object": "chat.completion",
                "created": created_time,
                "model": "autonomous-deep-research",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": report
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
        finally:
            logger.info("Research processing completed. Offloading models from system memory...")
            pipeline.offload_models()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="127.0.0.1", port=port)
