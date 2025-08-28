"""
Facebook Scraper API - Main Application
Threading-based FastAPI application for Facebook reactions and comments scraping
"""
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.reactions import router as reactions_router
from app.api.comments import router as comments_router
from app.core.job_manager import job_manager
from app.models.responses import HealthResponse, JobsSummaryResponse

# Application start time for uptime calculation
app_start_time = time.time()

# Create FastAPI application
app = FastAPI(
    title="Facebook Scraper API",
    description="Threading-based API for scraping Facebook reactions and comments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(reactions_router, prefix=settings.API_PREFIX)
app.include_router(comments_router, prefix=settings.API_PREFIX)


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Facebook Scraper API",
        "version": "1.0.0",
        "description": "Threading-based API for Facebook scraping",
        "endpoints": {
            "reactions": {
                "scrape": f"{settings.API_PREFIX}/reactions/scrape",
                "status": f"{settings.API_PREFIX}/reactions/status/{{job_id}}",
                "download": f"{settings.API_PREFIX}/reactions/download/{{job_id}}"
            },
            "comments": {
                "scrape": f"{settings.API_PREFIX}/comments/scrape",
                "status": f"{settings.API_PREFIX}/comments/status/{{job_id}}",
                "download": f"{settings.API_PREFIX}/comments/download/{{job_id}}"
            },
            "system": {
                "health": "/health",
                "jobs": "/jobs",
                "docs": "/docs"
            }
        },
        "features": [
            "Concurrent job processing",
            "Real-time progress tracking",
            "Automatic file cleanup",
            "Comprehensive error handling",
            "Arabic language support"
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Calculate uptime
        uptime_seconds = int(time.time() - app_start_time)
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime = f"{uptime_hours}h {uptime_minutes}m"
        
        # Get job manager stats
        summary = job_manager.get_all_jobs_summary()
        
        # Determine system load
        active_jobs = summary["active_jobs"]
        max_jobs = settings.MAX_CONCURRENT_JOBS
        
        if active_jobs == 0:
            system_load = "idle"
        elif active_jobs < max_jobs * 0.5:
            system_load = "light"
        elif active_jobs < max_jobs * 0.8:
            system_load = "moderate"
        else:
            system_load = "heavy"
        
        return HealthResponse(
            status="healthy",
            active_jobs=active_jobs,
            available_slots=summary["available_slots"],
            system_load=system_load,
            uptime=uptime
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "health_check_failed",
                "message": f"فشل في فحص حالة النظام: {str(e)}"
            }
        )


@app.get("/jobs", response_model=JobsSummaryResponse)
async def jobs_summary():
    """Get summary of all jobs"""
    try:
        summary = job_manager.get_all_jobs_summary()
        
        return JobsSummaryResponse(
            total_jobs=summary["total_jobs"],
            active_jobs=summary["active_jobs"],
            available_slots=summary["available_slots"],
            jobs_by_status=summary["jobs_by_status"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "jobs_summary_failed",
                "message": f"فشل في جلب ملخص المهام: {str(e)}"
            }
        )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "الصفحة المطلوبة غير موجودة",
            "available_endpoints": [
                f"{settings.API_PREFIX}/reactions/scrape",
                f"{settings.API_PREFIX}/comments/scrape",
                "/health",
                "/jobs",
                "/docs"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "خطأ داخلي في الخادم",
            "support": "تحقق من logs الخادم للتفاصيل"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print("=" * 80)
    print("🚀 Facebook Scraper API - Starting Up")
    print("=" * 80)
    print(f"📊 Max concurrent jobs: {settings.MAX_CONCURRENT_JOBS}")
    print(f"📁 Results directory: {settings.RESULTS_DIR}")
    print(f"🕐 File cleanup after: {settings.CLEANUP_AFTER_HOURS} hours")
    print(f"🌐 API prefix: {settings.API_PREFIX}")
    print("=" * 80)
    print("✅ Application started successfully!")
    print(f"📖 Documentation: http://localhost:{settings.PORT}/docs")
    print("=" * 80)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("\n" + "=" * 80)
    print("🛑 Facebook Scraper API - Shutting Down")
    print("=" * 80)
    
    # Get final stats
    try:
        summary = job_manager.get_all_jobs_summary()
        print(f"📊 Final Stats:")
        print(f"   Total jobs processed: {summary['total_jobs']}")
        print(f"   Active jobs: {summary['active_jobs']}")
        print(f"   Jobs by status: {summary['jobs_by_status']}")
    except:
        pass
    
    print("✅ Application shutdown complete!")
    print("=" * 80)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

