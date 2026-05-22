# Masahiro Sakurai on Creating Games Guide

This guide explains how an AI agent should use this handbook as a thick reference system, not as a single behavior script.

## Mental Model
- `entry_skill/SKILL.md` is the lightweight activation layer.
- `INDEX.md` is the map for routing a user request to the right category.
- `categories/<category_slug>/CATEGORY.md` narrows the local search space.
- `categories/<category_slug>/<entry_slug>.md` contains reusable guidance, checks, and failure modes.
- `references/glossary.md` defines terms that apply across entries.
- `references/source_index.md` and `evidence/<source_id>.md` ground guidance in source material.

## Reading Protocol
1. Start with `entry_skill/SKILL.md` only to confirm the handbook is relevant.
2. Read `INDEX.md` and choose the smallest plausible set of categories.
3. Open one category page and select one or two entries before reading deeper.
4. Use `read_next` links when the first entry exposes a nearby dependency.
5. Open evidence pages only for examples, conflicts, source checks, or high-stakes claims.

## Answer Protocol
- State the category and entry files that shaped the answer when the user needs traceability.
- Convert handbook guidance into the user's concrete context instead of restating sections verbatim.
- Separate source-backed claims from interpretation when the answer depends on evidence pages.
- Prefer focused, actionable recommendations over broad summaries of the whole book.
- If no entry fits, say so and use the closest category only as loose background.

## Maintenance Protocol
- Add a category only when several entries need a shared routing surface.
- Add an entry when there is a stable reusable judgment pattern, not just a one-off note.
- Keep each entry self-contained enough to answer a narrow task after it is selected.
- Link related entries with `read_next` instead of duplicating the same guidance.
- Add evidence when a claim needs provenance, concrete examples, or conflict resolution.

## Routing Rules
1. If query is about core game mechanics, risk-reward, difficulty, or player motivation, route to 'Game Essence' or 'Game Design Principles'.
1. If query is about UI, controls, menus, or accessibility, route to 'UI/UX Design'.
1. If query is about graphics, effects, or visual polish, route to 'Visual & Graphics'.
1. If query is about animation, character motion, or hit feedback, route to 'Animation & Motion'.
1. If query is about sound effects, music, or audio design, route to 'Audio Design'.
1. If query is about player experience, tutorials, or time management, route to 'Player Experience'.
1. If query is about development workflow, project management, or technical tools, route to 'Development Insights'.
1. If query is about team leadership, communication, or team culture, route to 'Team Management & Workflow'.
1. If query is about personal productivity, creative process, or professional attitude, route to 'Work Ethic & Mindset'.
1. If query is about marketing, trailers, or community engagement, route to 'Marketing & Communication'.
1. If query is about programming practices, parameter tuning, or debugging, route to 'Programming & Tech'.
1. If query is about specific design techniques like hit stop, screen shake, or explosion effects, route to 'Design Specifics'.
