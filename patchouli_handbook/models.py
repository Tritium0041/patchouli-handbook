from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class NotableSegment(BaseModel):
    timestamp: str = Field(..., min_length=1)
    excerpt: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class StructuredSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary_zh: str = Field(..., min_length=1)
    key_points: list[str]
    action_steps: list[str]
    tools_or_resources: list[str]
    notable_segments: list[NotableSegment]
    transcript_language: str = Field(..., min_length=1)
    source_video_url: str = Field(..., min_length=1)


@dataclass(slots=True)
class VideoSummaryDocument:
    video_id: str
    title: str
    url: str
    published_at: str | None
    sequence: int
    summary: StructuredSummary

    @classmethod
    def from_clean_json(
        cls,
        payload: dict,
        *,
        video_id: str,
        title: str,
        url: str,
        published_at: str | None,
        sequence: int,
    ) -> "VideoSummaryDocument":
        return cls(
            video_id=video_id,
            title=title,
            url=url,
            published_at=published_at,
            sequence=sequence,
            summary=StructuredSummary.model_validate(payload),
        )
