from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class Motor3DDiscoverRequest(BaseModel):
    sitemap_url: HttpUrl = Field(default="https://motor3dmodel.ir/wp-sitemap.xml")
    url_prefix: HttpUrl = Field(default="https://motor3dmodel.ir/product/")
    limit: int = Field(default=5000, ge=1, le=20000)


class Motor3DDiscoverResponse(BaseModel):
    count: int
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


class Motor3DProduct(BaseModel):
    url: str
    title: Optional[str] = None
    price_text: Optional[str] = None
    images: list[str] = []
    categories: list[str] = []
    tags: list[str] = []
    description_html: Optional[str] = None
    sku: Optional[str] = None
    raw: dict = {}
