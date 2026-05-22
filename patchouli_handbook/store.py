from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .builder import (
    HandbookBlueprint,
    HandbookCategory,
    HandbookEntry,
    render_category_markdown,
    render_entry_markdown,
    render_entry_skill_markdown,
    render_guide_markdown,
    render_index_markdown,
)
from .utils import safe_slug


def _unique_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]

    seen: set[str] = set()
    items: list[str] = []
    for raw_item in raw_items:
        item = str(raw_item).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        items.append(item)
    return items


def _slug_from(value: str | None, *, fallback: str, max_length: int = 80) -> str:
    candidate = str(value or "").strip() or fallback
    slug = safe_slug(candidate, max_length=max_length)
    if slug == "job":
        raise ValueError("A lowercase ASCII slug is required when the title cannot form one.")
    return slug


def _entry_path(category_slug: str, entry_slug: str) -> str:
    return f"categories/{category_slug}/{entry_slug}.md"


def _category_path(category_slug: str) -> str:
    return f"categories/{category_slug}/CATEGORY.md"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _delete_if_stale(root: Path, relative_path: str, current_paths: set[str]) -> None:
    if not relative_path or relative_path in current_paths:
        return
    path = root / relative_path
    if path.exists() and path.is_file():
        path.unlink()
    for parent in [path.parent, path.parent.parent]:
        if parent == root or not parent.exists():
            continue
        try:
            parent.rmdir()
        except OSError:
            pass


class HandbookStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format_name: str = "patchouli-handbook"
    manifest_path: str = "manifest.json"
    guide_path: str = "GUIDE.md"
    index_path: str = "INDEX.md"
    category_path_pattern: str = "categories/{category_slug}/CATEGORY.md"
    entry_path_pattern: str = "categories/{category_slug}/{entry_slug}.md"
    evidence_path_pattern: str = "evidence/{video_id}.md"
    glossary_path: str = "references/glossary.md"
    source_index_path: str = "references/source_index.md"
    entry_skill_path: str = "entry_skill/SKILL.md"
    manifest_fields: list[str] = Field(
        default_factory=lambda: [
            "book_title",
            "book_slug",
            "description",
            "audience",
            "routing_rules",
            "categories",
            "entries",
            "source_videos",
            "guide_path",
        ]
    )
    category_fields: list[str] = Field(
        default_factory=lambda: [
            "title",
            "slug",
            "path",
            "description",
            "when_to_read",
            "core_terms",
            "entries",
        ]
    )
    entry_fields: list[str] = Field(
        default_factory=lambda: [
            "title",
            "slug",
            "category_slug",
            "path",
            "summary",
            "use_when",
            "do_this",
            "checklist",
            "anti_patterns",
            "read_next",
            "source_videos",
        ]
    )
    writable_kinds: list[str] = Field(default_factory=lambda: ["book", "category", "entry"])
    operations: list[str] = Field(
        default_factory=lambda: [
            "describe",
            "validate",
            "list_categories",
            "list_entries",
            "get_category",
            "get_entry",
            "update_book",
            "create_category",
            "update_category",
            "delete_category",
            "create_entry",
            "update_entry",
            "delete_entry",
        ]
    )


class HandbookEntryRef(BaseModel):
    model_config = ConfigDict(extra="allow")

    slug: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)


class HandbookManifestCategory(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    when_to_read: list[str] = Field(default_factory=list)
    core_terms: list[str] = Field(default_factory=list)
    entries: list[HandbookEntryRef] = Field(default_factory=list)

    @field_validator("when_to_read", "core_terms", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookManifestEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    category_slug: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    read_next: list[str] = Field(default_factory=list)
    source_videos: list[str] = Field(default_factory=list)

    @field_validator("read_next", "source_videos", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookSourceVideo(BaseModel):
    model_config = ConfigDict(extra="allow")

    video_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    published_at: str | None = None
    source_video_url: str = Field(..., min_length=1)
    evidence_path: str = Field(..., min_length=1)


class HandbookManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    book_title: str = Field(..., min_length=1)
    book_slug: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    routing_rules: list[str] = Field(default_factory=list)
    categories: list[HandbookManifestCategory] = Field(default_factory=list)
    entries: list[HandbookManifestEntry] = Field(default_factory=list)
    source_videos: list[HandbookSourceVideo] | int = Field(default_factory=list)
    guide_path: str = "GUIDE.md"
    entry_skill_path: str = "entry_skill/SKILL.md"
    index_path: str = "INDEX.md"
    glossary_path: str = "references/glossary.md"
    source_index_path: str = "references/source_index.md"
    status: str | None = None
    category_count: int | None = None
    entry_count: int | None = None
    source_video_count: int | None = None

    @field_validator("routing_rules", mode="before")
    @classmethod
    def normalize_routing_rules(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookBookPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    book_title: str | None = None
    book_slug: str | None = None
    description: str | None = None
    audience: str | None = None
    routing_rules: list[str] | None = None

    @field_validator("routing_rules", mode="before")
    @classmethod
    def normalize_routing_rules(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _unique_string_list(value)

    @model_validator(mode="after")
    def require_change(self) -> "HandbookBookPatch":
        if not self.model_fields_set:
            raise ValueError("At least one book field must be provided.")
        return self


class StoredHandbookCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    path: str | None = None
    description: str = Field(..., min_length=1)
    when_to_read: list[str] = Field(default_factory=list)
    core_terms: list[str] = Field(default_factory=list)
    entry_slugs: list[str] = Field(default_factory=list)

    @field_validator("when_to_read", "core_terms", "entry_slugs", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class StoredHandbookEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    category_slug: str = Field(..., min_length=1)
    path: str | None = None
    summary: str = Field(..., min_length=1)
    use_when: list[str] = Field(default_factory=list)
    do_this: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    read_next: list[str] = Field(default_factory=list)
    source_videos: list[str] = Field(default_factory=list)

    @field_validator(
        "use_when",
        "do_this",
        "checklist",
        "anti_patterns",
        "read_next",
        "source_videos",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    slug: str | None = None
    description: str = Field(..., min_length=1)
    when_to_read: list[str] = Field(default_factory=list)
    core_terms: list[str] = Field(default_factory=list)

    @field_validator("when_to_read", "core_terms", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookCategoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    slug: str | None = None
    description: str | None = None
    when_to_read: list[str] | None = None
    core_terms: list[str] | None = None

    @field_validator("when_to_read", "core_terms", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _unique_string_list(value)

    @model_validator(mode="after")
    def require_change(self) -> "HandbookCategoryPatch":
        if not self.model_fields_set:
            raise ValueError("At least one category field must be provided.")
        return self


class HandbookEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    slug: str | None = None
    category_slug: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    use_when: list[str] = Field(default_factory=list)
    do_this: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    read_next: list[str] = Field(default_factory=list)
    source_videos: list[str] = Field(default_factory=list)

    @field_validator(
        "use_when",
        "do_this",
        "checklist",
        "anti_patterns",
        "read_next",
        "source_videos",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _unique_string_list(value)


class HandbookEntryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    slug: str | None = None
    category_slug: str | None = None
    summary: str | None = None
    use_when: list[str] | None = None
    do_this: list[str] | None = None
    checklist: list[str] | None = None
    anti_patterns: list[str] | None = None
    read_next: list[str] | None = None
    source_videos: list[str] | None = None

    @field_validator(
        "use_when",
        "do_this",
        "checklist",
        "anti_patterns",
        "read_next",
        "source_videos",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _unique_string_list(value)

    @model_validator(mode="after")
    def require_change(self) -> "HandbookEntryPatch":
        if not self.model_fields_set:
            raise ValueError("At least one entry field must be provided.")
        return self


class HandbookValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str = Field(..., pattern="^(error|warning)$")
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    path: str | None = None
    slug: str | None = None


class HandbookValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[HandbookValidationIssue] = Field(default_factory=list)
    warnings: list[HandbookValidationIssue] = Field(default_factory=list)
    category_count: int
    entry_count: int
    source_video_count: int


class HandbookOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., min_length=1)
    handbook: str | None = None
    slug: str | None = None
    category_slug: str | None = None
    force: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)


@dataclass(slots=True)
class _HandbookState:
    manifest: HandbookManifest
    categories: list[StoredHandbookCategory]
    entries: list[StoredHandbookEntry]


def describe_handbook_structure() -> HandbookStructure:
    return HandbookStructure()


def create_empty_handbook(
    handbook_dir: str | Path,
    *,
    title: str,
    slug: str | None = None,
    description: str | None = None,
    audience: str | None = None,
    overwrite: bool = False,
) -> HandbookManifest:
    root = Path(handbook_dir).expanduser().resolve()
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise FileExistsError(f"Output directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    book_title = title.strip()
    if not book_title:
        raise ValueError("title is required.")
    book_slug = _slug_from(slug, fallback=book_title)
    manifest = HandbookManifest(
        book_title=book_title,
        book_slug=book_slug,
        description=(description or f"{book_title} handbook for AI-assisted reference and execution.").strip(),
        audience=(audience or "AI agents and human maintainers who need reusable guidance.").strip(),
        routing_rules=[
            "Read GUIDE.md for the operating protocol before using this handbook for complex tasks.",
            "Read INDEX.md to select the smallest relevant category before opening entries.",
            "Open evidence pages only when source grounding, examples, or conflict resolution are needed.",
        ],
        categories=[],
        entries=[],
        source_videos=[],
        guide_path="GUIDE.md",
        entry_skill_path="entry_skill/SKILL.md",
        index_path="INDEX.md",
        glossary_path="references/glossary.md",
        source_index_path="references/source_index.md",
        status="draft",
        category_count=0,
        entry_count=0,
        source_video_count=0,
    )
    state = _HandbookState(manifest=manifest, categories=[], entries=[])
    store = HandbookStore(root)
    store._write_state(state)
    _write_text(root / manifest.glossary_path, "# Glossary\n\nAdd cross-entry terms here as the handbook grows.")
    if manifest.source_index_path:
        _write_text(root / manifest.source_index_path, "# Source Index\n\nAdd source-to-entry links here when evidence pages are available.")
    return store.load_manifest()


def _parse_markdown_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in markdown.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


def _parse_markdown_list(section: str, *, numbered: bool = False) -> list[str]:
    items: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if numbered:
            match = re.match(r"^\d+\.\s+(.*)$", line)
        else:
            match = re.match(r"^-\s+(.*)$", line)
        if match:
            items.append(match.group(1).strip())
        elif not line.startswith("#"):
            items.append(line)
    return _unique_string_list(items)


def _source_video_count(manifest: HandbookManifest) -> int:
    if isinstance(manifest.source_videos, int):
        return manifest.source_video_count or manifest.source_videos
    return len(manifest.source_videos)


def _render_source_index_from_manifest(manifest: HandbookManifest) -> str | None:
    if isinstance(manifest.source_videos, int):
        return None

    entry_by_video: dict[str, list[HandbookManifestEntry]] = defaultdict(list)
    for entry in manifest.entries:
        for video_id in entry.source_videos:
            entry_by_video[video_id].append(entry)

    lines = [
        "# Source Index",
        "",
        "本索引把 handbook 条目回溯到具体视频证据页。",
    ]
    for index, video in enumerate(manifest.source_videos, start=1):
        lines.extend(
            [
                "",
                f"## {index}. {video.title}",
                f"- video_id: {video.video_id}",
                f"- published_at: {video.published_at or 'unknown'}",
                f"- source_video_url: {video.source_video_url}",
                f"- evidence: [{video.video_id}]({video.evidence_path})",
            ]
        )
        used_by_entries = entry_by_video.get(video.video_id, [])
        if used_by_entries:
            lines.append("- used_by_entries:")
            for entry in used_by_entries:
                lines.append(f"  - [{entry.title}]({entry.path})")
    return "\n".join(lines)


class HandbookStore:
    """Programmatic CRUD facade for an on-disk Patchouli handbook artifact."""

    def __init__(self, handbook_dir: str | Path) -> None:
        self.root = Path(handbook_dir).expanduser().resolve()

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    def load_manifest(self) -> HandbookManifest:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Missing handbook manifest: {self.manifest_path}")
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return HandbookManifest.model_validate(payload)

    def describe(self) -> dict[str, Any]:
        manifest = self.load_manifest()
        return {
            "structure": describe_handbook_structure().model_dump(),
            "book_title": manifest.book_title,
            "book_slug": manifest.book_slug,
            "category_count": len(manifest.categories),
            "entry_count": len(manifest.entries),
            "source_video_count": _source_video_count(manifest),
        }

    def update_book(self, data: dict[str, Any] | HandbookBookPatch) -> HandbookManifest:
        payload = data if isinstance(data, HandbookBookPatch) else HandbookBookPatch.model_validate(data)
        state = self._load_state()
        manifest = state.manifest
        if payload.book_title is not None:
            manifest.book_title = payload.book_title.strip()
        if payload.book_slug is not None:
            manifest.book_slug = _slug_from(payload.book_slug, fallback=manifest.book_title)
        if payload.description is not None:
            manifest.description = payload.description.strip()
        if payload.audience is not None:
            manifest.audience = payload.audience.strip()
        if payload.routing_rules is not None:
            manifest.routing_rules = payload.routing_rules
        self._write_state(state)
        return self.load_manifest()

    def validate(self) -> HandbookValidationReport:
        state = self._load_state()
        errors: list[HandbookValidationIssue] = []
        warnings: list[HandbookValidationIssue] = []
        manifest = state.manifest

        category_slugs = [category.slug for category in state.categories]
        entry_slugs = [entry.slug for entry in state.entries]
        category_set = set(category_slugs)
        entry_set = set(entry_slugs)

        for slug in sorted({slug for slug in category_slugs if category_slugs.count(slug) > 1}):
            errors.append(
                HandbookValidationIssue(
                    severity="error",
                    code="duplicate_category_slug",
                    message=f"Duplicate category slug: {slug}",
                    slug=slug,
                )
            )
        for slug in sorted({slug for slug in entry_slugs if entry_slugs.count(slug) > 1}):
            errors.append(
                HandbookValidationIssue(
                    severity="error",
                    code="duplicate_entry_slug",
                    message=f"Duplicate entry slug: {slug}",
                    slug=slug,
                )
            )

        if manifest.category_count is not None and manifest.category_count != len(state.categories):
            warnings.append(
                HandbookValidationIssue(
                    severity="warning",
                    code="category_count_mismatch",
                    message=f"category_count is {manifest.category_count}, but manifest contains {len(state.categories)} categories.",
                    path="manifest.json",
                )
            )
        if manifest.entry_count is not None and manifest.entry_count != len(state.entries):
            warnings.append(
                HandbookValidationIssue(
                    severity="warning",
                    code="entry_count_mismatch",
                    message=f"entry_count is {manifest.entry_count}, but manifest contains {len(state.entries)} entries.",
                    path="manifest.json",
                )
            )

        for category in state.categories:
            expected_path = _category_path(category.slug)
            if category.path != expected_path:
                warnings.append(
                    HandbookValidationIssue(
                        severity="warning",
                        code="category_path_mismatch",
                        message=f"Category {category.slug} path should be {expected_path}.",
                        path=category.path,
                        slug=category.slug,
                    )
                )
            category_file = self.root / expected_path
            if not category_file.exists():
                errors.append(
                    HandbookValidationIssue(
                        severity="error",
                        code="missing_category_file",
                        message=f"Missing category file for {category.slug}.",
                        path=expected_path,
                        slug=category.slug,
                    )
                )
            for entry_slug in category.entry_slugs:
                if entry_slug not in entry_set:
                    errors.append(
                        HandbookValidationIssue(
                            severity="error",
                            code="category_references_missing_entry",
                            message=f"Category {category.slug} references missing entry {entry_slug}.",
                            path=expected_path,
                            slug=category.slug,
                        )
                    )

        for entry in state.entries:
            expected_path = _entry_path(entry.category_slug, entry.slug)
            if entry.category_slug not in category_set:
                errors.append(
                    HandbookValidationIssue(
                        severity="error",
                        code="entry_references_missing_category",
                        message=f"Entry {entry.slug} references missing category {entry.category_slug}.",
                        path=entry.path,
                        slug=entry.slug,
                    )
                )
            if entry.path != expected_path:
                warnings.append(
                    HandbookValidationIssue(
                        severity="warning",
                        code="entry_path_mismatch",
                        message=f"Entry {entry.slug} path should be {expected_path}.",
                        path=entry.path,
                        slug=entry.slug,
                    )
                )
            if not (self.root / expected_path).exists():
                errors.append(
                    HandbookValidationIssue(
                        severity="error",
                        code="missing_entry_file",
                        message=f"Missing entry file for {entry.slug}.",
                        path=expected_path,
                        slug=entry.slug,
                    )
                )
            for next_slug in entry.read_next:
                if next_slug == entry.slug:
                    errors.append(
                        HandbookValidationIssue(
                            severity="error",
                            code="entry_read_next_self",
                            message=f"Entry {entry.slug} cannot read_next itself.",
                            path=entry.path,
                            slug=entry.slug,
                        )
                    )
                elif next_slug not in entry_set:
                    errors.append(
                        HandbookValidationIssue(
                            severity="error",
                            code="entry_read_next_missing",
                            message=f"Entry {entry.slug} references missing read_next entry {next_slug}.",
                            path=entry.path,
                            slug=entry.slug,
                        )
                    )

        for required_path in [manifest.guide_path, manifest.index_path, manifest.entry_skill_path, manifest.glossary_path, manifest.source_index_path]:
            if required_path and not (self.root / required_path).exists():
                warnings.append(
                    HandbookValidationIssue(
                        severity="warning",
                        code="missing_reference_file",
                        message=f"Missing reference file: {required_path}",
                        path=required_path,
                    )
                )

        return HandbookValidationReport(
            ok=not errors,
            errors=errors,
            warnings=warnings,
            category_count=len(state.categories),
            entry_count=len(state.entries),
            source_video_count=_source_video_count(manifest),
        )

    def apply_operation(self, operation: dict[str, Any] | HandbookOperation) -> Any:
        request = operation if isinstance(operation, HandbookOperation) else HandbookOperation.model_validate(operation)
        action = request.action
        if action == "describe":
            return self.describe()
        if action == "validate":
            return self.validate()
        if action == "list_categories":
            return self.list_categories()
        if action == "list_entries":
            return self.list_entries(category_slug=request.category_slug)
        if action == "get_category":
            if not request.slug:
                raise ValueError("slug is required for get_category.")
            return self.get_category(request.slug)
        if action == "get_entry":
            if not request.slug:
                raise ValueError("slug is required for get_entry.")
            return self.get_entry(request.slug)
        if action == "update_book":
            return self.update_book(request.payload)
        if action == "create_category":
            return self.create_category(request.payload)
        if action == "update_category":
            if not request.slug:
                raise ValueError("slug is required for update_category.")
            return self.update_category(request.slug, request.payload)
        if action == "delete_category":
            if not request.slug:
                raise ValueError("slug is required for delete_category.")
            return self.delete_category(request.slug, force=request.force)
        if action == "create_entry":
            return self.create_entry(request.payload)
        if action == "update_entry":
            if not request.slug:
                raise ValueError("slug is required for update_entry.")
            return self.update_entry(request.slug, request.payload)
        if action == "delete_entry":
            if not request.slug:
                raise ValueError("slug is required for delete_entry.")
            return self.delete_entry(request.slug)
        raise ValueError(f"Unknown handbook operation: {action}")

    def list_categories(self) -> list[StoredHandbookCategory]:
        return self._load_state().categories

    def list_entries(self, *, category_slug: str | None = None) -> list[StoredHandbookEntry]:
        entries = self._load_state().entries
        if category_slug is None:
            return entries
        return [entry for entry in entries if entry.category_slug == category_slug]

    def get_category(self, slug: str) -> StoredHandbookCategory:
        state = self._load_state()
        for category in state.categories:
            if category.slug == slug:
                return category
        raise KeyError(f"Unknown category: {slug}")

    def get_entry(self, slug: str) -> StoredHandbookEntry:
        state = self._load_state()
        for entry in state.entries:
            if entry.slug == slug:
                return entry
        raise KeyError(f"Unknown entry: {slug}")

    def create_category(self, data: dict[str, Any] | HandbookCategoryCreate) -> StoredHandbookCategory:
        payload = data if isinstance(data, HandbookCategoryCreate) else HandbookCategoryCreate.model_validate(data)
        state = self._load_state()
        slug = _slug_from(payload.slug, fallback=payload.title)
        if any(category.slug == slug for category in state.categories):
            raise ValueError(f"Category already exists: {slug}")
        state.categories.append(
            StoredHandbookCategory(
                title=payload.title.strip(),
                slug=slug,
                path=_category_path(slug),
                description=payload.description.strip(),
                when_to_read=payload.when_to_read,
                core_terms=payload.core_terms,
                entry_slugs=[],
            )
        )
        self._write_state(state)
        return self.get_category(slug)

    def update_category(self, slug: str, data: dict[str, Any] | HandbookCategoryPatch) -> StoredHandbookCategory:
        payload = data if isinstance(data, HandbookCategoryPatch) else HandbookCategoryPatch.model_validate(data)
        state = self._load_state()
        category = self._find_category(state, slug)
        old_slug = category.slug
        old_paths = [_category_path(old_slug)]
        old_paths.extend(_entry_path(entry.category_slug, entry.slug) for entry in state.entries if entry.category_slug == old_slug)

        new_slug = old_slug
        if payload.slug is not None:
            new_slug = _slug_from(payload.slug, fallback=category.title)
            if new_slug != old_slug and any(item.slug == new_slug for item in state.categories):
                raise ValueError(f"Category already exists: {new_slug}")

        category.title = (payload.title or category.title).strip()
        category.slug = new_slug
        category.path = _category_path(new_slug)
        category.description = (payload.description or category.description).strip()
        if payload.when_to_read is not None:
            category.when_to_read = payload.when_to_read
        if payload.core_terms is not None:
            category.core_terms = payload.core_terms

        if new_slug != old_slug:
            for entry in state.entries:
                if entry.category_slug == old_slug:
                    entry.category_slug = new_slug
                    entry.path = _entry_path(new_slug, entry.slug)
        self._write_state(state, old_paths=old_paths)
        return self.get_category(new_slug)

    def delete_category(self, slug: str, *, force: bool = False) -> StoredHandbookCategory:
        state = self._load_state()
        category = self._find_category(state, slug)
        category_entries = [entry for entry in state.entries if entry.category_slug == slug]
        if category_entries and not force:
            raise ValueError(f"Category is not empty: {slug}. Pass force=True to delete its entries.")
        deleted_entry_slugs = {entry.slug for entry in category_entries}
        old_paths = [_category_path(category.slug)]
        old_paths.extend(_entry_path(entry.category_slug, entry.slug) for entry in category_entries)
        state.categories = [item for item in state.categories if item.slug != slug]
        if force:
            state.entries = [entry for entry in state.entries if entry.category_slug != slug]
            for entry in state.entries:
                entry.read_next = [item for item in entry.read_next if item not in deleted_entry_slugs]
        self._write_state(state, old_paths=old_paths)
        return category

    def create_entry(self, data: dict[str, Any] | HandbookEntryCreate) -> StoredHandbookEntry:
        payload = data if isinstance(data, HandbookEntryCreate) else HandbookEntryCreate.model_validate(data)
        state = self._load_state()
        self._find_category(state, payload.category_slug)
        slug = _slug_from(payload.slug, fallback=payload.title)
        if any(entry.slug == slug for entry in state.entries):
            raise ValueError(f"Entry already exists: {slug}")
        self._validate_read_next(state, payload.read_next, current_slug=slug)
        entry = StoredHandbookEntry(
            title=payload.title.strip(),
            slug=slug,
            category_slug=payload.category_slug,
            path=_entry_path(payload.category_slug, slug),
            summary=payload.summary.strip(),
            use_when=payload.use_when,
            do_this=payload.do_this,
            checklist=payload.checklist,
            anti_patterns=payload.anti_patterns,
            read_next=payload.read_next,
            source_videos=payload.source_videos,
        )
        state.entries.append(entry)
        category = self._find_category(state, payload.category_slug)
        category.entry_slugs = _unique_string_list(category.entry_slugs + [slug])
        self._write_state(state)
        return self.get_entry(slug)

    def update_entry(self, slug: str, data: dict[str, Any] | HandbookEntryPatch) -> StoredHandbookEntry:
        payload = data if isinstance(data, HandbookEntryPatch) else HandbookEntryPatch.model_validate(data)
        state = self._load_state()
        entry = self._find_entry(state, slug)
        old_slug = entry.slug
        old_path = _entry_path(entry.category_slug, entry.slug)

        new_slug = old_slug
        if payload.slug is not None:
            new_slug = _slug_from(payload.slug, fallback=entry.title)
            if new_slug != old_slug and any(item.slug == new_slug for item in state.entries):
                raise ValueError(f"Entry already exists: {new_slug}")
        new_category_slug = payload.category_slug or entry.category_slug
        self._find_category(state, new_category_slug)

        entry.title = (payload.title or entry.title).strip()
        entry.slug = new_slug
        entry.category_slug = new_category_slug
        entry.path = _entry_path(new_category_slug, new_slug)
        entry.summary = (payload.summary or entry.summary).strip()
        if payload.use_when is not None:
            entry.use_when = payload.use_when
        if payload.do_this is not None:
            entry.do_this = payload.do_this
        if payload.checklist is not None:
            entry.checklist = payload.checklist
        if payload.anti_patterns is not None:
            entry.anti_patterns = payload.anti_patterns
        if payload.read_next is not None:
            entry.read_next = payload.read_next
        if payload.source_videos is not None:
            entry.source_videos = payload.source_videos

        if new_slug != old_slug:
            for other_entry in state.entries:
                other_entry.read_next = [new_slug if item == old_slug else item for item in other_entry.read_next]
        self._validate_read_next(state, entry.read_next, current_slug=new_slug)
        self._write_state(state, old_paths=[old_path])
        return self.get_entry(new_slug)

    def delete_entry(self, slug: str) -> StoredHandbookEntry:
        state = self._load_state()
        entry = self._find_entry(state, slug)
        old_path = _entry_path(entry.category_slug, entry.slug)
        state.entries = [item for item in state.entries if item.slug != slug]
        for category in state.categories:
            category.entry_slugs = [item for item in category.entry_slugs if item != slug]
        for remaining_entry in state.entries:
            remaining_entry.read_next = [item for item in remaining_entry.read_next if item != slug]
        self._write_state(state, old_paths=[old_path])
        return entry

    def _load_state(self) -> _HandbookState:
        manifest = self.load_manifest()
        categories = [
            StoredHandbookCategory(
                title=category.title,
                slug=category.slug,
                path=category.path,
                description=category.description,
                when_to_read=category.when_to_read,
                core_terms=category.core_terms,
                entry_slugs=[entry.slug for entry in category.entries],
            )
            for category in manifest.categories
        ]
        entries = [self._entry_from_manifest(entry) for entry in manifest.entries]
        return _HandbookState(manifest=manifest, categories=categories, entries=entries)

    def _entry_from_manifest(self, entry: HandbookManifestEntry) -> StoredHandbookEntry:
        sections: dict[str, str] = {}
        path = self.root / entry.path
        if path.exists():
            sections = _parse_markdown_sections(path.read_text(encoding="utf-8"))
        return StoredHandbookEntry(
            title=entry.title,
            slug=entry.slug,
            category_slug=entry.category_slug,
            path=entry.path,
            summary=sections.get("Summary") or entry.summary,
            use_when=_parse_markdown_list(sections.get("Use When", "")),
            do_this=_parse_markdown_list(sections.get("Do This", ""), numbered=True),
            checklist=_parse_markdown_list(sections.get("Checklist", "")),
            anti_patterns=_parse_markdown_list(sections.get("Anti-Patterns", "")),
            read_next=entry.read_next,
            source_videos=entry.source_videos,
        )

    def _write_state(self, state: _HandbookState, *, old_paths: list[str] | None = None) -> None:
        old_paths = old_paths or []
        self._validate_state(state)
        category_by_slug = {category.slug: category for category in state.categories}
        entry_by_slug = {entry.slug: entry for entry in state.entries}

        for category in state.categories:
            category.path = _category_path(category.slug)
            existing = [
                entry_slug
                for entry_slug in category.entry_slugs
                if entry_slug in entry_by_slug and entry_by_slug[entry_slug].category_slug == category.slug
            ]
            additions = [
                entry.slug
                for entry in state.entries
                if entry.category_slug == category.slug and entry.slug not in existing
            ]
            category.entry_slugs = existing + additions

        for entry in state.entries:
            entry.path = _entry_path(entry.category_slug, entry.slug)

        state.manifest.categories = [
            HandbookManifestCategory(
                title=category.title,
                slug=category.slug,
                path=category.path or _category_path(category.slug),
                description=category.description,
                when_to_read=category.when_to_read,
                core_terms=category.core_terms,
                entries=[
                    HandbookEntryRef(slug=entry_slug, path=entry_by_slug[entry_slug].path or _entry_path(category.slug, entry_slug))
                    for entry_slug in category.entry_slugs
                    if entry_slug in entry_by_slug
                ],
            )
            for category in state.categories
        ]
        state.manifest.entries = [
            HandbookManifestEntry(
                title=entry.title,
                slug=entry.slug,
                category_slug=entry.category_slug,
                path=entry.path or _entry_path(entry.category_slug, entry.slug),
                summary=entry.summary,
                read_next=entry.read_next,
                source_videos=entry.source_videos,
            )
            for entry in state.entries
        ]
        state.manifest.category_count = len(state.manifest.categories)
        state.manifest.entry_count = len(state.manifest.entries)
        state.manifest.source_video_count = _source_video_count(state.manifest)

        blueprint = self._blueprint_from_state(state)
        categories_for_render = {category.category_slug: category for category in blueprint.categories}
        entries_for_render = {entry.entry_slug: entry for entry in blueprint.entries}

        _write_text(self.root / state.manifest.guide_path, render_guide_markdown(blueprint))
        _write_text(self.root / state.manifest.index_path, render_index_markdown(blueprint))
        _write_text(self.root / state.manifest.entry_skill_path, render_entry_skill_markdown(blueprint))
        source_index = _render_source_index_from_manifest(state.manifest)
        if source_index is not None:
            _write_text(self.root / state.manifest.source_index_path, source_index)

        for category in blueprint.categories:
            entries = [
                entries_for_render[entry_slug]
                for entry_slug in category.entry_slugs
                if entry_slug in entries_for_render
            ]
            _write_text(
                self.root / _category_path(category.category_slug),
                render_category_markdown(category, entries=entries),
            )

        for entry in blueprint.entries:
            _write_text(
                self.root / _entry_path(entry.category_slug, entry.entry_slug),
                render_entry_markdown(
                    entry,
                    categories=categories_for_render,
                    entries_by_slug=entries_for_render,
                ),
            )

        _write_text(
            self.manifest_path,
            json.dumps(state.manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        )

        current_paths = {state.manifest.guide_path, state.manifest.index_path, state.manifest.entry_skill_path, state.manifest.source_index_path}
        current_paths.update(category.path for category in state.manifest.categories)
        current_paths.update(entry.path for entry in state.manifest.entries)
        for old_path in old_paths:
            _delete_if_stale(self.root, old_path, current_paths)

    def _blueprint_from_state(self, state: _HandbookState) -> HandbookBlueprint:
        return HandbookBlueprint(
            book_title=state.manifest.book_title,
            book_slug=state.manifest.book_slug,
            description=state.manifest.description,
            audience=state.manifest.audience,
            routing_rules=state.manifest.routing_rules,
            categories=[
                HandbookCategory(
                    title=category.title,
                    category_slug=category.slug,
                    description=category.description,
                    when_to_read=category.when_to_read,
                    core_terms=category.core_terms,
                    entry_slugs=category.entry_slugs,
                )
                for category in state.categories
            ],
            entries=[
                HandbookEntry(
                    title=entry.title,
                    entry_slug=entry.slug,
                    category_slug=entry.category_slug,
                    summary=entry.summary,
                    use_when=entry.use_when or ["Use this entry when the task matches its summary."],
                    do_this=entry.do_this or ["State the relevant constraints before applying the guidance."],
                    checklist=entry.checklist or ["Confirm the result is grounded in the selected handbook entry."],
                    anti_patterns=entry.anti_patterns or ["Do not apply the entry without matching it to the current task."],
                    read_next=entry.read_next,
                    source_video_ids=entry.source_videos,
                )
                for entry in state.entries
            ],
            glossary=[],
        )

    def _validate_state(self, state: _HandbookState) -> None:
        category_slugs = [category.slug for category in state.categories]
        entry_slugs = [entry.slug for entry in state.entries]
        if len(category_slugs) != len(set(category_slugs)):
            raise ValueError("Duplicate category slug in handbook state.")
        if len(entry_slugs) != len(set(entry_slugs)):
            raise ValueError("Duplicate entry slug in handbook state.")
        category_set = set(category_slugs)
        entry_set = set(entry_slugs)
        for entry in state.entries:
            if entry.category_slug not in category_set:
                raise ValueError(f"Entry {entry.slug} references missing category: {entry.category_slug}")
            unknown_read_next = [item for item in entry.read_next if item not in entry_set]
            if unknown_read_next:
                raise ValueError(f"Entry {entry.slug} references missing read_next entries: {unknown_read_next}")
            if entry.slug in entry.read_next:
                raise ValueError(f"Entry {entry.slug} cannot read_next itself.")

    def _validate_read_next(self, state: _HandbookState, read_next: list[str], *, current_slug: str) -> None:
        known_entries = {entry.slug for entry in state.entries}
        known_entries.add(current_slug)
        unknown = [slug for slug in read_next if slug not in known_entries]
        if unknown:
            raise ValueError(f"Unknown read_next entries: {unknown}")
        if current_slug in read_next:
            raise ValueError("An entry cannot read_next itself.")

    def _find_category(self, state: _HandbookState, slug: str) -> StoredHandbookCategory:
        for category in state.categories:
            if category.slug == slug:
                return category
        raise KeyError(f"Unknown category: {slug}")

    def _find_entry(self, state: _HandbookState, slug: str) -> StoredHandbookEntry:
        for entry in state.entries:
            if entry.slug == slug:
                return entry
        raise KeyError(f"Unknown entry: {slug}")
