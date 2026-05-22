# Patchouli Handbook

Patchouli Handbook is a file-backed knowledge system for AI agents. It is inspired by skills, but it is intentionally thicker: a skill can trigger the right behavior, while a handbook can hold a full guide, routing map, reusable entries, glossary, source evidence, validation, and CRUD tooling.

Use it when an agent needs more than a short SOP: domain principles, decision rules, examples, anti-patterns, and source-grounded guidance that should be expanded progressively instead of loaded all at once.

## What It Provides

- A stable on-disk handbook format built from Markdown plus `manifest.json`.
- A lightweight `entry_skill/SKILL.md` activation layer for skill-aware agents.
- A thicker `GUIDE.md` operating manual for complex tasks.
- Category and entry pages for progressive disclosure.
- Optional evidence pages and source indexes for provenance.
- A Python API and JSON CLI for creating, editing, validating, and inspecting handbooks.
- A complete example handbook generated from public game-design source summaries.

## Repository Layout

```text
patchouli_handbook/   Python library and CLI
docs/                 Architecture, authoring, and agent protocol docs
example/              Example generated handbooks
tests/                Unit tests
pyproject.toml        Package metadata and console script
```

## Handbook Layout

```text
<handbook_dir>/
├── manifest.json
├── GUIDE.md
├── INDEX.md
├── entry_skill/
│   └── SKILL.md
├── categories/
│   └── <category_slug>/
│       ├── CATEGORY.md
│       └── <entry_slug>.md
├── references/
│   ├── glossary.md
│   └── source_index.md
└── evidence/
    └── <source_id>.md
```

## Quick Start

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

Python 3.10+ is supported.

Create a blank handbook:

```bash
patchouli-handbook init \
  --output output/studio-handbook \
  --title "Studio Handbook" \
  --audience "AI agents and studio maintainers"
```

Add content:

```bash
patchouli-handbook categories create \
  '{"title":"Planning","description":"Scoping, goals, and project framing."}' \
  --handbook output/studio-handbook

patchouli-handbook entries create \
  '{"title":"Scope First","category_slug":"planning","summary":"Decide the scope before choosing tactics."}' \
  --handbook output/studio-handbook

patchouli-handbook validate --handbook output/studio-handbook
```

Inspect the included example:

```bash
patchouli-handbook inspect --handbook example/masahiro-sakurai-on-creating-games
patchouli-handbook validate --handbook example/masahiro-sakurai-on-creating-games
```

Start reading the example at:

- `example/masahiro-sakurai-on-creating-games/GUIDE.md`
- `example/masahiro-sakurai-on-creating-games/INDEX.md`

## CLI

Common commands:

```bash
patchouli-handbook structure
patchouli-handbook describe --handbook <handbook_dir>
patchouli-handbook validate --handbook <handbook_dir>
patchouli-handbook categories list --handbook <handbook_dir>
patchouli-handbook entries get <entry_slug> --handbook <handbook_dir>
```

Machine-readable integration point:

```bash
patchouli-handbook apply '{"action":"get_entry","slug":"scope-first"}' --handbook <handbook_dir>
```

`apply` accepts these actions:

- `describe`
- `validate`
- `list_categories`
- `list_entries`
- `get_category`
- `get_entry`
- `update_book`
- `create_category`
- `update_category`
- `delete_category`
- `create_entry`
- `update_entry`
- `delete_entry`

CLI failures are emitted as JSON:

```json
{
  "ok": false,
  "error": {
    "type": "KeyError",
    "message": "'Unknown entry: missing-entry'"
  }
}
```

## Python API

```python
from patchouli_handbook import HandbookStore, create_empty_handbook

create_empty_handbook(
    "output/studio-handbook",
    title="Studio Handbook",
    audience="AI agents and studio maintainers",
)

store = HandbookStore("output/studio-handbook")
store.create_category(
    {
        "title": "Planning",
        "description": "Scoping, goals, and project framing.",
    }
)
store.create_entry(
    {
        "title": "Scope First",
        "category_slug": "planning",
        "summary": "Decide the scope before choosing tactics.",
        "use_when": ["The task is broad or under-specified."],
        "do_this": ["Name the goal.", "Name constraints.", "Pick the smallest useful next step."],
        "checklist": ["The scope is explicit.", "The next action is concrete."],
        "anti_patterns": ["Do not choose tactics before defining the target."],
    }
)
print(store.validate().model_dump())
```

## Build From Source Summaries

The builder can generate a handbook from a `channel_extractor`-style job directory containing:

- `channel.json`
- `videos.json`
- `clean/<video_id>.json`

Example:

```bash
export OPENAI_API_KEY=...
patchouli-handbook build \
  --input path/to/channel-job \
  --output output/generated-handbook
```

The builder writes `GUIDE.md`, `INDEX.md`, category pages, entry pages, references, evidence pages, `entry_skill/SKILL.md`, and `manifest.json`.

## Documentation

- [Architecture](docs/architecture.md): artifact layout and layer responsibilities.
- [Agent Protocol](docs/agent-protocol.md): how an AI agent should progressively read a handbook.
- [Authoring Guide](docs/authoring-guide.md): how to add categories, entries, evidence, and links.
- [Minimal Template](docs/template-handbook.md): planning worksheet for a new handbook.

## Included Example

`example/masahiro-sakurai-on-creating-games` demonstrates a generated handbook with:

- 14 categories
- 260 entries
- 299 evidence pages
- `GUIDE.md` plus a skill-compatible `entry_skill/SKILL.md`

The example is included to show the intended scale and navigation pattern of a thick handbook.

## Test

```bash
pytest
```

