---
title: "Billboard Effects"
entry_slug: "billboard-effects"
category_slug: "design-specifics"
source_videos:
  - "_o29OOOarPY"
read_next:
  - "animation-interpolation"
---

# Billboard Effects

Category: Design Specifics

## Summary
Billboard technique: polygons always facing camera. Used for particles, explosions, and certain objects. Variations like Y-axis billboard and pitfalls.

## Use When
- Creating low-cost visual effects.

## Do This
1. Use full billboard for spherical effects; Y-axis billboard for cylindrical objects only when appropriate.

## Checklist
- Test billboard at extreme camera angles
- Ensure texture scaling correct
- Avoid Y-axis billboard for effects needing full 3D orientation

## Anti-Patterns
- Applying Y-axis billboard to flat effects without considering vertical angle
- Overusing billboards for objects needing depth

## Read Next
- [Animation Interpolation Pitfalls](../animation-motion/animation-interpolation.md)

## Source Videos
- [_o29OOOarPY](../../evidence/_o29OOOarPY.md)
