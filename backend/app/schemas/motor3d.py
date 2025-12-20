from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class Motor3DDiscoverRequest(BaseModel):
    sitemap_url: HttpUrl | None = Field(default=None)
    domain: str | None = Field(default="motor3dmodel.ir")
    url_prefix: HttpUrl | None = Field(default=None)
    max_urls: int = Field(default=2000, ge=1, le=20000)


class Motor3DDiscoverResponse(BaseModel):
    count: int
    sample_urls: list[str]
    urls: list[str]


class Motor3DCreateJobsRequest(BaseModel):
    project_id: str
    urls: list[str]
    policy_domain: str = Field(default="motor3dmodel.ir")
    name_prefix: str = Field(default="Motor3D product")
    allow_duplicates: bool = False


class Motor3DCreateJobsResponse(BaseModel):
    created: int
    rejected: list[dict[str, str]]


class Motor3DParseRequest(BaseModel):
    url: HttpUrl
    method: Optional[Literal["auto", "http", "playwright"]] = None
    project_id: Optional[str] = None


class Motor3DProduct(BaseModel):
    url: str
    title: Optional[str] = None
    price_text: Optional[str] = None
    images: list[str] = []
    specs: list[str] = []
    categories: list[str] = []
    tags: list[str] = []
    description_html: Optional[str] = None
    sku: Optional[str] = None
    raw: dict = {}
