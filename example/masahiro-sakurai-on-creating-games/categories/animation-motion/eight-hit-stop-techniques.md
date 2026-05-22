---
title: "Eight Hit Stop Techniques"
entry_slug: "eight-hit-stop-techniques"
category_slug: "animation-motion"
source_videos:
  - "tycbMSjDDLg"
read_next:
  - "breaking-down-attack-animations"
---

# Eight Hit Stop Techniques

Category: Animation & Motion

## Summary
Details seven special hit stop techniques used in Super Smash Bros. Ultimate: larger shake on receiver, no hitbox offset, directional shake control, amplitude decay, adjustable pause length, smooth pose transition, slight attacker movement.

## Use When
- Designing hit reactions for action game.

## Do This
1. Implement hit stop with asymmetric shake, keep hitboxes fixed, limit ground shake to horizontal, decay amplitude, adjust pause length per attack, blend hit pose over ~4 frames, allow minimal attacker drift.

## Checklist
- Receiver shakes more than attacker
- Hitbox does not move with shake
- Ground shake only horizontal; air shake omnidirectional
- Amplitude decays gradually
- Hit stop length tunable per attack
- Hit pose transitions smoothly
- Attacker has slight movement

## Anti-Patterns
- Hitboxes shifting with screen shake
- Constant amplitude
- No pause on hit
- Attacker frozen completely

## Read Next
- [Breaking Down Attack Animations](./breaking-down-attack-animations.md)

## Source Videos
- [tycbMSjDDLg](../../evidence/tycbMSjDDLg.md)
