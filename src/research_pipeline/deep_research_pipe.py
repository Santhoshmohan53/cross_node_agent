"""
Autonomous Multi-Agent Deep Research Pipeline
Compatible with Open WebUI Pipes and Standalone Local Execution.

Features:
1. Planner Agent: Decomposes complex topics into targeted sub-questions.
2. Parallel Scraper Agent: Executes concurrent web search & full text scraping (DuckDuckGo + Trafilatura).
3. Synthesizer Agent: Compiles structured, cited research dossiers with bibliography.
"""

import os
import re
import json
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
from dataclasses import dataclass, field
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepResearchPipe")


@dataclass
class ResearchSource:
    url: str
    title: str
    snippet: str
    content: str = ""
    domain: str = ""

    def __post_init__(self):
        try:
            parsed = urllib.parse.urlparse(self.url)
            self.domain = parsed.netloc.replace("www.", "")
        except Exception:
            self.domain = "web"


@dataclass
class ResearchPlan:
    topic: str
    sub_questions: List[str]
    search_queries: List[str]
    focus_areas: List[str]


class OllamaClient:
    """Lightweight direct HTTP client for local Ollama instance."""
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")

    def get_installed_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []

    def resolve_model(self, preferred: str, fallbacks: List[str]) -> str:
        installed = self.get_installed_models()
        if not installed:
            return preferred
        for cand in [preferred] + fallbacks:
            for inst in installed:
                if cand == inst or cand in inst or inst in cand:
                    return inst
        return installed[0]

    def unload_model(self, model: str) -> bool:
        """Explicitly offloads a model from system memory (RAM/VRAM) via keep_alive: 0."""
        url = f"{self.base_url}/api/generate"
        try:
            resp = requests.post(url, json={"model": model, "keep_alive": 0}, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Successfully offloaded '{model}' from system memory.")
                return True
        except Exception as e:
            logger.warning(f"Failed to offload '{model}' from system memory: {e}")
        return False

    def generate(self, model: str, prompt: str, system: Optional[str] = None, stream: bool = False) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 8192
            }
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(url, json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error communicating with local model ({model}): {str(e)}"

    def generate_stream(self, model: str, prompt: str, system: Optional[str] = None) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "num_ctx": 8192
            }
        }
        if system:
            payload["system"] = system

        try:
            with requests.post(url, json=payload, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        token = data.get("response", "")
                        if token:
                            yield token
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"\n\n[Error communicating with model {model}: {str(e)}]"

    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 8192
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"Error communicating with local model ({model}): {str(e)}"


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


class VisionAgent:
    """Multimodal Vision Agent that analyzes images, tables, diagrams, and OCR text."""
    def __init__(self, client: OllamaClient, vision_model: str = "llava:7b"):
        self.client = client
        self.model = vision_model

    def analyze_image(self, base64_image: str, prompt: str = "Extract all text, table columns, rows, data points, and visual structure from this image:") -> str:
        url = f"{self.client.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [base64_image],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 350,
                "num_ctx": 2048
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            logger.warning(f"Vision analysis warning: {e}")
        return ""


class PlannerAgent:
    """Agent responsible for breaking down a research topic into sub-queries."""
    def __init__(self, client: OllamaClient, planner_model: str = "deepseek-r1:7b"):
        self.client = client
        self.model = planner_model

    def parse_llm_plan(self, raw: str, topic: str) -> Optional[ResearchPlan]:
        try:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if not json_match:
                json_match = re.search(r"(\{.*\})", raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                sub_q = data.get("sub_questions", [])
                queries = data.get("search_queries", [])
                if sub_q and queries:
                    return ResearchPlan(
                        topic=topic,
                        sub_questions=sub_q,
                        search_queries=queries,
                        focus_areas=data.get("focus_areas", ["Overview", "Analysis"])
                    )
        except Exception as e:
            logger.warning(f"Failed to parse LLM plan: {e}")
        return None

    def formulate_plan(self, topic: str, use_llm: bool = False) -> ResearchPlan:
        if use_llm and self.client:
            try:
                raw = self.client.generate(self.model, f"Decompose topic into JSON: {topic}")
                parsed = self.parse_llm_plan(raw, topic)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"LLM plan generation failed, falling back to deterministic: {e}")

        # Deterministic instant zero-token keyword decomposition (Rule 02 Governance)
        search_queries = extract_search_keywords(topic)
        sub_questions = [
            f"What are the baseline specifications, architectures, and state-of-the-art for {search_queries[0]}?",
            f"What are the latest 2025/2026 breakthroughs, benchmarks, and community findings for {search_queries[1]}?",
            f"What are the quantitative performance metrics, hardware footprints, and user reviews for {search_queries[2]}?",
            f"What are the critical real-world limitations, bottlenecks, and open-source availability for {search_queries[3]}?"
        ]
        return ResearchPlan(
            topic=topic,
            sub_questions=sub_questions,
            search_queries=search_queries,
            focus_areas=["SOTA & Architecture", "Hardware & Footprint", "Community Feedback", "Trade-offs"]
        )


class ParallelScraperAgent:
    """Agent responsible for parallel web search and text extraction without API keys."""
    def __init__(self, max_sources_per_query: int = 3, max_tokens_per_source: int = 2000):
        self.max_sources = max_sources_per_query
        self.max_tokens = max_tokens_per_source

    def search_query(self, query: str) -> List[ResearchSource]:
        sources = []
        if DDGS is not None:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=self.max_sources))
                    for r in results:
                        url = r.get("href") or r.get("url")
                        title = r.get("title", "")
                        snippet = r.get("body", "")
                        if url:
                            sources.append(ResearchSource(url=url, title=title, snippet=snippet))
            except Exception as e:
                logger.warning(f"DuckDuckGo search error for '{query}': {e}")
        
        # Fallback if DDGS fails or is unavailable
        if not sources:
            try:
                encoded = urllib.parse.quote(query)
                req = urllib.request.Request(
                    f"https://html.duckduckgo.com/html/?q={encoded}",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read().decode("utf-8", errors="ignore")
                    if BeautifulSoup:
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.find_all("a", class_="result__url")[:self.max_sources]:
                            href = a.get("href")
                            if isinstance(href, str) and "uddg=" in href:
                                actual_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                                sources.append(ResearchSource(url=actual_url, title=query, snippet=""))
            except Exception as e:
                logger.error(f"Fallback search error: {e}")

        return sources

    def scrape_url(self, source: ResearchSource) -> ResearchSource:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(source.url, headers=headers, timeout=5)
            if resp.status_code == 200:
                text = ""
                if trafilatura is not None:
                    text = trafilatura.extract(resp.text) or ""
                
                if not text and BeautifulSoup is not None:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for s in soup(["script", "style", "nav", "footer", "header"]):
                        s.extract()
                    text = soup.get_text(separator="\n", strip=True)
                
                if not text:
                    text = resp.text[:2500]

                clean_text = re.sub(r"\n{3,}", "\n\n", text).strip()
                source.content = clean_text[:self.max_tokens * 4]
        except Exception as e:
            logger.debug(f"Failed to scrape {source.url}: {e}")

        return source

    def execute_research_gathering(self, queries: List[str]) -> List[ResearchSource]:
        all_sources: Dict[str, ResearchSource] = {}
        
        # Concurrent multi-query search
        with ThreadPoolExecutor(max_workers=len(queries)) as search_exec:
            search_results = list(search_exec.map(self.search_query, queries))

        for found in search_results:
            for s in found:
                if s.url not in all_sources:
                    all_sources[s.url] = s

        sources_list = list(all_sources.values())[:10]
        # Concurrent page scraping
        with ThreadPoolExecutor(max_workers=10) as scrape_exec:
            scraped = list(scrape_exec.map(self.scrape_url, sources_list))

        return [s for s in scraped if (s.content or s.snippet)]


class SynthesizerAgent:
    """Agent responsible for compiling gathered sources into a comprehensive, cited dossier."""
    def __init__(self, client: OllamaClient, synthesis_model: str = "qwen2.5-vl:7b"):
        self.client = client
        self.model = synthesis_model

    def compile_report(self, topic: str, plan: ResearchPlan, sources: List[ResearchSource]) -> str:
        evidence_blocks = []
        for i, src in enumerate(sources, 1):
            excerpt = src.content[:1500] if src.content else src.snippet
            evidence_blocks.append(f"[{i}] SOURCE: {src.title} ({src.domain})\nURL: {src.url}\nEXCERPT: {excerpt}\n")

        evidence_text = "\n---\n".join(evidence_blocks)

        system_prompt = (
            "You are a Lead AI Research Synthesizer. Your objective is to produce an in-depth, rigorous, "
            "factual, and comprehensive Research Report based strictly on the provided web source evidence. "
            "Requirements:\n"
            "1. Use markdown formatting with clear headings (## Executive Summary, ## Key Findings, ## Technical Analysis, ## Challenges & Trade-offs, ## Conclusion).\n"
            "2. Cite your claims meticulously using bracketed numbers corresponding to the sources (e.g. [1], [2]).\n"
            "3. Include a Markdown comparison table where appropriate.\n"
            "4. Do NOT refuse, lecture, or add conversational filler. Jump straight into the research dossier.\n"
            "5. At the very end, include a ## References & Sources section listing all cited sources with clickable markdown links."
        )

        prompt = (
            f"# RESEARCH TOPIC: {topic}\n\n"
            f"## SUB-QUESTIONS INVESTIGATED:\n" + "\n".join(f"- {q}" for q in plan.sub_questions) + "\n\n"
            f"## SCRAPED EVIDENCE & SOURCE MATERIAL:\n{evidence_text}\n\n"
            "Synthesize the complete, comprehensive research dossier now."
        )

        report = self.client.generate(self.model, prompt, system=system_prompt)
        cleaned_report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
        return cleaned_report

    def compile_report_stream(self, topic: str, plan: ResearchPlan, sources: List[ResearchSource]) -> Generator[str, None, None]:
        evidence_blocks = []
        for i, src in enumerate(sources, 1):
            excerpt = src.content[:1500] if src.content else src.snippet
            evidence_blocks.append(f"[{i}] SOURCE: {src.title} ({src.domain})\nURL: {src.url}\nEXCERPT: {excerpt}\n")

        evidence_text = "\n---\n".join(evidence_blocks)

        system_prompt = (
            "You are a Lead AI Research Synthesizer. Your objective is to produce an in-depth, rigorous, "
            "factual, and comprehensive Research Report based strictly on the provided web source evidence. "
            "Requirements:\n"
            "1. Use markdown formatting with clear headings (## Executive Summary, ## Key Findings, ## Technical Analysis, ## Challenges & Trade-offs, ## Conclusion).\n"
            "2. Cite your claims meticulously using bracketed numbers corresponding to the sources (e.g. [1], [2]).\n"
            "3. Include a Markdown comparison table where appropriate.\n"
            "4. Do NOT refuse, lecture, or add conversational filler. Jump straight into the research dossier.\n"
            "5. At the very end, include a ## References & Sources section listing all cited sources with clickable markdown links."
        )

        prompt = (
            f"# RESEARCH TOPIC: {topic}\n\n"
            f"## SUB-QUESTIONS INVESTIGATED:\n" + "\n".join(f"- {q}" for q in plan.sub_questions) + "\n\n"
            f"## SCRAPED EVIDENCE & SOURCE MATERIAL:\n{evidence_text}\n\n"
            "Synthesize the complete, comprehensive research dossier now."
        )

        for chunk in self.client.generate_stream(self.model, prompt, system=system_prompt):
            yield chunk


class DeepResearchPipeline:
    """Master Orchestrator connecting Planner, Scraper, and Synthesizer."""
    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        planner_model: str = "deepseek-r1:7b",
        synthesis_model: str = "deepseek-r1:7b"
    ):
        self.client = OllamaClient(base_url=ollama_url)
        resolved_planner = self.client.resolve_model(planner_model, ["deepseek-r1:7b", "llava:7b"])
        resolved_synthesis = self.client.resolve_model(synthesis_model, ["deepseek-r1:7b", "llava:7b"])
        resolved_vision = self.client.resolve_model("llava:7b", ["llava:7b", "qwen2.5-vl:7b"])
        logger.info(f"Initialized Pipeline with Vision: {resolved_vision}, Planner: {resolved_planner}, Synthesizer: {resolved_synthesis}")
        self.vision = VisionAgent(self.client, vision_model=resolved_vision)
        self.planner = PlannerAgent(self.client, planner_model=resolved_planner)
        self.scraper = ParallelScraperAgent()
        self.synthesizer = SynthesizerAgent(self.client, synthesis_model=resolved_synthesis)

    def offload_models(self) -> None:
        """Offload all active pipeline models from system memory (RAM/VRAM)."""
        try:
            if hasattr(self, "vision") and getattr(self.vision, "model", None):
                self.client.unload_model(self.vision.model)
            if hasattr(self, "planner") and getattr(self.planner, "model", None):
                self.client.unload_model(self.planner.model)
            if hasattr(self, "synthesizer") and getattr(self.synthesizer, "model", None):
                self.client.unload_model(self.synthesizer.model)
            logger.info("Pipeline models successfully offloaded from system memory.")
        except Exception as e:
            logger.warning(f"Error offloading models: {e}")

    def run_research(self, topic: str, progress_callback=None) -> str:
        try:
            if progress_callback:
                progress_callback("🔍 Formulating research plan and decomposing queries...")
            plan = self.planner.formulate_plan(topic)

            if progress_callback:
                progress_callback(f"🌐 Scraping {len(plan.search_queries)} search angles concurrently...")
            sources = self.scraper.execute_research_gathering(plan.search_queries)

            if progress_callback:
                progress_callback(f"📝 Synthesizing comprehensive cited dossier from {len(sources)} verified sources...")
            report = self.synthesizer.compile_report(topic, plan, sources)

            return report
        finally:
            self.offload_models()


# =========================================================================
# Open WebUI Function / Pipe Adapter
# =========================================================================
class Pipe:
    """Open WebUI Custom Pipe Provider."""
    class Valves:
        def __init__(self):
            self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
            self.PLANNER_MODEL: str = os.getenv("PLANNER_MODEL", "deepseek-r1:7b")
            self.SYNTHESIS_MODEL: str = os.getenv("SYNTHESIS_MODEL", "qwen2.5-vl:7b")

    def __init__(self):
        self.type = "pipe"
        self.id = "deep_research_pipe"
        self.name = "Autonomous Deep Research (Planner + Scraper + Qwen2.5-VL)"
        self.valves = self.Valves()

    def pipe(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
        messages = body.get("messages", [])
        if not messages:
            yield "No prompt received."
            return

        latest_user_msg = messages[-1].get("content", "")
        if not latest_user_msg:
            yield "Empty query."
            return

        yield "🔍 **[Autonomous Deep Research Agent Active]**\n\n"
        yield "> 🧩 **Phase 1**: Decomposing research topic into sub-questions...\n\n"

        pipeline = DeepResearchPipeline(
            ollama_url=self.valves.OLLAMA_BASE_URL,
            planner_model=self.valves.PLANNER_MODEL,
            synthesis_model=self.valves.SYNTHESIS_MODEL
        )

        try:
            plan = pipeline.planner.formulate_plan(latest_user_msg)
            yield f"> 📋 **Research Strategy**:\n"
            for q in plan.sub_questions:
                yield f"> • {q}\n"
            yield "\n> 🌐 **Phase 2**: Scraping web sources in parallel...\n\n"

            sources = pipeline.scraper.execute_research_gathering(plan.search_queries)
            domains = list(set(s.domain for s in sources if s.domain))
            yield f"> 📚 Gathered **{len(sources)}** unique sources across: " + (", ".join(domains[:6]) if domains else "web") + "\n\n"
            yield "> ✍️ **Phase 3**: Synthesizing cited research dossier...\n\n---\n\n"

            report = pipeline.synthesizer.compile_report(latest_user_msg, plan, sources)
            yield report
        finally:
            pipeline.offload_models()


if __name__ == "__main__":
    import sys
    query = "Solid state battery breakthroughs and commercialization timeline"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"Executing Deep Research on: {query}\n")
    pipe = DeepResearchPipeline()
    result = pipe.run_research(query, progress_callback=lambda msg: print(f"[*] {msg}"))
    print("\n" + "="*80 + "\n")
    print(result)
