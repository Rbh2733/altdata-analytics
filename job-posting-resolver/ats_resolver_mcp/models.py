"""Pydantic input models and the normalized Posting schema.

A single normalized Posting shape is produced by every provider, so the tools and the
caller never have to know which ATS a listing came from.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class WorkplaceType(str, Enum):
    """Normalized work arrangement. 'unknown' means the source did not state it."""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class Posting(BaseModel):
    """Normalized job posting, uniform across every ATS source."""
    model_config = ConfigDict(use_enum_values=True)

    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    workplace_type: WorkplaceType = WorkplaceType.UNKNOWN
    department: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[str] = None
    source: str = ""
    job_id: Optional[str] = None
    description_excerpt: Optional[str] = None


# --------------------------- Tool input models ---------------------------

class ResolveAtsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    company: str = Field(
        ...,
        description="Company name (e.g. 'Acme Analytics', \"Grimble's Fine Foods\") or a known ATS board slug (e.g. 'acme').",
        min_length=1, max_length=120,
    )
    hint_url: Optional[str] = Field(
        default=None,
        description="Optional ATS or careers URL to parse directly (e.g. a Greenhouse/Lever/Ashby link an aggregator redirected to). When given, detection is exact and skips slug guessing.",
        max_length=500,
    )


class ListJobsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    company: str = Field(..., description="Company name or ATS board slug.", min_length=1, max_length=120)
    hint_url: Optional[str] = Field(default=None, description="Optional ATS/careers URL to use directly instead of slug detection.", max_length=500)
    query: Optional[str] = Field(default=None, description="Optional case-insensitive substring to filter role titles (e.g. 'insights', 'market intelligence').", max_length=120)
    location: Optional[str] = Field(default=None, description="Optional case-insensitive substring to filter the location field (e.g. 'remote', 'austin', 'tx').", max_length=120)
    limit: int = Field(default=25, description="Maximum postings to return.", ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="'markdown' (human-readable) or 'json' (machine-readable).")


class GetJobInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    company: str = Field(..., description="Company name or ATS board slug.", min_length=1, max_length=120)
    job_id: Optional[str] = Field(default=None, description="ATS job id (from list_jobs). Provide job_id OR url.", max_length=200)
    url: Optional[str] = Field(default=None, description="Direct posting URL. Provide job_id OR url.", max_length=500)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="'markdown' or 'json'.")


class VerifyRemoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    company: str = Field(..., description="Company name or ATS board slug (e.g. 'Acme Analytics').", min_length=1, max_length=120)
    title: str = Field(..., description="Role title to verify, as seen on the aggregator (e.g. 'Market Research Analyst').", min_length=1, max_length=200)
    hint_url: Optional[str] = Field(default=None, description="Optional ATS/careers URL to use directly.", max_length=500)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="'markdown' or 'json'.")


class ScrapeCareersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    url: str = Field(..., description="Careers-page or single-posting URL to fetch and parse as a last resort when no ATS API is detected.", min_length=4, max_length=500)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="'markdown' or 'json'.")
