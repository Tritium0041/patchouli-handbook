# Patchouli Handbook Architecture

Patchouli Handbook is a file-backed AI knowledge system. It borrows the progressive-disclosure idea from skills, but the unit is a guidebook: broad enough to hold concepts, judgment patterns, evidence, examples, and maintenance rules.

## Design Goals

- Give an AI agent a small activation entry and a larger reference structure.
- Keep routing, reading depth, and evidence checks explicit.
- Make every handbook editable through plain files, Python APIs, and JSON CLI calls.
- Support both generated handbooks and manually curated handbooks.
- Preserve source grounding without forcing every task to load every source page.

## Artifact Layout

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

## Layer Responsibilities

- `manifest.json`: machine-readable table of contents, cross-links, counts, and paths.
- `GUIDE.md`: thick operating manual for how to use and maintain this handbook.
- `INDEX.md`: human-readable routing map across all categories and entries.
- `entry_skill/SKILL.md`: lightweight activation layer for systems that understand skills.
- `CATEGORY.md`: local routing page for one domain area.
- Entry pages: reusable guidance units with `Summary`, `Use When`, `Do This`, `Checklist`, `Anti-Patterns`, `Read Next`, and `Source Videos`.
- `references/glossary.md`: cross-entry vocabulary.
- `references/source_index.md`: source-to-entry reverse index.
- `evidence/*.md`: source-grounded supporting material.

## Skill Versus Handbook

A skill should stay short and action-oriented. A handbook can be thick because it is navigated progressively.

Use a skill when the user needs one stable procedure. Use a handbook when the agent must choose among many related concepts, examples, constraints, and evidence pages.

## Runtime Surfaces

- `patchouli-handbook init`: create a blank handbook scaffold.
- `patchouli-handbook build`: generate a handbook from cleaned source summaries.
- `patchouli-handbook validate`: check paths, counts, and cross-links.
- `patchouli-handbook apply`: run one machine-readable operation for agent integrations.
- `HandbookStore`: programmatic CRUD facade for categories and entries.

`init` is a CLI/library creation surface. It is not an `apply` operation because `apply` operates on an existing handbook directory.
