from __future__ import annotations

from dataclasses import dataclass
import json

from patchouli_handbook.builder import HandbookBlueprint, HandbookBuilder, normalize_blueprint, render_entry_markdown, render_entry_skill_markdown, render_guide_markdown, render_manifest
from patchouli_handbook.models import StructuredSummary, VideoSummaryDocument


@dataclass
class FakeGateway:
    responses: list[str]

    def __post_init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]], *, json_mode: bool) -> str:
        assert json_mode is True
        self.calls.append(messages)
        return self.responses.pop(0)


def make_document(video_id: str, sequence: int, *, suffix: str = "") -> VideoSummaryDocument:
    return VideoSummaryDocument(
        video_id=video_id,
        title=f"Video {sequence}",
        url=f"https://www.youtube.com/watch?v={video_id}",
        published_at=f"2026-05-2{sequence}",
        sequence=sequence,
        summary=StructuredSummary.model_validate(
            {
                "summary_zh": f"围绕游戏设计审阅的长摘要 {suffix or video_id} " + ("x" * 120),
                "key_points": [f"目标对齐 {sequence}", f"玩家体验 {sequence}"],
                "action_steps": [f"步骤 {sequence}-1", f"步骤 {sequence}-2"],
                "tools_or_resources": [f"工具 {sequence}"],
                "notable_segments": [
                    {"timestamp": "00:00", "excerpt": "片段", "note": "说明"}
                ],
                "transcript_language": "en",
                "source_video_url": f"https://www.youtube.com/watch?v={video_id}",
            }
        ),
    )


def sample_blueprint() -> HandbookBlueprint:
    return HandbookBlueprint.model_validate(
        {
            "book_title": "Demo Patchouli Handbook",
            "book_slug": "demo-patchouli-handbook",
            "description": "供 agent 按需展开的参考手册。",
            "audience": "需要复用频道经验的 AI agent。",
            "routing_rules": [
                "先读 INDEX.md。",
                "先选一个 category。",
                "只展开 1-2 个 entry。",
            ],
            "glossary": [
                {"term": "玩家体验", "definition": "频道反复强调的目标。"}
            ],
            "categories": [
                {
                    "title": "Review Workflows",
                    "category_slug": "review-workflows",
                    "description": "适合做设计审阅的入口分类。",
                    "when_to_read": ["需要审阅设计方案时。"],
                    "core_terms": ["玩家体验", "目标对齐"],
                    "entry_slugs": ["combat-balance-review", "goal-framing"],
                }
            ],
            "entries": [
                {
                    "title": "Combat Balance Review",
                    "entry_slug": "combat-balance-review",
                    "category_slug": "review-workflows",
                    "summary": "用于审阅战斗平衡与反馈节奏。",
                    "use_when": ["需要审阅战斗系统时。"],
                    "do_this": ["先抽取目标与限制。", "再对照设计原则进行审查。"],
                    "checklist": ["目标是否清晰。", "改进项是否可执行。"],
                    "anti_patterns": ["不要跳过目标定义直接下结论。"],
                    "read_next": ["goal-framing"],
                    "source_video_ids": ["video-1", "video-2"],
                },
                {
                    "title": "Goal Framing",
                    "entry_slug": "goal-framing",
                    "category_slug": "review-workflows",
                    "summary": "在展开分析前统一问题边界和评价标准。",
                    "use_when": ["需要先定义目标再展开分析时。"],
                    "do_this": ["识别目标玩家。", "列出评价标准。"],
                    "checklist": ["评价标准是否可验证。"],
                    "anti_patterns": ["不要把目标和方案混为一谈。"],
                    "read_next": [],
                    "source_video_ids": ["video-2"],
                },
            ],
        }
    )


def test_render_manifest_contains_required_routing_metadata() -> None:
    documents = [make_document("video-1", 1), make_document("video-2", 2)]
    blueprint = normalize_blueprint(
        sample_blueprint(),
        documents=documents,
        channel_title="Demo Channel",
    )

    manifest = render_manifest(blueprint, documents=documents)

    assert manifest["book_title"] == "Demo Patchouli Handbook"
    assert manifest["guide_path"] == "GUIDE.md"
    assert manifest["index_path"] == "INDEX.md"
    assert manifest["entry_skill_path"] == "entry_skill/SKILL.md"
    assert manifest["categories"][0]["path"] == "categories/review-workflows/CATEGORY.md"
    assert manifest["entries"][0]["path"] == "categories/review-workflows/combat-balance-review.md"
    assert manifest["source_videos"][0]["evidence_path"] == "evidence/video-1.md"


def test_render_entry_markdown_includes_frontmatter_and_links() -> None:
    documents = [make_document("video-1", 1), make_document("video-2", 2)]
    blueprint = normalize_blueprint(
        sample_blueprint(),
        documents=documents,
        channel_title="Demo Channel",
    )
    entries_by_slug = {entry.entry_slug: entry for entry in blueprint.entries}
    categories = {category.category_slug: category for category in blueprint.categories}

    markdown = render_entry_markdown(
        entries_by_slug["combat-balance-review"],
        categories=categories,
        entries_by_slug=entries_by_slug,
    )

    assert markdown.startswith("---\n")
    assert 'entry_slug: "combat-balance-review"' in markdown
    assert "source_videos:" in markdown
    assert "## Summary" in markdown
    assert "## Read Next" in markdown
    assert "- [Goal Framing](./goal-framing.md)" in markdown
    assert "- [video-1](../../evidence/video-1.md)" in markdown


def test_build_deduplicates_categories_and_entries_after_chunk_merge() -> None:
    documents = [
        make_document("video-1", 1, suffix="alpha"),
        make_document("video-2", 2, suffix="beta"),
    ]
    responses = [
        json.dumps(
            {
                "book_title": "Demo Patchouli Handbook",
                "book_slug": "demo-patchouli-handbook",
                "description": "desc",
                "audience": "agents",
                "routing_rules": ["先读 INDEX.md。"],
                "glossary": [],
                "categories": [
                    {
                        "title": "Review Workflows",
                        "category_slug": "review-workflows",
                        "description": "desc",
                        "when_to_read": ["A"],
                        "core_terms": ["玩家体验"],
                        "entry_slugs": ["combat-balance-review"],
                    }
                ],
                "entries": [
                    {
                        "title": "Combat Balance Review",
                        "entry_slug": "combat-balance-review",
                        "category_slug": "review-workflows",
                        "summary": "summary",
                        "use_when": ["A"],
                        "do_this": ["step"],
                        "checklist": ["check"],
                        "anti_patterns": ["avoid"],
                        "read_next": [],
                        "source_video_ids": ["video-1"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "book_title": "Demo Patchouli Handbook",
                "book_slug": "demo-patchouli-handbook",
                "description": "desc",
                "audience": "agents",
                "routing_rules": ["先选一个 category。"],
                "glossary": [],
                "categories": [
                    {
                        "title": "Review Workflows",
                        "category_slug": "review-workflows",
                        "description": "desc",
                        "when_to_read": ["B"],
                        "core_terms": ["目标对齐"],
                        "entry_slugs": ["combat-balance-review", "goal-framing"],
                    }
                ],
                "entries": [
                    {
                        "title": "Combat Balance Review",
                        "entry_slug": "combat-balance-review",
                        "category_slug": "review-workflows",
                        "summary": "summary",
                        "use_when": ["B"],
                        "do_this": ["step"],
                        "checklist": ["check"],
                        "anti_patterns": ["avoid"],
                        "read_next": ["goal-framing"],
                        "source_video_ids": ["video-2"],
                    },
                    {
                        "title": "Goal Framing",
                        "entry_slug": "goal-framing",
                        "category_slug": "review-workflows",
                        "summary": "goal summary",
                        "use_when": ["C"],
                        "do_this": ["step 2"],
                        "checklist": ["check 2"],
                        "anti_patterns": ["avoid 2"],
                        "read_next": [],
                        "source_video_ids": ["video-2"],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "book_title": "Demo Patchouli Handbook",
                "book_slug": "demo-patchouli-handbook",
                "description": "desc",
                "audience": "agents",
                "routing_rules": ["先读 INDEX.md。", "只展开 1-2 个 entry。"],
                "glossary": [],
                "categories": [
                    {
                        "title": "Review Workflows",
                        "category_slug": "review-workflows",
                        "description": "desc",
                        "when_to_read": ["A", "B"],
                        "core_terms": ["玩家体验", "目标对齐"],
                        "entry_slugs": ["combat-balance-review", "goal-framing"],
                    },
                    {
                        "title": "Review Workflows",
                        "category_slug": "review-workflows",
                        "description": "duplicate",
                        "when_to_read": ["B"],
                        "core_terms": ["目标对齐"],
                        "entry_slugs": ["combat-balance-review"],
                    },
                ],
                "entries": [
                    {
                        "title": "Combat Balance Review",
                        "entry_slug": "combat-balance-review",
                        "category_slug": "review-workflows",
                        "summary": "summary",
                        "use_when": ["A", "B"],
                        "do_this": ["step"],
                        "checklist": ["check"],
                        "anti_patterns": ["avoid"],
                        "read_next": ["goal-framing"],
                        "source_video_ids": ["video-1", "video-2"],
                    },
                    {
                        "title": "Combat Balance Review",
                        "entry_slug": "combat-balance-review",
                        "category_slug": "review-workflows",
                        "summary": "summary",
                        "use_when": ["A"],
                        "do_this": ["step"],
                        "checklist": ["check"],
                        "anti_patterns": ["avoid"],
                        "read_next": [],
                        "source_video_ids": ["video-1"],
                    },
                    {
                        "title": "Goal Framing",
                        "entry_slug": "goal-framing",
                        "category_slug": "review-workflows",
                        "summary": "goal summary",
                        "use_when": ["C"],
                        "do_this": ["step 2"],
                        "checklist": ["check 2"],
                        "anti_patterns": ["avoid 2"],
                        "read_next": [],
                        "source_video_ids": ["video-2"],
                    },
                ],
            },
            ensure_ascii=False,
        ),
    ]
    builder = HandbookBuilder(FakeGateway(responses), max_chars=350)

    blueprint = builder.build(documents, channel_title="Demo Channel")

    assert len(blueprint.categories) == 1
    assert len(blueprint.entries) == 2
    assert blueprint.categories[0].entry_slugs == ["combat-balance-review", "goal-framing"]
    assert blueprint.entries[0].read_next == ["goal-framing"]


def test_build_falls_back_to_overview_when_model_returns_empty_structure() -> None:
    gateway = FakeGateway(
        responses=[
            json.dumps(
                {
                    "book_title": "Empty Handbook",
                    "book_slug": "empty-handbook",
                    "description": "desc",
                    "audience": "agents",
                    "routing_rules": [],
                    "glossary": [],
                    "categories": [],
                    "entries": [],
                },
                ensure_ascii=False,
            )
        ]
    )
    builder = HandbookBuilder(gateway)

    blueprint = builder.build([make_document("video-1", 1)], channel_title="Demo Channel")

    assert blueprint.categories[0].title == "Overview"
    assert blueprint.entries[0].entry_slug == "channel-overview"
    assert blueprint.routing_rules


def test_render_entry_skill_stays_navigation_only() -> None:
    documents = [make_document("video-1", 1), make_document("video-2", 2)]
    blueprint = normalize_blueprint(
        sample_blueprint(),
        documents=documents,
        channel_title="Demo Channel",
    )

    markdown = render_entry_skill_markdown(blueprint)

    assert "`../GUIDE.md`" in markdown
    assert "`../INDEX.md`" in markdown
    assert "Expand only 1-2 entry pages" in markdown
    assert "用于审阅战斗平衡与反馈节奏" not in markdown


def test_render_guide_markdown_explains_thick_handbook_protocol() -> None:
    documents = [make_document("video-1", 1), make_document("video-2", 2)]
    blueprint = normalize_blueprint(
        sample_blueprint(),
        documents=documents,
        channel_title="Demo Channel",
    )

    markdown = render_guide_markdown(blueprint)

    assert "# Demo Patchouli Handbook Guide" in markdown
    assert "thick reference system" in markdown
    assert "`entry_skill/SKILL.md` is the lightweight activation layer" in markdown
    assert "## Reading Protocol" in markdown
    assert "## Maintenance Protocol" in markdown


def test_builder_accepts_dict_routing_rules_and_normalizes_them() -> None:
    gateway = FakeGateway(
        responses=[
            json.dumps(
                {
                    "book_title": "Structured Rules Handbook",
                    "book_slug": "structured-rules-handbook",
                    "description": "desc",
                    "audience": "agents",
                    "routing_rules": [
                        {
                            "condition": "the user asks about UI polish",
                            "route_to": "ui-category",
                        },
                        {
                            "condition": "the user asks about animation timing",
                            "route_to": "animation-category",
                            "reason": "timing issues usually live there",
                        },
                    ],
                    "glossary": [],
                    "categories": [
                        {
                            "title": "Overview",
                            "category_slug": "overview",
                            "description": "desc",
                            "when_to_read": ["A"],
                            "core_terms": ["术语"],
                            "entry_slugs": ["overview-entry"],
                        }
                    ],
                    "entries": [
                        {
                            "title": "Overview Entry",
                            "entry_slug": "overview-entry",
                            "category_slug": "overview",
                            "summary": "summary",
                            "use_when": ["A"],
                            "do_this": ["step"],
                            "checklist": ["check"],
                            "anti_patterns": ["avoid"],
                            "read_next": [],
                            "source_video_ids": ["video-1"],
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    builder = HandbookBuilder(gateway)

    blueprint = builder.build([make_document("video-1", 1)], channel_title="Demo Channel")

    assert blueprint.routing_rules[0] == "If the user asks about UI polish; route to ui-category"
    assert "because timing issues usually live there" in blueprint.routing_rules[1]
