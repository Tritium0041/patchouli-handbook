---
title: "Parameter Externalization"
entry_slug: "parameter-externalization"
category_slug: "development-insights"
source_videos:
  - "dyqKV_oZFMo"
read_next:
  - "ticket-system"
---

# Parameter Externalization

Category: Development Insights

## Summary
Store tunable numbers in external files like Excel, not hard-coded, to allow quick iteration without recompiling.

## Use When
- Implementing any system with adjustable values.

## Do This
1. Create Excel sheet with all parameters. Use formulas for derived values. Mark parameterized locations in design docs with brackets.

## Checklist
- Identify all magic numbers in code
- Move to separate data file or spreadsheet
- Set up pipeline to convert Excel to in-game data
- Document parameters and ranges

## Anti-Patterns
- Hard-coding values 'just for now'
- Forgetting to externalize values that will later need tuning

## Read Next
- [Ticket System](./ticket-system.md)

## Source Videos
- [dyqKV_oZFMo](../../evidence/dyqKV_oZFMo.md)
