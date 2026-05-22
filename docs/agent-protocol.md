# Agent Protocol

This protocol defines how an AI agent should use a Patchouli handbook without loading the whole book.

## Default Flow

1. Read `entry_skill/SKILL.md` only to decide whether this handbook is relevant.
2. Read `GUIDE.md` when the task needs more than a quick lookup or when the handbook is unfamiliar.
3. Read `INDEX.md` and pick the smallest plausible category set.
4. Open exactly one `CATEGORY.md` first.
5. Open one or two entry pages.
6. Follow `Read Next` only when the current entry exposes a dependency.
7. Open evidence pages only when detail, examples, source verification, or conflict resolution are needed.

## Answer Rules

- Use the selected entries as guidance, not as text to restate.
- Name the category and entry files used when traceability matters.
- Separate source-backed claims from your interpretation when evidence pages were read.
- Say when no entry fits cleanly.
- Do not claim the handbook covers a topic just because a loosely related entry exists.

## Retrieval Budget

For ordinary tasks, use:

- `entry_skill/SKILL.md`
- `INDEX.md`
- one `CATEGORY.md`
- one or two entries

For complex or high-risk tasks, add:

- `GUIDE.md`
- linked `Read Next` entries
- relevant evidence pages
- glossary terms needed to resolve ambiguity

## Integration API

Use `patchouli-handbook apply` when an agent or external program needs a single JSON command surface.

```bash
patchouli-handbook apply '{"action":"get_entry","slug":"risk-and-reward"}' --handbook <handbook_dir>
```

Supported actions are declared by:

```bash
patchouli-handbook structure
```

Always run validation after write operations:

```bash
patchouli-handbook validate --handbook <handbook_dir>
```

