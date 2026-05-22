---
title: "Flashing Effects"
entry_slug: "flashing-effects"
category_slug: "design-specifics"
source_videos:
  - "Mmw39T_dBLI"
read_next:
  - "always-keep-attack-collision-in-mind"
---

# Flashing Effects

Category: Design Specifics

## Summary
Flashing effects enhance feel and convey state. Contrast issues with additive blending; solutions like mixing with dark colors or adding shadows.

## Use When
- Implementing visual feedback for invincibility, stun, or hit reactions.

## Do This
1. Use color addition with attention to background brightness. Mix light and dark flashes for visibility. Adjust intensity based on camera distance. Color code (white for invincibility, yellow for throw immunity).

## Checklist
- Test flash visibility on various backgrounds
- Verify contrast: dark flash on bright background
- Set flash intensity proportional to camera distance
- Assign distinct colors for different states
- Consider display response times

## Anti-Patterns
- Pure additive flash on bright backgrounds
- Overly subtle flashes players may miss

## Read Next
- [Always Keep Attack Collision in Mind](../animation-motion/always-keep-attack-collision-in-mind.md)

## Source Videos
- [Mmw39T_dBLI](../../evidence/Mmw39T_dBLI.md)
