---
title: "Let Your Characters Shine"
entry_slug: "let-your-characters-shine"
category_slug: "visual-graphics"
source_videos:
  - "0ucvynuIe-o"
read_next:
  - "distinguishing-between-major-and-minor-elements"
  - "eight-hit-stop-techniques"
---

# Let Your Characters Shine

Category: Visual & Graphics

## Summary
Prevent effects from obscuring characters: in 2D, use higher render priority; in 3D, adjust depth test or render order. Use edge lights.

## Use When
- When effects risk hiding important gameplay elements.

## Do This
1. Ensure characters are always visible by adjusting rendering order, using edge lights, or dynamically controlling effect opacity.

## Checklist
- Character render priority above effects (2D)
- Use depth test adjustments to keep character topmost (3D)
- Add rim lights or outlines to character
- Test with all effects to ensure no occlusion

## Anti-Patterns
- Allowing effects to cover characters entirely
- Uniform depth without considering character visibility

## Read Next
- [Distinguishing Between Major and Minor Elements](./distinguishing-between-major-and-minor-elements.md)
- [Eight Hit Stop Techniques](../animation-motion/eight-hit-stop-techniques.md)

## Source Videos
- [0ucvynuIe-o](../../evidence/0ucvynuIe-o.md)
