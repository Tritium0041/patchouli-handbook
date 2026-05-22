---
title: "Damage Animation Transition"
entry_slug: "damage-animation-transition"
category_slug: "animation-motion"
source_videos:
  - "vj-PewTwDV0"
read_next:
  - "extreme-keyframes"
---

# Damage Animation Transition

Category: Animation & Motion

## Summary
When a character takes damage, the first frame of damage animation should be hit instantly (often via hit stop), then transition smoothly via interpolation from hit pose.

## Use When
- Creating hit reaction animations.

## Do This
1. Design the damage animation's first frame as an extreme pose (pain). Use hit stop to hold that pose briefly, then blend smoothly.

## Checklist
- First frame of damage animation clearly readable (pain pose)
- Hit stop provides enough time to see first frame
- Transition from hit pose to damage animation smooth

## Anti-Patterns
- No hit stop making first frame invisible
- Instant snap to damage animation without interpolation

## Read Next
- [Extreme Keyframes for Sharp Animation](./extreme-keyframes.md)

## Source Videos
- [vj-PewTwDV0](../../evidence/vj-PewTwDV0.md)
