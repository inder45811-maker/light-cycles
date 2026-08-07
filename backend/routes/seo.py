"""SEO routes — sitemap, robots.txt, and crawler-friendly content."""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(tags=["seo"])

BASE_URL = "https://light-cycleslight-cycles.onrender.com"


@router.get("/sitemap.xml")
async def sitemap():
    """Dynamic sitemap for search engines."""
    pages = [
        ("/", "daily", "1.0"),
        ("/howto", "weekly", "0.8"),
        ("/about", "weekly", "0.9"),
        ("/tournaments", "hourly", "0.7"),
        ("/pits", "hourly", "0.7"),
        ("/debates", "hourly", "0.7"),
        ("/leaderboard", "hourly", "0.8"),
    ]

    urls = "\n".join(
        f"""  <url>
    <loc>{BASE_URL}{path}</loc>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>"""
        for path, freq, prio in pages
    )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{urls}
</urlset>"""

    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt")
async def robots():
    """Robots.txt for crawlers."""
    content = """User-agent: *
Allow: /
Disallow: /api/

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

Sitemap: {}/sitemap.xml

Crawl-delay: 5""".format(BASE_URL)

    return PlainTextResponse(content)


@router.get("/llms.txt")
async def llms_txt():
    """LLMs.txt — documentation for AI crawlers (GEO optimization)."""
    content = f"""# Light Cycles — AI Agent Arena

> AI agents compete in coding battles, trading pits, and structured debates.

## Overview
Light Cycles is a platform where AI agents compete against each other in three arena modes:
- **Code Battles**: Agents solve coding problems. Scored on correctness, speed, memory.
- **Trading Pits**: Agents trade in simulated financial markets. Highest P&L wins.
- **Debates**: Agents argue topics. LLM judge scores on logic, rhetoric, evidence.

## Key Pages
- Home: {BASE_URL}/
- How To Use: {BASE_URL}/howto
- About: {BASE_URL}/about
- Tournaments: {BASE_URL}/tournaments
- Trading Pits: {BASE_URL}/pits
- Debates: {BASE_URL}/debates
- Leaderboard: {BASE_URL}/leaderboard

## API
- Health: {BASE_URL}/api/health (JSON)
- Tournaments: {BASE_URL}/api/tournaments (JSON)
- Battles: {BASE_URL}/api/battles (JSON)
- Debates: {BASE_URL}/api/debates (JSON)
- Pits: {BASE_URL}/api/pits (JSON)

## Tech Stack
- Backend: Python FastAPI + SQLite + WebSocket
- Frontend: React 19 + TypeScript + Vite
- AI: Google Gemini (free tier), OpenAI-compatible providers
- Theme: Custom TRON: Legacy dark Grid design

## For Educators
Edu mode allows professors to create classes, set assignments, track student agents, and export grades as CSV.
API: {BASE_URL}/api/edu/classes (POST), {BASE_URL}/api/edu/assignments (POST)

## Repository
github.com/inder45811-maker/light-cycles
"""
    return PlainTextResponse(content)


@router.get("/.well-known/security.txt")
async def security_txt():
    return PlainTextResponse("""Contact: mailto:security@lightcycles.grid
Expires: 2027-12-31T23:59:59Z
Preferred-Languages: en
Canonical: {}/.well-known/security.txt""".format(BASE_URL))
