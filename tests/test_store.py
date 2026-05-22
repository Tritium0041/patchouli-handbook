from __future__ import annotations

import json
from pathlib import Path

import pytest

from patchouli_handbook.builder import (
    normalize_blueprint,
    render_category_markdown,
    render_entry_markdown,
    render_entry_skill_markdown,
    render_guide_markdown,
    render_index_markdown,
    render_manifest,
    render_source_index_markdown,
)
from patchouli_handbook.cli import main
from patchouli_handbook.store import HandbookStore, create_empty_handbook, describe_handbook_structure

from tests.test_builder import make_document, sample_blueprint


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_sample_handbook(root: Path) -> None:
    documents = [make_document("video-1", 1), make_document("video-2", 2)]
    blueprint = normalize_blueprint(
        sample_blueprint(),
        documents=documents,
        channel_title="Demo Channel",
    )
    categories = {category.category_slug: category for category in blueprint.categories}
    entries_by_slug = {entry.entry_slug: entry for entry in blueprint.entries}

    write_text(root / "INDEX.md", render_index_markdown(blueprint))
    write_text(root / "GUIDE.md", render_guide_markdown(blueprint))
    write_text(root / "entry_skill" / "SKILL.md", render_entry_skill_markdown(blueprint))
    write_text(root / "references" / "source_index.md", render_source_index_markdown(blueprint, documents=documents))

    for category in blueprint.categories:
        entries = [
            entries_by_slug[entry_slug]
            for entry_slug in category.entry_slugs
            if entry_slug in entries_by_slug
        ]
        write_text(
            root / "categories" / category.category_slug / "CATEGORY.md",
            render_category_markdown(category, entries=entries),
        )

    for entry in blueprint.entries:
        write_text(
            root / "categories" / entry.category_slug / f"{entry.entry_slug}.md",
            render_entry_markdown(
                entry,
                categories=categories,
                entries_by_slug=entries_by_slug,
            ),
        )

    manifest = render_manifest(blueprint, documents=documents)
    manifest.update(
        {
            "status": "completed",
            "category_count": len(blueprint.categories),
            "entry_count": len(blueprint.entries),
            "source_video_count": len(documents),
        }
    )
    write_text(root / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def test_describe_handbook_structure_declares_current_paths() -> None:
    structure = describe_handbook_structure()

    assert structure.manifest_path == "manifest.json"
    assert structure.guide_path == "GUIDE.md"
    assert structure.category_path_pattern == "categories/{category_slug}/CATEGORY.md"
    assert structure.entry_path_pattern == "categories/{category_slug}/{entry_slug}.md"
    assert "entries" in structure.manifest_fields
    assert structure.writable_kinds == ["book", "category", "entry"]
    assert "validate" in structure.operations
    assert "init" not in structure.operations


def test_create_empty_handbook_scaffolds_guided_knowledge_system(tmp_path: Path) -> None:
    manifest = create_empty_handbook(
        tmp_path,
        title="Studio Knowledge",
        description="Reusable production guidance.",
        audience="AI agents and producers.",
    )

    guide = (tmp_path / "GUIDE.md").read_text(encoding="utf-8")
    skill = (tmp_path / "entry_skill" / "SKILL.md").read_text(encoding="utf-8")
    report = HandbookStore(tmp_path).validate()

    assert manifest.book_slug == "studio-knowledge"
    assert manifest.status == "draft"
    assert manifest.category_count == 0
    assert "thick reference system" in guide
    assert "`../GUIDE.md`" in skill
    assert report.ok is True


def test_cli_init_outputs_manifest_and_writes_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "new-handbook"

    exit_code = main(
        [
            "init",
            "--output",
            str(target),
            "--title",
            "Design Handbook",
            "--audience",
            "Design agents.",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["book_slug"] == "design-handbook"
    assert (target / "GUIDE.md").exists()
    assert (target / "INDEX.md").exists()
    assert (target / "entry_skill" / "SKILL.md").exists()


def test_store_reads_manifest_and_entry_markdown(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    store = HandbookStore(tmp_path)

    category = store.get_category("review-workflows")
    entry = store.get_entry("combat-balance-review")

    assert category.entry_slugs == ["combat-balance-review", "goal-framing"]
    assert entry.summary == "用于审阅战斗平衡与反馈节奏。"
    assert entry.do_this == ["先抽取目标与限制。", "再对照设计原则进行审查。"]
    assert entry.source_videos == ["video-1", "video-2"]


def test_store_supports_legacy_manifest_with_source_video_count(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_videos"] = 2
    manifest["source_video_count"] = 2
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_index_before = (tmp_path / "references" / "source_index.md").read_text(encoding="utf-8")

    store = HandbookStore(tmp_path)
    created = store.create_category(
        {
            "title": "Agent Workflow",
            "slug": "agent-workflow",
            "description": "Agent-facing workflow notes.",
        }
    )

    manifest_after = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_index_after = (tmp_path / "references" / "source_index.md").read_text(encoding="utf-8")

    assert created.slug == "agent-workflow"
    assert manifest_after["source_videos"] == 2
    assert manifest_after["source_video_count"] == 2
    assert source_index_after == source_index_before


def test_store_creates_updates_and_deletes_entry_with_manifest_and_markdown_sync(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    store = HandbookStore(tmp_path)

    created = store.create_entry(
        {
            "title": "Scope First",
            "category_slug": "review-workflows",
            "summary": "先确定范围，再选择条目。",
            "use_when": ["需要先缩小问题范围时。"],
            "do_this": ["确认目标。"],
            "checklist": ["范围是否明确。"],
            "anti_patterns": ["不要边界不清就执行。"],
            "read_next": ["goal-framing"],
            "source_videos": ["video-1"],
        }
    )

    assert created.slug == "scope-first"
    assert (tmp_path / "categories" / "review-workflows" / "scope-first.md").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["entry_count"] == 3
    assert "scope-first" in [entry["slug"] for entry in manifest["entries"]]

    updated = store.update_entry(
        "scope-first",
        {
            "slug": "scope-before-review",
            "summary": "先统一范围和评价标准，再选择条目。",
            "read_next": ["combat-balance-review"],
        },
    )

    assert updated.slug == "scope-before-review"
    assert updated.summary == "先统一范围和评价标准，再选择条目。"
    assert not (tmp_path / "categories" / "review-workflows" / "scope-first.md").exists()
    assert (tmp_path / "categories" / "review-workflows" / "scope-before-review.md").exists()

    deleted = store.delete_entry("scope-before-review")

    assert deleted.slug == "scope-before-review"
    assert not (tmp_path / "categories" / "review-workflows" / "scope-before-review.md").exists()
    assert "scope-before-review" not in [entry.slug for entry in store.list_entries()]


def test_store_protects_non_empty_category_delete_and_supports_force(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    store = HandbookStore(tmp_path)

    with pytest.raises(ValueError, match="Category is not empty"):
        store.delete_category("review-workflows")

    deleted = store.delete_category("review-workflows", force=True)

    assert deleted.slug == "review-workflows"
    assert store.list_categories() == []
    assert store.list_entries() == []
    assert not (tmp_path / "categories" / "review-workflows" / "CATEGORY.md").exists()


def test_cli_entry_crud_outputs_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_sample_handbook(tmp_path)
    payload = json.dumps(
        {
            "title": "Agent Handoff",
            "category_slug": "review-workflows",
            "summary": "把条目作为 agent 交接上下文。",
            "use_when": ["需要交给另一个 agent 继续时。"],
            "do_this": ["列出条目路径。"],
            "checklist": ["输出是否包含 slug。"],
            "anti_patterns": ["不要省略来源。"],
        },
        ensure_ascii=False,
    )

    exit_code = main(["entries", "create", payload, "--handbook", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["slug"] == "agent-handoff"
    assert output["path"] == "categories/review-workflows/agent-handoff.md"


def test_cli_describe_outputs_structure_and_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_sample_handbook(tmp_path)

    exit_code = main(["describe", "--handbook", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["structure"]["manifest_path"] == "manifest.json"
    assert output["category_count"] == 1
    assert output["entry_count"] == 2
    assert output["source_video_count"] == 2


def test_store_updates_book_metadata_and_rerenders_navigation(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    store = HandbookStore(tmp_path)

    manifest = store.update_book(
        {
            "book_title": "Updated Handbook",
            "book_slug": "Updated Handbook",
            "description": "Updated description.",
            "audience": "Agent callers.",
            "routing_rules": ["Read INDEX first.", "Pick one entry."],
        }
    )

    index = (tmp_path / "INDEX.md").read_text(encoding="utf-8")
    entry_skill = (tmp_path / "entry_skill" / "SKILL.md").read_text(encoding="utf-8")

    assert manifest.book_title == "Updated Handbook"
    assert manifest.book_slug == "updated-handbook"
    assert "# Updated Handbook" in index
    assert "Read INDEX first." in index
    assert "Updated Handbook Entry Skill" in entry_skill


def test_store_validate_reports_missing_files_and_bad_links(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"][0]["read_next"] = ["missing-entry"]
    manifest["entries"][0]["path"] = "categories/review-workflows/missing-file.md"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (tmp_path / "categories" / "review-workflows" / "combat-balance-review.md").unlink()

    report = HandbookStore(tmp_path).validate()

    assert report.ok is False
    assert {issue.code for issue in report.errors} >= {"entry_read_next_missing", "missing_entry_file"}
    assert "entry_path_mismatch" in {issue.code for issue in report.warnings}


def test_store_apply_operation_dispatches_single_json_calls(tmp_path: Path) -> None:
    write_sample_handbook(tmp_path)
    store = HandbookStore(tmp_path)

    created = store.apply_operation(
        {
            "action": "create_entry",
            "payload": {
                "title": "Operation Entry",
                "category_slug": "review-workflows",
                "summary": "Created through the generic operation API.",
            },
        }
    )
    fetched = store.apply_operation({"action": "get_entry", "slug": "operation-entry"})

    assert created.slug == "operation-entry"
    assert fetched.summary == "Created through the generic operation API."


def test_cli_apply_and_validate_are_machine_readable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_sample_handbook(tmp_path)
    operation = json.dumps(
        {
            "action": "create_category",
            "payload": {
                "title": "Machine Calls",
                "description": "Operations designed for agent callers.",
            },
        },
        ensure_ascii=False,
    )

    create_exit = main(["apply", operation, "--handbook", str(tmp_path)])
    created = json.loads(capsys.readouterr().out)
    validate_exit = main(["validate", "--handbook", str(tmp_path)])
    report = json.loads(capsys.readouterr().out)

    assert create_exit == 0
    assert created["slug"] == "machine-calls"
    assert validate_exit == 0
    assert report["ok"] is True


def test_cli_errors_are_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_sample_handbook(tmp_path)

    exit_code = main(["entries", "get", "missing-entry", "--handbook", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert output["error"]["type"] == "KeyError"
