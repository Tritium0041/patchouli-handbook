---
title: "The Limitations of Particle Effects"
entry_slug: "the-limitations-of-particle-effects"
category_slug: "design-specifics"
source_videos:
  - "jAQv4PTQvQE"
read_next:
  - "h-effects-1"
---

# The Limitations of Particle Effects

Category: Design Specifics

## Summary
Particle effects can strain performance; optimize by shortening lifespan, staggering spawn times, using pre-baked animation frames instead of real-time particles.

## Use When
- Implementing particle systems on limited hardware.

## Do This
1. Shorten particle life; offset emission times; reuse sprites; consider sprite sheets for complex effects.

## Checklist
- Set lifespan to minimum needed
- Stagger spawn to avoid peak counts
- Use additive blending to hide repetition?
- Pre-bake high-density animations as flipbooks

## Anti-Patterns
- Letting particles live too long
- Firing all particles simultaneously
- Relying on polygons for simple effects

## Read Next
- [H: Effects 1 (Category Compilation)](./h-effects-1.md)

## Source Videos
- [jAQv4PTQvQE](../../evidence/jAQv4PTQvQE.md)
