---
title: "Particle Optimization"
entry_slug: "particle-optimization"
category_slug: "design-specifics"
source_videos:
  - "tNRGqvCck6M"
read_next:
  - "screen-shake"
---

# Particle Optimization

Category: Design Specifics

## Summary
Optimize particle effects by shortening lifetime, increasing speed, using composite particles, offsetting emission times, avoiding overlap.

## Use When
- Dealing with large numbers of particles impacting frame rate.

## Do This
1. Reduce lifetime and speed. Combine multiple effects onto one polygon (composite). Issue at staggered times. Scale up size slightly.

## Checklist
- Particle lifetime as short as acceptable
- Composite particles used where possible
- Emission times offset
- Overlap minimized
- Size appropriate

## Anti-Patterns
- Long-lived particles clogging screen
- All particles emitted simultaneously
- Overlapping creating solid blobs

## Read Next
- [Screen Shake](./screen-shake.md)

## Source Videos
- [tNRGqvCck6M](../../evidence/tNRGqvCck6M.md)
