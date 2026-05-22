from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
import json
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .models import VideoSummaryDocument
from .summarizer import ChatGateway
from .utils import safe_slug


class HandbookGlossaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str = Field(..., min_length=1)
    definition: str = Field(..., min_length=1)


class HandbookCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    category_slug: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    when_to_read: list[str] = Field(default_factory=list)
    core_terms: list[str] = Field(default_factory=list)
    entry_slugs: list[str] = Field(default_factory=list)


class HandbookEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    entry_slug: str = Field(..., min_length=1)
    category_slug: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    use_when: list[str] = Field(default_factory=list)
    do_this: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    read_next: list[str] = Field(default_factory=list)
    source_video_ids: list[str] = Field(default_factory=list)


def _stringify_routing_rule_part(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return ", ".join(part for part in (_stringify_routing_rule_part(item) for item in value) if part)
    if isinstance(value, dict):
        return ", ".join(
            f"{key}={part}"
            for key, part in (
                (str(key).strip(), _stringify_routing_rule_part(item))
                for key, item in value.items()
            )
            if key and part
        )
    return str(value).strip()


def _normalize_routing_rule(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        condition = _stringify_routing_rule_part(
            value.get("condition") or value.get("when") or value.get("if")
        )
        route_target = _stringify_routing_rule_part(
            value.get("route_to")
            or value.get("route")
            or value.get("target")
            or value.get("category")
            or value.get("entry")
            or value.get("then")
        )
        rationale = _stringify_routing_rule_part(
            value.get("reason") or value.get("note") or value.get("because")
        )
        fallback = _stringify_routing_rule_part(
            {
                key: item
                for key, item in value.items()
                if key not in {"condition", "when", "if", "route_to", "route", "target", "category", "entry", "then", "reason", "note", "because"}
            }
        )

        parts: list[str] = []
        if condition:
            parts.append(f"If {condition}")
        if route_target:
            route_prefix = "route to" if parts else "Route to"
            parts.append(f"{route_prefix} {route_target}")
        if rationale:
            parts.append(f"because {rationale}")
        if fallback:
            parts.append(f"details: {fallback}")
        if parts:
            return "; ".join(parts)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return _stringify_routing_rule_part(value)


class HandbookBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    book_title: str = Field(..., min_length=1)
    book_slug: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    routing_rules: list[str] = Field(default_factory=list)
    categories: list[HandbookCategory] = Field(default_factory=list)
    entries: list[HandbookEntry] = Field(default_factory=list)
    glossary: list[HandbookGlossaryItem] = Field(default_factory=list)

    @field_validator("routing_rules", mode="before")
    @classmethod
    def normalize_routing_rules(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (str, dict)):
            raw_items = [value]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            raw_items = list(value)
        else:
            raw_items = [value]
        normalized = [
            rule
            for rule in (_normalize_routing_rule(item) for item in raw_items)
            if rule
        ]
        return normalized


def _unique_preserve_order(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def _fallback_title(raw_value: str, *, default: str) -> str:
    text = str(raw_value or "").strip()
    return text or default


def _append_frontmatter_list(lines: list[str], key: str, items: Sequence[str]) -> None:
    if not items:
        lines.append(f"{key}: []")
        return
    lines.append(f"{key}:")
    for item in items:
        lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")


def _entry_path(entry: HandbookEntry) -> PurePosixPath:
    return PurePosixPath("categories") / entry.category_slug / f"{entry.entry_slug}.md"


def _category_path(category: HandbookCategory) -> PurePosixPath:
    return PurePosixPath("categories") / category.category_slug / "CATEGORY.md"


def _evidence_path(video_id: str) -> PurePosixPath:
    return PurePosixPath("evidence") / f"{video_id}.md"


def _relpath(target: PurePosixPath, start: PurePosixPath) -> str:
    start_parts = start.parts
    target_parts = target.parts
    common = 0
    for start_part, target_part in zip(start_parts, target_parts):
        if start_part != target_part:
            break
        common += 1
    upward = [".."] * (len(start_parts) - common)
    downward = list(target_parts[common:])
    combined = upward + downward
    if not combined:
        return "."
    relative = "/".join(combined)
    if not upward and not relative.startswith("."):
        return f"./{relative}"
    return relative


def format_summary_document(document: VideoSummaryDocument) -> str:
    summary = document.summary
    lines = [
        f"# Video {document.sequence}: {document.title}",
        f"- video_id: {document.video_id}",
        f"- published_at: {document.published_at or 'unknown'}",
        f"- source_video_url: {summary.source_video_url}",
        f"- transcript_language: {summary.transcript_language}",
        "## summary_zh",
        summary.summary_zh,
        "## key_points",
    ]
    lines.extend(f"- {item}" for item in summary.key_points)
    lines.extend(["## action_steps"])
    lines.extend(f"1. {item}" for item in summary.action_steps)
    lines.extend(["## tools_or_resources"])
    if summary.tools_or_resources:
        lines.extend(f"- {item}" for item in summary.tools_or_resources)
    else:
        lines.append("- none")
    lines.extend(["## notable_segments"])
    if summary.notable_segments:
        for item in summary.notable_segments:
            lines.append(f"- {item.timestamp} | {item.note} | {item.excerpt}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def chunk_documents(documents: Sequence[str], *, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for document in documents:
        additional = len(document) + (2 if current else 0)
        if current and current_size + additional > max_chars:
            chunks.append("\n\n".join(current))
            current = [document]
            current_size = len(document)
            continue
        current.append(document)
        current_size += additional
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _fallback_blueprint(
    documents: Sequence[VideoSummaryDocument],
    *,
    channel_title: str | None,
) -> HandbookBlueprint:
    source_video_ids = [document.video_id for document in documents[:5]]
    repeated_points: list[str] = []
    repeated_steps: list[str] = []
    for document in documents:
        repeated_points.extend(document.summary.key_points[:2])
        repeated_steps.extend(document.summary.action_steps[:2])

    category = HandbookCategory(
        title="Overview",
        category_slug="overview",
        description="默认入口，用于快速理解该频道的核心方法和常见工作流。",
        when_to_read=[
            "任务与该频道主题相关，但还不知道应该先读哪一页时。",
            "需要先建立频道整体语境，再决定深入哪个子主题时。",
        ],
        core_terms=_unique_preserve_order(repeated_points[:4])[:4],
        entry_slugs=["channel-overview"],
    )
    entry = HandbookEntry(
        title="Channel Overview",
        entry_slug="channel-overview",
        category_slug=category.category_slug,
        summary=(
            f"{channel_title or '该频道'} 的 Patchouli handbook 默认入口。"
            "先用这一页建立整体判断，再决定是否跳转到更具体的流程页。"
        ),
        use_when=[
            "需要快速了解这个频道反复强调的问题拆解方式时。",
            "当前素材不足以稳定拆出多个专题时。",
        ],
        do_this=_unique_preserve_order(repeated_steps[:4])[:4]
        or ["先概括任务目标与约束。", "再从整理稿中提炼重复出现的关键原则。"],
        checklist=_unique_preserve_order(repeated_points[:4])[:4]
        or ["是否已经识别出频道反复强调的判断标准。", "是否保留了后续继续展开的入口。"],
        anti_patterns=[
            "不要把所有视频细节直接复制进入口页。",
            "不要在没有明确证据时捏造不存在的工作流。",
        ],
        read_next=[],
        source_video_ids=source_video_ids,
    )
    glossary = [
        HandbookGlossaryItem(
            term="Patchouli handbook",
            definition="面向 AI agent 的静态参考手册，通过分类和词条逐步展开知识。",
        )
    ]
    return HandbookBlueprint(
        book_title=f"{channel_title or 'Channel'} Patchouli Handbook",
        book_slug=safe_slug(f"{channel_title or 'channel'}-patchouli-handbook", max_length=80),
        description="从频道整理稿蒸馏出的递进式参考手册。",
        audience="需要复用该频道经验的 AI agent。",
        routing_rules=[
            "先读 INDEX.md，再根据任务选择单一 category。",
            "初次展开时最多只打开 1-2 个 entry。",
            "只有在 entry 证据不足或出现冲突时才继续打开 evidence 页面。",
        ],
        categories=[category],
        entries=[entry],
        glossary=glossary,
    )


def normalize_blueprint(
    blueprint: HandbookBlueprint,
    *,
    documents: Sequence[VideoSummaryDocument],
    channel_title: str | None,
) -> HandbookBlueprint:
    if not blueprint.categories or not blueprint.entries:
        blueprint = _fallback_blueprint(documents, channel_title=channel_title)

    known_video_ids = [document.video_id for document in documents]
    known_video_id_set = set(known_video_ids)
    default_source_ids = known_video_ids[: min(5, len(known_video_ids))]
    book_title = _fallback_title(
        blueprint.book_title,
        default=f"{channel_title or 'Channel'} Patchouli Handbook",
    )
    normalized_book_slug = safe_slug(
        blueprint.book_slug or f"{book_title}-patchouli-handbook",
        max_length=80,
    )
    if normalized_book_slug == "job":
        normalized_book_slug = safe_slug(f"{channel_title or 'channel'}-patchouli-handbook", max_length=80)
    if normalized_book_slug == "job":
        normalized_book_slug = "patchouli-handbook"

    category_map: dict[str, HandbookCategory] = {}
    category_order: list[str] = []
    for raw_category in blueprint.categories:
        title = _fallback_title(raw_category.title, default="Overview")
        slug = safe_slug(raw_category.category_slug or title, max_length=80)
        if slug == "job":
            slug = safe_slug(title, max_length=80)
        if slug == "job":
            slug = "overview"
        if slug in category_map:
            existing = category_map[slug]
            category_map[slug] = HandbookCategory(
                title=existing.title,
                category_slug=slug,
                description=existing.description if existing.description else raw_category.description,
                when_to_read=_unique_preserve_order(existing.when_to_read + raw_category.when_to_read),
                core_terms=_unique_preserve_order(existing.core_terms + raw_category.core_terms),
                entry_slugs=_unique_preserve_order(existing.entry_slugs + raw_category.entry_slugs),
            )
            continue
        category_order.append(slug)
        category_map[slug] = HandbookCategory(
            title=title,
            category_slug=slug,
            description=_fallback_title(
                raw_category.description,
                default=f"{title} 相关的常见问题和判断路径。",
            ),
            when_to_read=_unique_preserve_order(raw_category.when_to_read),
            core_terms=_unique_preserve_order(raw_category.core_terms),
            entry_slugs=_unique_preserve_order(raw_category.entry_slugs),
        )

    if not category_order:
        fallback = _fallback_blueprint(documents, channel_title=channel_title)
        return normalize_blueprint(fallback, documents=documents, channel_title=channel_title)

    entry_map: dict[str, HandbookEntry] = {}
    entry_order: list[str] = []
    for raw_entry in blueprint.entries:
        title = _fallback_title(raw_entry.title, default="Overview Entry")
        preferred_category_slug = safe_slug(raw_entry.category_slug, max_length=80)
        if preferred_category_slug not in category_map:
            preferred_category_slug = category_order[0]
        base_slug = safe_slug(raw_entry.entry_slug or title, max_length=80)
        if base_slug == "job":
            base_slug = safe_slug(title, max_length=80)
        if base_slug == "job":
            base_slug = "entry"
        slug = base_slug
        if slug in entry_map and (
            entry_map[slug].title != title or entry_map[slug].category_slug != preferred_category_slug
        ):
            suffix = 2
            while slug in entry_map:
                slug = safe_slug(f"{preferred_category_slug}-{base_slug}-{suffix}", max_length=80)
                suffix += 1
        if slug in entry_map:
            existing = entry_map[slug]
            entry_map[slug] = HandbookEntry(
                title=existing.title,
                entry_slug=slug,
                category_slug=existing.category_slug,
                summary=existing.summary if existing.summary else raw_entry.summary,
                use_when=_unique_preserve_order(existing.use_when + raw_entry.use_when),
                do_this=_unique_preserve_order(existing.do_this + raw_entry.do_this),
                checklist=_unique_preserve_order(existing.checklist + raw_entry.checklist),
                anti_patterns=_unique_preserve_order(existing.anti_patterns + raw_entry.anti_patterns),
                read_next=_unique_preserve_order(existing.read_next + raw_entry.read_next),
                source_video_ids=_unique_preserve_order(existing.source_video_ids + raw_entry.source_video_ids),
            )
            continue
        entry_order.append(slug)
        entry_map[slug] = HandbookEntry(
            title=title,
            entry_slug=slug,
            category_slug=preferred_category_slug,
            summary=_fallback_title(
                raw_entry.summary,
                default=f"{title} 的执行页，负责把频道经验转成可操作步骤。",
            ),
            use_when=_unique_preserve_order(raw_entry.use_when),
            do_this=_unique_preserve_order(raw_entry.do_this),
            checklist=_unique_preserve_order(raw_entry.checklist),
            anti_patterns=_unique_preserve_order(raw_entry.anti_patterns),
            read_next=_unique_preserve_order(raw_entry.read_next),
            source_video_ids=_unique_preserve_order(raw_entry.source_video_ids),
        )

    if not entry_order:
        fallback = _fallback_blueprint(documents, channel_title=channel_title)
        return normalize_blueprint(fallback, documents=documents, channel_title=channel_title)

    normalized_entries: list[HandbookEntry] = []
    for slug in entry_order:
        entry = entry_map[slug]
        source_video_ids = [video_id for video_id in entry.source_video_ids if video_id in known_video_id_set]
        if not source_video_ids:
            source_video_ids = default_source_ids
        normalized_entries.append(
            HandbookEntry(
                title=entry.title,
                entry_slug=entry.entry_slug,
                category_slug=entry.category_slug if entry.category_slug in category_map else category_order[0],
                summary=entry.summary,
                use_when=entry.use_when or ["当任务与该条目描述的问题形态一致时。"],
                do_this=entry.do_this or ["先明确目标与约束。", "再用该条目的判断顺序推进任务。"],
                checklist=entry.checklist or ["是否保留了结构化结论。"],
                anti_patterns=entry.anti_patterns or ["不要跳过证据和约束直接下结论。"],
                read_next=entry.read_next,
                source_video_ids=source_video_ids,
            )
        )

    entry_slug_set = {entry.entry_slug for entry in normalized_entries}
    category_entry_map: dict[str, list[str]] = defaultdict(list)
    for entry in normalized_entries:
        category_entry_map[entry.category_slug].append(entry.entry_slug)

    repaired_entries: list[HandbookEntry] = []
    for entry in normalized_entries:
        read_next = [
            slug for slug in _unique_preserve_order(entry.read_next)
            if slug in entry_slug_set and slug != entry.entry_slug
        ]
        if not read_next:
            siblings = [slug for slug in category_entry_map[entry.category_slug] if slug != entry.entry_slug]
            if siblings:
                read_next = siblings[:1]
        repaired_entries.append(entry.model_copy(update={"read_next": read_next}))
    normalized_entries = repaired_entries

    normalized_categories: list[HandbookCategory] = []
    for slug in category_order:
        category = category_map[slug]
        entry_slugs = category_entry_map.get(slug, [])
        if not entry_slugs:
            continue
        normalized_categories.append(
            HandbookCategory(
                title=category.title,
                category_slug=slug,
                description=category.description,
                when_to_read=category.when_to_read or ["当任务属于该主题范围时。"],
                core_terms=category.core_terms[:8],
                entry_slugs=entry_slugs,
            )
        )

    if not normalized_categories or not normalized_entries:
        fallback = _fallback_blueprint(documents, channel_title=channel_title)
        return normalize_blueprint(fallback, documents=documents, channel_title=channel_title)

    glossary_map: dict[str, HandbookGlossaryItem] = {}
    glossary_order: list[str] = []
    for raw_item in blueprint.glossary:
        term = str(raw_item.term).strip()
        definition = str(raw_item.definition).strip()
        if not term or not definition:
            continue
        key = term.casefold()
        if key in glossary_map:
            continue
        glossary_order.append(key)
        glossary_map[key] = HandbookGlossaryItem(term=term, definition=definition)
    if not glossary_order:
        for category in normalized_categories:
            for term in category.core_terms:
                key = term.casefold()
                if key in glossary_map:
                    continue
                glossary_order.append(key)
                glossary_map[key] = HandbookGlossaryItem(
                    term=term,
                    definition="该术语来自频道整理稿，是进入对应 category 前需要掌握的上下文。",
                )
    glossary = [glossary_map[key] for key in glossary_order[:32]]

    routing_rules = _unique_preserve_order(blueprint.routing_rules)
    if not routing_rules:
        routing_rules = [
            "先读 INDEX.md，再锁定最匹配的单一 category。",
            "第一次只展开 1-2 个 entry，避免过早加载整本手册。",
            "只有在 entry 信息不足、需要举例或校验冲突时才继续读 evidence 页面。",
        ]

    return HandbookBlueprint(
        book_title=book_title,
        book_slug=normalized_book_slug,
        description=_fallback_title(
            blueprint.description,
            default="从频道整理稿蒸馏出的递进式 Patchouli handbook。",
        ),
        audience=_fallback_title(
            blueprint.audience,
            default="需要复用该频道知识的 AI agent。",
        ),
        routing_rules=routing_rules,
        categories=normalized_categories,
        entries=normalized_entries,
        glossary=glossary,
    )


def render_manifest(
    blueprint: HandbookBlueprint,
    *,
    documents: Sequence[VideoSummaryDocument],
) -> dict[str, Any]:
    entry_map = {entry.entry_slug: entry for entry in blueprint.entries}
    categories = []
    for category in blueprint.categories:
        categories.append(
            {
                "title": category.title,
                "slug": category.category_slug,
                "path": str(_category_path(category)),
                "description": category.description,
                "when_to_read": category.when_to_read,
                "core_terms": category.core_terms,
                "entries": [
                    {
                        "slug": entry_slug,
                        "path": str(_entry_path(entry_map[entry_slug])),
                    }
                    for entry_slug in category.entry_slugs
                    if entry_slug in entry_map
                ],
            }
        )

    entries = [
        {
            "title": entry.title,
            "slug": entry.entry_slug,
            "category_slug": entry.category_slug,
            "path": str(_entry_path(entry)),
            "summary": entry.summary,
            "read_next": entry.read_next,
            "source_videos": entry.source_video_ids,
        }
        for entry in blueprint.entries
    ]

    source_videos = [
        {
            "video_id": document.video_id,
            "title": document.title,
            "published_at": document.published_at,
            "source_video_url": document.summary.source_video_url,
            "evidence_path": str(_evidence_path(document.video_id)),
        }
        for document in documents
    ]

    return {
        "book_title": blueprint.book_title,
        "book_slug": blueprint.book_slug,
        "description": blueprint.description,
        "audience": blueprint.audience,
        "routing_rules": blueprint.routing_rules,
        "categories": categories,
        "entries": entries,
        "source_videos": source_videos,
        "guide_path": "GUIDE.md",
        "entry_skill_path": "entry_skill/SKILL.md",
        "index_path": "INDEX.md",
        "glossary_path": "references/glossary.md",
        "source_index_path": "references/source_index.md",
    }


def render_index_markdown(blueprint: HandbookBlueprint) -> str:
    entry_map = {entry.entry_slug: entry for entry in blueprint.entries}
    lines = [
        f"# {blueprint.book_title}",
        "",
        blueprint.description,
        "",
        "## Audience",
        blueprint.audience,
        "",
        "## Routing Rules",
    ]
    lines.extend(f"1. {rule}" for rule in blueprint.routing_rules)
    lines.extend(["", "## Categories"])
    for category in blueprint.categories:
        lines.extend(
            [
                "",
                f"### {category.title}",
                category.description,
                "",
                "When to read:",
            ]
        )
        lines.extend(f"- {item}" for item in category.when_to_read)
        if category.core_terms:
            lines.extend(["", "Core terms:"])
            lines.extend(f"- {item}" for item in category.core_terms)
        lines.extend(["", "Entries:"])
        for entry_slug in category.entry_slugs:
            entry = entry_map.get(entry_slug)
            if not entry:
                continue
            lines.append(f"- [{entry.title}]({str(_entry_path(entry))})")
    lines.extend(
        [
            "",
            "## References",
            "- [Guide](GUIDE.md)",
            "- [Glossary](references/glossary.md)",
            "- [Source Index](references/source_index.md)",
            "- [Entry Skill](entry_skill/SKILL.md)",
        ]
    )
    return "\n".join(lines)


def render_guide_markdown(blueprint: HandbookBlueprint) -> str:
    lines = [
        f"# {blueprint.book_title} Guide",
        "",
        "This guide explains how an AI agent should use this handbook as a thick reference system, not as a single behavior script.",
        "",
        "## Mental Model",
        "- `entry_skill/SKILL.md` is the lightweight activation layer.",
        "- `INDEX.md` is the map for routing a user request to the right category.",
        "- `categories/<category_slug>/CATEGORY.md` narrows the local search space.",
        "- `categories/<category_slug>/<entry_slug>.md` contains reusable guidance, checks, and failure modes.",
        "- `references/glossary.md` defines terms that apply across entries.",
        "- `references/source_index.md` and `evidence/<source_id>.md` ground guidance in source material.",
        "",
        "## Reading Protocol",
        "1. Start with `entry_skill/SKILL.md` only to confirm the handbook is relevant.",
        "2. Read `INDEX.md` and choose the smallest plausible set of categories.",
        "3. Open one category page and select one or two entries before reading deeper.",
        "4. Use `read_next` links when the first entry exposes a nearby dependency.",
        "5. Open evidence pages only for examples, conflicts, source checks, or high-stakes claims.",
        "",
        "## Answer Protocol",
        "- State the category and entry files that shaped the answer when the user needs traceability.",
        "- Convert handbook guidance into the user's concrete context instead of restating sections verbatim.",
        "- Separate source-backed claims from interpretation when the answer depends on evidence pages.",
        "- Prefer focused, actionable recommendations over broad summaries of the whole book.",
        "- If no entry fits, say so and use the closest category only as loose background.",
        "",
        "## Maintenance Protocol",
        "- Add a category only when several entries need a shared routing surface.",
        "- Add an entry when there is a stable reusable judgment pattern, not just a one-off note.",
        "- Keep each entry self-contained enough to answer a narrow task after it is selected.",
        "- Link related entries with `read_next` instead of duplicating the same guidance.",
        "- Add evidence when a claim needs provenance, concrete examples, or conflict resolution.",
        "",
        "## Routing Rules",
    ]
    if blueprint.routing_rules:
        lines.extend(f"1. {rule}" for rule in blueprint.routing_rules)
    else:
        lines.append("1. Read `INDEX.md`, select the closest category, then expand only the entries needed for the task.")
    return "\n".join(lines)


def render_category_markdown(
    category: HandbookCategory,
    *,
    entries: Sequence[HandbookEntry],
) -> str:
    lines = [
        "---",
        f"title: {json.dumps(category.title, ensure_ascii=False)}",
        f"category_slug: {json.dumps(category.category_slug, ensure_ascii=False)}",
        "---",
        "",
        f"# {category.title}",
        "",
        category.description,
        "",
        "## When To Read",
    ]
    lines.extend(f"- {item}" for item in category.when_to_read)
    lines.extend(["", "## Core Terms"])
    if category.core_terms:
        lines.extend(f"- {item}" for item in category.core_terms)
    else:
        lines.append("- See the glossary for channel-wide terminology.")
    lines.extend(["", "## Next Entries"])
    lines.extend(f"- [{entry.title}](./{entry.entry_slug}.md)" for entry in entries)
    return "\n".join(lines)


def render_entry_markdown(
    entry: HandbookEntry,
    *,
    categories: dict[str, HandbookCategory],
    entries_by_slug: dict[str, HandbookEntry],
) -> str:
    entry_path = _entry_path(entry)
    lines = [
        "---",
        f"title: {json.dumps(entry.title, ensure_ascii=False)}",
        f"entry_slug: {json.dumps(entry.entry_slug, ensure_ascii=False)}",
        f"category_slug: {json.dumps(entry.category_slug, ensure_ascii=False)}",
    ]
    _append_frontmatter_list(lines, "source_videos", entry.source_video_ids)
    _append_frontmatter_list(lines, "read_next", entry.read_next)
    lines.extend(
        [
            "---",
            "",
            f"# {entry.title}",
            "",
            f"Category: {categories[entry.category_slug].title}",
            "",
            "## Summary",
            entry.summary,
            "",
            "## Use When",
        ]
    )
    lines.extend(f"- {item}" for item in entry.use_when)
    lines.extend(["", "## Do This"])
    lines.extend(f"1. {item}" for item in entry.do_this)
    lines.extend(["", "## Checklist"])
    lines.extend(f"- {item}" for item in entry.checklist)
    lines.extend(["", "## Anti-Patterns"])
    lines.extend(f"- {item}" for item in entry.anti_patterns)
    lines.extend(["", "## Read Next"])
    if entry.read_next:
        for slug in entry.read_next:
            target = entries_by_slug.get(slug)
            if not target:
                continue
            relative_path = _relpath(_entry_path(target), entry_path.parent)
            lines.append(f"- [{target.title}]({relative_path})")
    else:
        lines.append("- No additional entry is required for the first pass.")
    lines.extend(["", "## Source Videos"])
    for video_id in entry.source_video_ids:
        lines.append(f"- [{video_id}]({_relpath(_evidence_path(video_id), entry_path.parent)})")
    return "\n".join(lines)


def render_glossary_markdown(blueprint: HandbookBlueprint) -> str:
    lines = [
        "# Glossary",
        "",
        "在深入具体 entry 前，先在这里建立频道反复出现的术语语境。",
    ]
    for item in blueprint.glossary:
        lines.extend(
            [
                "",
                f"## {item.term}",
                item.definition,
            ]
        )
    return "\n".join(lines)


def render_source_index_markdown(
    blueprint: HandbookBlueprint,
    *,
    documents: Sequence[VideoSummaryDocument],
) -> str:
    entry_by_video: dict[str, list[HandbookEntry]] = defaultdict(list)
    for entry in blueprint.entries:
        for video_id in entry.source_video_ids:
            entry_by_video[video_id].append(entry)

    lines = [
        "# Source Index",
        "",
        "本索引把 handbook 条目回溯到具体视频证据页。",
    ]
    for document in documents:
        lines.extend(
            [
                "",
                f"## {document.sequence}. {document.title}",
                f"- video_id: {document.video_id}",
                f"- published_at: {document.published_at or 'unknown'}",
                f"- source_video_url: {document.summary.source_video_url}",
                f"- evidence: [{document.video_id}]({_evidence_path(document.video_id)})",
            ]
        )
        if entry_by_video.get(document.video_id):
            lines.append("- used_by_entries:")
            for entry in entry_by_video[document.video_id]:
                lines.append(
                    f"  - [{entry.title}]({_entry_path(entry)})"
                )
    return "\n".join(lines)


def render_evidence_markdown(document: VideoSummaryDocument) -> str:
    summary = document.summary
    lines = [
        f"# Evidence: {document.title}",
        "",
        "仅在 entry 无法覆盖细节、需要举例或冲突校验时再阅读此页。",
        "",
        "## Metadata",
        f"- video_id: {document.video_id}",
        f"- published_at: {document.published_at or 'unknown'}",
        f"- transcript_language: {summary.transcript_language}",
        f"- source_video_url: {summary.source_video_url}",
        "",
        "## Summary",
        summary.summary_zh,
        "",
        "## Key Points",
    ]
    lines.extend(f"- {item}" for item in summary.key_points)
    lines.extend(["", "## Action Steps"])
    lines.extend(f"1. {item}" for item in summary.action_steps)
    lines.extend(["", "## Notable Segments"])
    if summary.notable_segments:
        for segment in summary.notable_segments:
            lines.append(f"- {segment.timestamp} | {segment.note} | {segment.excerpt}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def render_entry_skill_markdown(blueprint: HandbookBlueprint) -> str:
    lines = [
        "---",
        f"name: {json.dumps(blueprint.book_slug, ensure_ascii=False)}",
        f"description: {json.dumps(f'Navigate the {blueprint.book_title} Patchouli handbook.', ensure_ascii=False)}",
        "---",
        "",
        f"# {blueprint.book_title} Entry Skill",
        "",
        "## Use When",
        "- 任务与该频道主题相关，需要借助 handbook 找到可执行经验时。",
        "- 需要先选最相关的 category 和 entry，而不是一次性加载所有资料时。",
        "",
        "## Workflow",
        "1. Read `../GUIDE.md` when the task requires more than a quick lookup.",
        "2. Read `../INDEX.md` to identify the best matching category.",
        "3. Open exactly one category page under `../categories/<category_slug>/CATEGORY.md`.",
        "4. Expand only 1-2 entry pages under the selected category.",
        "5. Read `../evidence/<video_id>.md` only when an entry lacks detail, needs an example, or presents a conflict.",
        "",
        "## Navigation Rules",
    ]
    lines.extend(f"- {rule}" for rule in blueprint.routing_rules)
    lines.extend(
        [
            "",
            "## Output Requirements",
            "- State which category and entry files were used.",
            "- Keep the answer grounded in the selected entries; do not restate the entire handbook.",
        ]
    )
    return "\n".join(lines)


class HandbookBuilder:
    def __init__(self, gateway: ChatGateway, *, max_chars: int = 18000) -> None:
        self.gateway = gateway
        self.max_chars = max_chars

    def build(
        self,
        documents: Sequence[VideoSummaryDocument],
        *,
        channel_title: str | None,
    ) -> HandbookBlueprint:
        if not documents:
            raise ValueError("No summarized videos are available for handbook building.")

        formatted_documents = [format_summary_document(document) for document in documents]
        chunks = chunk_documents(formatted_documents, max_chars=self.max_chars)
        if len(chunks) == 1:
            blueprint = self._build_chunk(chunks[0], channel_title=channel_title)
        else:
            partials = [
                self._build_chunk(chunk, channel_title=channel_title).model_dump()
                for chunk in chunks
            ]
            blueprint = self._merge_partials(partials, channel_title=channel_title)
        return normalize_blueprint(blueprint, documents=documents, channel_title=channel_title)

    def _build_chunk(self, chunk: str, *, channel_title: str | None) -> HandbookBlueprint:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are building a Patchouli-style handbook blueprint for AI agents from a YouTube channel knowledge base. "
                    "Output JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Based on the normalized video summaries below, design one coherent Patchouli handbook. "
                    "Favor repeated workflows, recurring judgment patterns, and compact progressive disclosure. "
                    "Use lowercase ASCII hyphen slugs.\n\n"
                    f"channel_title: {channel_title or 'Unknown channel'}\n"
                    "Return strict JSON with fields: "
                    "book_title, book_slug, description, audience, routing_rules, glossary, categories, entries.\n"
                    "glossary[] fields: term, definition.\n"
                    "categories[] fields: title, category_slug, description, when_to_read, core_terms, entry_slugs.\n"
                    "entries[] fields: title, entry_slug, category_slug, summary, use_when, do_this, checklist, "
                    "anti_patterns, read_next, source_video_ids.\n\n"
                    "Source summaries:\n"
                    f"{chunk}"
                ),
            },
        ]
        return self._complete_blueprint(messages)

    def _merge_partials(
        self,
        partials: list[dict[str, Any]],
        *,
        channel_title: str | None,
    ) -> HandbookBlueprint:
        messages = [
            {
                "role": "system",
                "content": "You are merging several Patchouli handbook blueprint drafts into one final JSON blueprint. Output JSON only.",
            },
            {
                "role": "user",
                "content": (
                    "Merge these partial handbook blueprints into one final Patchouli handbook. "
                    "Keep the structure compact, deduplicate overlapping categories or entries, and preserve progressive disclosure.\n\n"
                    f"channel_title: {channel_title or 'Unknown channel'}\n"
                    "Return strict JSON with fields: "
                    "book_title, book_slug, description, audience, routing_rules, glossary, categories, entries.\n"
                    "glossary[] fields: term, definition.\n"
                    "categories[] fields: title, category_slug, description, when_to_read, core_terms, entry_slugs.\n"
                    "entries[] fields: title, entry_slug, category_slug, summary, use_when, do_this, checklist, "
                    "anti_patterns, read_next, source_video_ids.\n\n"
                    "Partial blueprints:\n"
                    f"{json.dumps(partials, ensure_ascii=False, indent=2)}"
                ),
            },
        ]
        return self._complete_blueprint(messages)

    def _complete_blueprint(self, messages: Sequence[dict[str, str]]) -> HandbookBlueprint:
        raw_text = self.gateway.complete(messages, json_mode=True)
        try:
            payload = json.loads(raw_text)
            return HandbookBlueprint.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            repair_messages = [
                {
                    "role": "system",
                    "content": "You repair malformed JSON into a valid Patchouli handbook blueprint. Output JSON only.",
                },
                {
                    "role": "user",
                    "content": (
                        "Repair the following payload into valid JSON with fields: "
                        "book_title, book_slug, description, audience, routing_rules, glossary, categories, entries.\n"
                        "glossary[] fields: term, definition.\n"
                        "categories[] fields: title, category_slug, description, when_to_read, core_terms, entry_slugs.\n"
                        "entries[] fields: title, entry_slug, category_slug, summary, use_when, do_this, checklist, "
                        "anti_patterns, read_next, source_video_ids.\n\n"
                        f"validation_error: {exc}\n"
                        f"broken_payload:\n{raw_text}"
                    ),
                },
            ]
            repaired_text = self.gateway.complete(repair_messages, json_mode=True)
            payload = json.loads(repaired_text)
            return HandbookBlueprint.model_validate(payload)
