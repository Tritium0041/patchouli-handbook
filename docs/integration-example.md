# Minimal Integration Example

This document shows the smallest useful integration pattern for an external agent or program that wants to use a Patchouli handbook through the CLI.

The pattern is:

1. Discover the handbook shape.
2. Describe the target handbook.
3. Select a category and entry.
4. Read only the selected entry.
5. Optionally write a small update.
6. Validate after every write.

Use `patchouli-handbook apply` when the caller wants one stable JSON command surface. Use the direct subcommands when a human is operating the handbook by hand.

## Example Handbook

The commands below use the included example handbook:

```bash
HANDBOOK=example/masahiro-sakurai-on-creating-games
```

For a generated or custom handbook, replace `HANDBOOK` with that handbook directory.

## 1. Discover Supported Operations

Call `structure` once at startup or during capability discovery.

```bash
patchouli-handbook structure
```

The response declares the file layout and supported operations. An external agent should treat this as the contract instead of hard-coding every path.

## 2. Describe The Handbook

Use `describe` to get counts and basic identity before reading content.

```bash
patchouli-handbook apply '{"action":"describe"}' --handbook "$HANDBOOK"
```

Typical response shape:

```json
{
  "structure": {
    "format_name": "patchouli-handbook",
    "manifest_path": "manifest.json",
    "guide_path": "GUIDE.md",
    "index_path": "INDEX.md"
  },
  "book_title": "Masahiro Sakurai on Creating Games Patchouli Handbook",
  "book_slug": "masahiro-sakurai-on-creating-games-patchouli-handbook",
  "category_count": 14,
  "entry_count": 260,
  "source_video_count": 299
}
```

## 3. Pick A Category

List categories and select the smallest one that matches the user task.

```bash
patchouli-handbook apply '{"action":"list_categories"}' --handbook "$HANDBOOK"
```

An agent should use the returned `title`, `description`, `when_to_read`, and `core_terms` fields to choose a category. It should not load every entry in the handbook.

## 4. Pick And Read An Entry

List entries in the selected category:

```bash
patchouli-handbook apply '{"action":"list_entries","category_slug":"player-experience"}' --handbook "$HANDBOOK"
```

Then fetch one entry:

```bash
patchouli-handbook apply '{"action":"get_entry","slug":"respecting-player-time"}' --handbook "$HANDBOOK"
```

Use the returned fields as guidance:

- `summary`: the narrow purpose of the entry.
- `use_when`: when the entry applies.
- `do_this`: the action sequence to adapt to the user's task.
- `checklist`: completion checks.
- `anti_patterns`: plausible mistakes to avoid.
- `read_next`: optional next entries when the first entry exposes a dependency.
- `source_videos`: evidence pages to open only when source detail is needed.

## 5. Answer From The Selected Entry

The caller should keep its answer grounded in the selected entry without restating the whole handbook.

Recommended answer metadata:

```json
{
  "handbook": "example/masahiro-sakurai-on-creating-games",
  "category_slug": "player-experience",
  "entry_slug": "respecting-player-time",
  "evidence_opened": []
}
```

Open evidence only when the task needs source verification, examples, or conflict resolution:

```bash
cat "$HANDBOOK/evidence/<video_id>.md"
```

## 6. Write A Small Update

For machine callers, write through `apply` so each operation stays a single JSON object.

Create the target handbook first if it does not exist yet:

```bash
patchouli-handbook init \
  --output output/studio-handbook \
  --title "Studio Handbook" \
  --audience "AI agents and studio maintainers"
```

Create a category:

```bash
patchouli-handbook apply '{
  "action": "create_category",
  "payload": {
    "title": "Planning",
    "description": "Scoping, goals, and project framing.",
    "when_to_read": ["Use when a task needs project framing before tactics."],
    "core_terms": ["scope", "constraints", "success criteria"]
  }
}' --handbook output/studio-handbook
```

Create an entry:

```bash
patchouli-handbook apply '{
  "action": "create_entry",
  "payload": {
    "title": "Scope First",
    "category_slug": "planning",
    "summary": "Decide the scope before choosing tactics.",
    "use_when": ["The task is broad or under-specified."],
    "do_this": ["Name the goal.", "Name constraints.", "Pick the smallest useful next step."],
    "checklist": ["The scope is explicit.", "The next action is concrete."],
    "anti_patterns": ["Do not choose tactics before defining the target."]
  }
}' --handbook output/studio-handbook
```

## 7. Validate After Every Write

Always validate after create, update, or delete operations:

```bash
patchouli-handbook apply '{"action":"validate"}' --handbook output/studio-handbook
```

Treat `ok: false` as a failed integration step. CLI errors also return JSON:

```json
{
  "ok": false,
  "error": {
    "type": "KeyError",
    "message": "'Unknown entry: missing-entry'"
  }
}
```

## Minimal Agent Loop

This is the full loop in compact form:

```text
user task
  -> structure
  -> describe handbook
  -> list_categories
  -> select one category
  -> list_entries for that category
  -> get_entry for one or two entries
  -> optionally read evidence
  -> answer using selected entries
  -> if writing, apply one JSON operation
  -> validate
```

The important constraint is progressive disclosure: the integration should select the smallest useful category and entry set instead of reading the whole handbook.
