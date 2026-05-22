---
title: "CRT Displays"
entry_slug: "crt-displays"
category_slug: "programming-tech"
source_videos:
  - "9FDDPZtWvhM"
read_next:
  - "knockback-in-super-smash-bros"
---

# CRT Displays

Category: Programming & Tech

## Summary
CRT monitors have unique properties: fast response, vibrant colors, interlaced scanning, visible scanlines. Understanding these helps in designing for retro or retro-styled games.

## Use When
- Designing for CRT hardware or emulating retro visuals.

## Do This
1. Use CRT's fast response to advantage; leverage interlaced scanning for 60fps with half bandwidth; be aware of safe frame areas.

## Checklist
- Account for safe frame (edges may be cropped)
- Design for interlaced if targeting NTSC
- Consider phosphor glow
- Test light gun functionality with CRT timing

## Anti-Patterns
- Assuming all displays behave like LCDs
- Ignoring scanlines in visual design

## Read Next
- [Knockback in Super Smash Bros.](./knockback-in-super-smash-bros.md)

## Source Videos
- [9FDDPZtWvhM](../../evidence/9FDDPZtWvhM.md)
