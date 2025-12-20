"""
API endpoints for BidFax connector (admin).
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.bidfax_connector import bidfax_connector
from app.services.jobs import job_service
from app.models.job import JobStatus
from app.models.project import Project

router = APIRouter()


class BidFaxDiscoverRequest(BaseModel):
    """Request schema for discovering BidFax listings."""

    base_url: str = Field(..., description="Category URL (e.g., https://en.bidfax.info/nissan/)")
    max_urls: int = Field(10, description="Maximum URLs to discover (0 = all)", ge=0)


class BidFaxDiscoverResponse(BaseModel):
    """Response schema for BidFax discovery."""

    urls: list[str]
    count: int
    pages_scraped: int
    sample_urls: list[str]


class BidFaxCreateJobsRequest(BaseModel):
    """Request schema for creating scrape jobs."""

    project_id: str = Field(..., description="Project ID to create jobs under")
    urls: list[str] = Field(..., description="List of vehicle URLs to scrape")


class BidFaxCreateJobsResponse(BaseModel):
    """Response schema for job creation."""

    created: int
    rejected: list[str]


class BidFaxParseRequest(BaseModel):
    """Request schema for parsing a single vehicle."""

    url: str = Field(..., description="Vehicle detail URL")


@router.post("/discover", response_model=BidFaxDiscoverResponse)
async def discover_bidfax_listings(
    payload: BidFaxDiscoverRequest,
    db: AsyncSession = Depends(get_db),
) -> BidFaxDiscoverResponse:
    """
    Discover vehicle listing URLs from BidFax category pages.

    Supports pagination - will scrape multiple pages until max_urls reached.
    """
    result = await bidfax_connector.discover_listings(
        db=db,
        base_url=payload.base_url,
        max_urls=payload.max_urls,
    )

    return BidFaxDiscoverResponse(**result)


@router.post("/create-jobs", response_model=BidFaxCreateJobsResponse)
async def create_bidfax_jobs(
    payload: BidFaxCreateJobsRequest,
    db: AsyncSession = Depends(get_db),
) -> BidFaxCreateJobsResponse:
    """
    Create scrape jobs for discovered BidFax URLs.

    Jobs will be queued and processed by workers.
    """
    # Verify project exists
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    created_count = 0
    rejected = []

    for url in payload.urls:
        try:
            # Create job for this URL
            job = await job_service.create_job(
                db=db,
                project_id=payload.project_id,
                name=f"BidFax: {url.split('/')[-1][:50]}",
                target_url=url,
                schedule_now=True,
            )
            created_count += 1
        except Exception as exc:
            rejected.append(f"{url}: {str(exc)}")

    return BidFaxCreateJobsResponse(created=created_count, rejected=rejected)


@router.post("/parse")
async def parse_bidfax_vehicle(
    payload: BidFaxParseRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Parse a single BidFax vehicle listing (for preview/testing).

    Returns parsed vehicle data without creating a job.
    """
    vehicle_data = await bidfax_connector.parse_vehicle(
        db=db,
        url=payload.url,
    )

    if not vehicle_data:
        raise HTTPException(status_code=500, detail="Failed to parse vehicle")

    return vehicle_data


@router.get("/vehicles")
async def list_bidfax_vehicles(
    db: AsyncSession = Depends(get_db),
    project_id: str = None,
    limit: int = 100,
):
    """
    List parsed BidFax vehicles from completed jobs.

    Fetches results from the database for jobs that have finished.
    """
    from sqlalchemy import select
    from app.models.result import Result
    from app.models.job import Job

    # Build query
    query = (
        select(Result)
        .join(Job, Result.job_id == Job.id)
        .where(Job.status == JobStatus.SUCCEEDED)
        .where(Job.target_url.like("%bidfax.info%"))
        .order_by(Result.created_at.desc())
        .limit(limit)
    )

    if project_id:
        query = query.where(Job.project_id == project_id)

    result = await db.execute(query)
    results = result.scalars().all()

    # Extract vehicle data from structured_data
    vehicles = []
    for r in results:
        if r.structured_data:
            vehicles.append({
                "job_id": r.job_id,
                "scraped_at": r.created_at.isoformat() if r.created_at else None,
                **r.structured_data,
            })

    return vehicles


@router.get("/export-csv")
async def export_bidfax_csv(
    db: AsyncSession = Depends(get_db),
    project_id: str = None,
):
    """
    Export BidFax vehicles to CSV.

    Returns CSV file download.
    """
    # Get vehicles
    from sqlalchemy import select
    from app.models.result import Result
    from app.models.job import Job

    query = (
        select(Result)
        .join(Job, Result.job_id == Job.id)
        .where(Job.status == JobStatus.SUCCEEDED)
        .where(Job.target_url.like("%bidfax.info%"))
        .order_by(Result.created_at.desc())
    )

    if project_id:
        query = query.where(Job.project_id == project_id)

    result = await db.execute(query)
    results = result.scalars().all()

    vehicles = []
    for r in results:
        if r.structured_data:
            vehicles.append(r.structured_data)

    # Generate CSV
    csv_content = bidfax_connector.generate_csv(vehicles)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bidfax_vehicles.csv"},
    )


@router.post("/run-all")
async def run_all_bidfax_workflow(
    project_id: str,
    base_url: str = "https://en.bidfax.info/nissan/",
    max_urls: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Complete workflow: Discover → Create Jobs → Return summary.

    This doesn't scrape immediately, but queues jobs for workers.
    """
    # Discover URLs
    discovery_result = await bidfax_connector.discover_listings(
        db=db,
        base_url=base_url,
        max_urls=max_urls,
    )

    # Create jobs
    created_count = 0
    rejected = []

    for url in discovery_result["urls"]:
        try:
            await job_service.create_job(
                db=db,
                project_id=project_id,
                name=f"BidFax: {url.split('/')[-1][:50]}",
                target_url=url,
                schedule_now=True,
            )
            created_count += 1
        except Exception as exc:
            rejected.append(f"{url}: {str(exc)}")

    return {
        "discovered": discovery_result["count"],
        "pages_scraped": discovery_result["pages_scraped"],
        "sample_urls": discovery_result["sample_urls"],
        "jobs_created": created_count,
        "jobs_rejected": len(rejected),
        "rejected": rejected,
    }
