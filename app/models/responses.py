"""
Pydantic models for API responses
"""
from typing import Dict, Optional, Any, List
from pydantic import BaseModel
from datetime import datetime


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str
    status: str
    message: str
    estimated_time: Optional[str] = None
    created_at: str


class ProgressInfo(BaseModel):
    """Progress information model"""
    percentage: int
    message: str
    current_page: Optional[int] = None
    items_scraped: Optional[int] = None
    estimated_total: Optional[int] = None
    updated_at: Optional[str] = None


class ResultInfo(BaseModel):
    """Result information model"""
    total_items: int
    file_size: str
    download_expires_at: str
    pages_scraped: Optional[int] = None
    reaction_stats: Optional[Dict[str, int]] = None
    unique_authors: Optional[int] = None


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: Optional[ProgressInfo] = None
    result: Optional[ResultInfo] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    active_jobs: int
    available_slots: int
    system_load: str
    uptime: str


class JobsSummaryResponse(BaseModel):
    """Jobs summary response model"""
    total_jobs: int
    active_jobs: int
    available_slots: int
    jobs_by_status: Dict[str, int]

