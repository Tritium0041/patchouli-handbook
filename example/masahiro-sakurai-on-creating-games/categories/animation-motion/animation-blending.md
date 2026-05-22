---
title: "Animation Blending"
entry_slug: "animation-blending"
category_slug: "animation-motion"
source_videos:
  - "HYHajZ0wBfU"
read_next:
  - "motion-blur"
---

# Animation Blending

Category: Animation & Motion

## Summary
Blend animations to create smooth transitions. Keep blend times short (0.1-0.3s) to preserve crispness. In 3D, use layered blending.

## Use When
- Implementing character movement, combat, or interactions.

## Do This
1. Set blend times in state machine; test to avoid floaty feel. Use blend spaces for multi-directional movement. Separate upper body for aiming.

## Checklist
- Transitions smooth without being sluggish
- Blend times consistent across actions
- For 3D: upper body animation overrides lower appropriately

## Anti-Patterns
- Too much blending making actions mushy
- Sudden cuts without blending causing jarring stops
- Mixing animations with incompatible root motion

## Read Next
- [Motion Blur](./motion-blur.md)

## Source Videos
- [HYHajZ0wBfU](../../evidence/HYHajZ0wBfU.md)
