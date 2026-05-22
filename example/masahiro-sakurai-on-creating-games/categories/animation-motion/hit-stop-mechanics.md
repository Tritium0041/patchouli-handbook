---
title: "Hit Stop Mechanics"
entry_slug: "hit-stop-mechanics"
category_slug: "animation-motion"
source_videos:
  - "5MBxBsF6-vg"
read_next:
  - "eight-hit-stop-techniques"
---

# Hit Stop Mechanics

Category: Animation & Motion

## Summary
Hit stop is a brief pause on attack impact that dramatically improves combat feel. Ultimate implements seven special variations for nuanced feedback.

## Use When
- Designing combat or action games.

## Do This
1. Implement hit stop with: victim vibrates more, hitbox stays in place, ground vibration only horizontal, amplitude decays, adjustable coefficient per attack, victim pose blends over frames, attacker moves slightly during stop.

## Checklist
- Victim vibration larger than attacker
- Hitbox not displaced during stop
- Ground vs air vibration direction difference
- Amplitude decays gradually
- Distinct hit stop values for different attacks
- Victim pose blends slowly
- Attacker slides slightly on sword attacks
- Camera distance scales vibration

## Anti-Patterns
- Uniform hit stop for all attacks
- No vibration decay causing stuttery feel
- Hitbox shifting during stop causing phantom hits

## Read Next
- [Eight Hit Stop Techniques](./eight-hit-stop-techniques.md)

## Source Videos
- [5MBxBsF6-vg](../../evidence/5MBxBsF6-vg.md)
