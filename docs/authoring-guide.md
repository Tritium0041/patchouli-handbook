# Authoring Guide

This guide is for maintaining a Patchouli handbook by hand or through agents.

## What Belongs In A Handbook

Add material that is reusable across tasks:

- Concepts that help choose an approach.
- Decision rules with clear triggers.
- Checklists that catch repeated mistakes.
- Anti-patterns that prevent plausible failures.
- Evidence that explains where a claim came from.
- Links between nearby ideas.

Avoid one-off chat answers, vague inspiration, and raw dumps that have not been turned into guidance.

## Category Rules

A category should be a routing surface. Create one when several entries share the same user intent, domain, or decision context.

Each category needs:

- A clear title.
- A short description.
- `when_to_read` bullets.
- `core_terms` that help agents route queries.
- Entry links managed through `manifest.json` and the CLI.

## Entry Rules

Each entry should answer one reusable question pattern.

Required sections:

- `Summary`: the point of the entry.
- `Use When`: triggers that make this entry relevant.
- `Do This`: ordered guidance.
- `Checklist`: checks before the answer or work is done.
- `Anti-Patterns`: mistakes to avoid.
- `Read Next`: nearby entries to load only if needed.
- `Source Videos` or equivalent source references when evidence exists.

## Evidence Rules

Use evidence pages for provenance and examples. Do not force agents to read evidence pages for every ordinary task.

Evidence is most useful when:

- A claim could be disputed.
- A concrete source example matters.
- Two entries appear to conflict.
- The user asks where the guidance came from.

## Editing Workflow

Prefer the CLI or `HandbookStore` so manifest and markdown stay in sync.

```bash
patchouli-handbook categories list --handbook <handbook_dir>
patchouli-handbook entries create '{"title":"Scope First","category_slug":"planning","summary":"Decide scope before choosing tactics."}' --handbook <handbook_dir>
patchouli-handbook validate --handbook <handbook_dir>
```

Manual edits are acceptable, but run validation afterward.

