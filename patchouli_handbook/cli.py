from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from .builder import (
    HandbookBuilder,
    render_category_markdown,
    render_entry_markdown,
    render_entry_skill_markdown,
    render_evidence_markdown,
    render_glossary_markdown,
    render_guide_markdown,
    render_index_markdown,
    render_manifest,
    render_source_index_markdown,
)
from .models import VideoSummaryDocument
from .summarizer import OpenAIChatGateway
from .store import (
    HandbookStore,
    create_empty_handbook,
    describe_handbook_structure,
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_documents(input_dir: Path) -> tuple[list[VideoSummaryDocument], str | None]:
    channel_path = input_dir / "channel.json"
    videos_path = input_dir / "videos.json"
    clean_dir = input_dir / "clean"
    if not videos_path.exists():
        raise FileNotFoundError(f"Missing videos.json: {videos_path}")
    if not clean_dir.exists():
        raise FileNotFoundError(f"Missing clean summary directory: {clean_dir}")

    channel_title = None
    if channel_path.exists():
        channel_payload = _read_json(channel_path)
        channel_title = channel_payload.get("channel_title")

    documents: list[VideoSummaryDocument] = []
    for video in _read_json(videos_path):
        video_id = str(video.get("video_id") or "").strip()
        if not video_id:
            continue
        clean_path = clean_dir / f"{video_id}.json"
        if not clean_path.exists():
            continue
        documents.append(
            VideoSummaryDocument.from_clean_json(
                _read_json(clean_path),
                video_id=video_id,
                title=str(video.get("title") or video_id),
                url=str(video.get("url") or f"https://www.youtube.com/watch?v={video_id}"),
                published_at=video.get("published_at"),
                sequence=int(video.get("sequence") or len(documents) + 1),
            )
        )
    if not documents:
        raise ValueError(f"No summarized videos found under {clean_dir}")
    return documents, channel_title


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def _write_handbook(output_dir: Path, blueprint, documents: list[VideoSummaryDocument]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    categories = {category.category_slug: category for category in blueprint.categories}
    entries_by_slug = {entry.entry_slug: entry for entry in blueprint.entries}

    _write_text(output_dir / "INDEX.md", render_index_markdown(blueprint))
    _write_text(output_dir / "GUIDE.md", render_guide_markdown(blueprint))
    _write_text(output_dir / "references" / "glossary.md", render_glossary_markdown(blueprint))
    _write_text(
        output_dir / "references" / "source_index.md",
        render_source_index_markdown(blueprint, documents=documents),
    )
    _write_text(output_dir / "entry_skill" / "SKILL.md", render_entry_skill_markdown(blueprint))

    for category in blueprint.categories:
        entries = [
            entries_by_slug[entry_slug]
            for entry_slug in category.entry_slugs
            if entry_slug in entries_by_slug
        ]
        _write_text(
            output_dir / "categories" / category.category_slug / "CATEGORY.md",
            render_category_markdown(category, entries=entries),
        )

    for entry in blueprint.entries:
        _write_text(
            output_dir / "categories" / entry.category_slug / f"{entry.entry_slug}.md",
            render_entry_markdown(
                entry,
                categories=categories,
                entries_by_slug=entries_by_slug,
            ),
        )

    for document in documents:
        _write_text(output_dir / "evidence" / f"{document.video_id}.md", render_evidence_markdown(document))

    manifest = render_manifest(blueprint, documents=documents)
    manifest.update(
        {
            "status": "completed",
            "category_count": len(blueprint.categories),
            "entry_count": len(blueprint.entries),
            "source_video_count": len(documents),
        }
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_command(args: argparse.Namespace) -> int:
    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    documents, channel_title = _load_documents(input_dir)

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY or pass --api-key to build a new handbook.")
    gateway = OpenAIChatGateway(
        api_key=api_key,
        model=args.model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        base_url=args.base_url or os.environ.get("OPENAI_BASE_URL"),
    )
    blueprint = HandbookBuilder(gateway, max_chars=args.max_chars).build(
        documents,
        channel_title=args.channel_title or channel_title,
    )
    _write_handbook(output_dir, blueprint, documents)
    print(f"Wrote {len(blueprint.categories)} categories and {len(blueprint.entries)} entries to {output_dir}")
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    manifest_path = Path(args.handbook).expanduser().resolve() / "manifest.json"
    manifest = _read_json(manifest_path)
    source_count = manifest.get("source_video_count", manifest.get("source_videos", 0))
    print(f"title: {manifest.get('book_title')}")
    print(f"slug: {manifest.get('book_slug')}")
    print(f"categories: {manifest.get('category_count', len(manifest.get('categories', [])))}")
    print(f"entries: {manifest.get('entry_count', len(manifest.get('entries', [])))}")
    print(f"source_videos: {source_count}")
    return 0


def init_command(args: argparse.Namespace) -> int:
    handbook = create_empty_handbook(
        args.output,
        title=args.title,
        slug=args.slug,
        description=args.description,
        audience=args.audience,
        overwrite=args.overwrite,
    )
    _print_json(handbook)
    return 0


def _print_json(payload: Any) -> None:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        payload = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in payload
        ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def structure_command(args: argparse.Namespace) -> int:
    _print_json(describe_handbook_structure())
    return 0


def describe_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.describe())
    return 0


def validate_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    report = store.validate()
    _print_json(report)
    return 0 if report.ok else 1


def update_book_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.update_book(_load_payload_arg(args.payload)))
    return 0


def apply_operation_command(args: argparse.Namespace) -> int:
    payload = _load_payload_arg(args.payload)
    handbook = args.handbook or payload.pop("handbook", None) or "handbook"
    store = HandbookStore(handbook)
    result = store.apply_operation(payload)
    _print_json(result)
    return 0


def list_categories_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json([category.model_dump(mode="json") for category in store.list_categories()])
    return 0


def list_entries_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(
        [
            entry.model_dump(mode="json")
            for entry in store.list_entries(category_slug=args.category_slug)
        ]
    )
    return 0


def get_category_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.get_category(args.slug))
    return 0


def get_entry_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.get_entry(args.slug))
    return 0


def _load_payload_arg(raw_payload: str) -> dict[str, Any]:
    if raw_payload.lstrip().startswith("{"):
        payload = json.loads(raw_payload)
    else:
        payload = _read_json(Path(raw_payload).expanduser())
    if not isinstance(payload, dict):
        raise ValueError("CRUD payload must be a JSON object.")
    return payload


def create_category_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.create_category(_load_payload_arg(args.payload)))
    return 0


def update_category_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.update_category(args.slug, _load_payload_arg(args.payload)))
    return 0


def delete_category_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.delete_category(args.slug, force=args.force))
    return 0


def create_entry_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.create_entry(_load_payload_arg(args.payload)))
    return 0


def update_entry_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.update_entry(args.slug, _load_payload_arg(args.payload)))
    return 0


def delete_entry_command(args: argparse.Namespace) -> int:
    store = HandbookStore(args.handbook)
    _print_json(store.delete_entry(args.slug))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="patchouli-handbook",
        description="Create, build, inspect, and edit Patchouli handbook knowledge systems.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create an empty handbook scaffold.")
    init_parser.add_argument("--output", required=True, help="Output handbook directory.")
    init_parser.add_argument("--title", required=True, help="Human-readable handbook title.")
    init_parser.add_argument("--slug", default=None, help="Optional lowercase ASCII handbook slug.")
    init_parser.add_argument("--description", default=None, help="Optional handbook description.")
    init_parser.add_argument("--audience", default=None, help="Optional target audience.")
    init_parser.add_argument("--overwrite", action="store_true", help="Allow initializing into a non-empty directory.")
    init_parser.set_defaults(func=init_command)

    build_parser = subparsers.add_parser("build", help="Build a handbook from a cleaned source-summary job directory.")
    build_parser.add_argument("--input", required=True, help="Directory containing channel.json, videos.json, and clean/*.json.")
    build_parser.add_argument("--output", required=True, help="Output handbook directory.")
    build_parser.add_argument("--channel-title", default=None, help="Override channel title.")
    build_parser.add_argument("--api-key", default=None, help="OpenAI API key. Defaults to OPENAI_API_KEY.")
    build_parser.add_argument("--model", default=None, help="OpenAI model. Defaults to OPENAI_MODEL or gpt-4.1-mini.")
    build_parser.add_argument("--base-url", default=None, help="Optional OpenAI-compatible base URL.")
    build_parser.add_argument("--max-chars", type=int, default=18000, help="Max characters per LLM chunk.")
    build_parser.set_defaults(func=build_command)

    inspect_parser = subparsers.add_parser("inspect", help="Print handbook manifest summary.")
    inspect_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    inspect_parser.set_defaults(func=inspect_command)

    structure_parser = subparsers.add_parser("structure", help="Print the handbook declaration and on-disk structure.")
    structure_parser.set_defaults(func=structure_command)

    describe_parser = subparsers.add_parser("describe", help="Print handbook structure and counts as JSON.")
    describe_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    describe_parser.set_defaults(func=describe_command)

    validate_parser = subparsers.add_parser("validate", help="Validate manifest, paths, and cross references.")
    validate_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    validate_parser.set_defaults(func=validate_command)

    apply_parser = subparsers.add_parser("apply", help="Apply one JSON operation object and print the JSON result.")
    apply_parser.add_argument("payload")
    apply_parser.add_argument("--handbook", default=None, help="Handbook directory. Overrides payload.handbook when provided.")
    apply_parser.set_defaults(func=apply_operation_command)

    book_parser = subparsers.add_parser("book", help="Update top-level handbook metadata.")
    book_subparsers = book_parser.add_subparsers(dest="book_command", required=True)
    book_update_parser = book_subparsers.add_parser("update", help="Update book metadata from a JSON object or JSON file path.")
    book_update_parser.add_argument("payload")
    book_update_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    book_update_parser.set_defaults(func=update_book_command)

    categories_parser = subparsers.add_parser("categories", help="List, get, create, update, or delete categories.")
    categories_subparsers = categories_parser.add_subparsers(dest="category_command", required=True)
    categories_list_parser = categories_subparsers.add_parser("list", help="List categories.")
    categories_list_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    categories_list_parser.set_defaults(func=list_categories_command)
    categories_get_parser = categories_subparsers.add_parser("get", help="Get one category by slug.")
    categories_get_parser.add_argument("slug")
    categories_get_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    categories_get_parser.set_defaults(func=get_category_command)
    categories_create_parser = categories_subparsers.add_parser("create", help="Create a category from a JSON object or JSON file path.")
    categories_create_parser.add_argument("payload")
    categories_create_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    categories_create_parser.set_defaults(func=create_category_command)
    categories_update_parser = categories_subparsers.add_parser("update", help="Update a category from a JSON object or JSON file path.")
    categories_update_parser.add_argument("slug")
    categories_update_parser.add_argument("payload")
    categories_update_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    categories_update_parser.set_defaults(func=update_category_command)
    categories_delete_parser = categories_subparsers.add_parser("delete", help="Delete a category.")
    categories_delete_parser.add_argument("slug")
    categories_delete_parser.add_argument("--force", action="store_true", help="Also delete entries in this category.")
    categories_delete_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    categories_delete_parser.set_defaults(func=delete_category_command)

    entries_parser = subparsers.add_parser("entries", help="List, get, create, update, or delete entries.")
    entries_subparsers = entries_parser.add_subparsers(dest="entry_command", required=True)
    entries_list_parser = entries_subparsers.add_parser("list", help="List entries.")
    entries_list_parser.add_argument("--category-slug", default=None, help="Only list entries in this category.")
    entries_list_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    entries_list_parser.set_defaults(func=list_entries_command)
    entries_get_parser = entries_subparsers.add_parser("get", help="Get one entry by slug.")
    entries_get_parser.add_argument("slug")
    entries_get_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    entries_get_parser.set_defaults(func=get_entry_command)
    entries_create_parser = entries_subparsers.add_parser("create", help="Create an entry from a JSON object or JSON file path.")
    entries_create_parser.add_argument("payload")
    entries_create_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    entries_create_parser.set_defaults(func=create_entry_command)
    entries_update_parser = entries_subparsers.add_parser("update", help="Update an entry from a JSON object or JSON file path.")
    entries_update_parser.add_argument("slug")
    entries_update_parser.add_argument("payload")
    entries_update_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    entries_update_parser.set_defaults(func=update_entry_command)
    entries_delete_parser = entries_subparsers.add_parser("delete", help="Delete an entry.")
    entries_delete_parser.add_argument("slug")
    entries_delete_parser.add_argument("--handbook", default="handbook", help="Handbook directory containing manifest.json.")
    entries_delete_parser.set_defaults(func=delete_entry_command)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        _print_json(
            {
                "ok": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            }
        )
        print("", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
