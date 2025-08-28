#!/usr/bin/env python3
"""
Facebook Scraper API - Runner
Simple runner script for the FastAPI application
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting Facebook Scraper API...")
    print(f"🌐 Server will run on: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

