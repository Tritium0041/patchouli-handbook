---
title: "Wind Cut Techniques"
entry_slug: "wind-cut-techniques"
category_slug: "design-specifics"
source_videos:
  - "tNRGqvCck6M"
read_next:
  - "screen-shake"
---

# Wind Cut Techniques

Category: Design Specifics

## Summary
Weapon trails (wind cuts) via polygonal trail meshes or billboard meshes along the path.

## Use When
- Implementing sword swings or fast-moving objects.

## Do This
1. For polygon trails, extrude geometry along path. For billboard, place quads at intervals with semi-transparent fade.

## Checklist
- Trail correctly follows movement
- Alpha fades gradually
- Does not obscure gameplay

## Anti-Patterns
- Trail persisting too long causing clutter
- Trail with hard edges instead of smooth fade

## Read Next
- [Screen Shake](./screen-shake.md)

## Source Videos
- [tNRGqvCck6M](../../evidence/tNRGqvCck6M.md)
