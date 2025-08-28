"""
API endpoints for Facebook reactions scraping
"""
import os
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from app.models.requests import ReactionsRequest
from app.models.responses import JobResponse, JobStatusResponse, ErrorResponse
from app.core.job_manager import job_manager
from app.scrapers.reactions_scraper import FacebookReactionsScraper

router = APIRouter(prefix="/reactions", tags=["reactions"])


def reactions_worker(job_id: str, progress_callback, request_data: ReactionsRequest):
    """Worker function for reactions scraping"""
    try:
        # Create scraper instance
        scraper = FacebookReactionsScraper()
        
        # Convert Pydantic models to dict for scraper
        cookies_array = [cookie.dict() for cookie in request_data.cookies]
        
        # Update progress
        progress_callback(job_id, 20, "جاري تحميل الكوكيز...")
        
        # Scrape reactions
        result = scraper.scrape_reactions_api(
            post_url=request_data.post_url,
            cookies_array=cookies_array,
            limit=request_data.limit,
            delay=request_data.delay
        )
        
        # Update progress
        progress_callback(job_id, 90, "جاري حفظ النتائج...")
        
        if result.get("error"):
            raise Exception(result["error"])
        
        return result
        
    except Exception as e:
        raise Exception(f"فشل في سحب التفاعلات: {str(e)}")


@router.post("/scrape", response_model=JobResponse)
async def scrape_reactions(request: ReactionsRequest):
    """
    Start a new reactions scraping job
    
    - **post_url**: Facebook post URL
    - **limit**: Number of reactions to scrape (0 = all)
    - **delay**: Delay between requests in seconds
    - **cookies**: Array of Facebook cookies
    """
    try:
        # Create job
        job_id = job_manager.create_job("reactions", request.post_url)
        
        # Start job in background thread
        success = job_manager.start_job(job_id, reactions_worker, request)
        
        if not success:
            # Check if we hit the concurrent limit
            active_count = job_manager.get_active_jobs_count()
            if active_count >= 5:  # MAX_CONCURRENT_JOBS from settings
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "too_many_requests",
                        "message": "تم تجاوز الحد الأقصى من الطلبات المتزامنة",
                        "active_jobs": active_count,
                        "retry_after": 300
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "job_start_failed",
                        "message": "فشل في بدء المهمة"
                    }
                )
        
        return JobResponse(
            job_id=job_id,
            status="running",
            message="تم بدء سحب التفاعلات بنجاح",
            estimated_time="2-5 دقائق",
            created_at=job_manager.get_job_status(job_id)["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"خطأ داخلي: {str(e)}"
            }
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_reactions_status(job_id: str):
    """
    Get the status of a reactions scraping job
    
    - **job_id**: The job ID returned from /scrape endpoint
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "job_not_found",
                    "message": "المهمة غير موجودة أو منتهية الصلاحية",
                    "job_id": job_id
                }
            )
        
        # Convert to response model
        response_data = {
            "job_id": job_status["job_id"],
            "status": job_status["status"],
            "started_at": job_status.get("started_at"),
            "completed_at": job_status.get("completed_at"),
            "error_message": job_status.get("error_message")
        }
        
        # Add progress if available
        if job_status.get("progress"):
            progress = job_status["progress"]
            response_data["progress"] = {
                "percentage": progress.get("percentage", 0),
                "message": progress.get("message", ""),
                "updated_at": progress.get("updated_at")
            }
            
            # Add additional progress info for reactions
            if job_status["status"] == "running":
                response_data["progress"]["current_page"] = progress.get("current_page")
                response_data["progress"]["items_scraped"] = progress.get("reactions_scraped")
                response_data["progress"]["estimated_total"] = progress.get("estimated_total")
        
        # Add result if completed
        if job_status.get("result") and job_status["status"] == "completed":
            result = job_status["result"]
            response_data["result"] = {
                "total_items": result.get("total_items", 0),
                "file_size": result.get("file_size", "Unknown"),
                "download_expires_at": result.get("download_expires_at", ""),
                "reaction_stats": result.get("reaction_stats")
            }
        
        return JobStatusResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error", 
                "message": f"خطأ في جلب حالة المهمة: {str(e)}"
            }
        )


@router.get("/download/{job_id}")
async def download_reactions(job_id: str):
    """
    Download the results of a completed reactions scraping job
    
    - **job_id**: The job ID returned from /scrape endpoint
    """
    try:
        # Get job status first
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "job_not_found",
                    "message": "المهمة غير موجودة أو منتهية الصلاحية",
                    "job_id": job_id
                }
            )
        
        if job_status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "job_not_completed",
                    "message": f"المهمة لم تكتمل بعد. الحالة الحالية: {job_status['status']}",
                    "current_status": job_status["status"]
                }
            )
        
        # Get file path
        file_path = job_manager.get_job_result_file(job_id)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "file_not_found",
                    "message": "ملف النتائج غير موجود أو منتهي الصلاحية"
                }
            )
        
        # Return file
        filename = f"reactions_{job_id}.json"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "download_failed",
                "message": f"فشل في تحميل الملف: {str(e)}"
            }
        )

