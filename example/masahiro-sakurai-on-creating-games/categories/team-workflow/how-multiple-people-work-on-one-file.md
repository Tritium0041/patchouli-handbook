---
title: "How Multiple People Work on One File"
entry_slug: "how-multiple-people-work-on-one-file"
category_slug: "team-workflow"
source_videos:
  - "s5u7VqDl-1I"
read_next:
  - "finish-everything-within-the-day"
---

# How Multiple People Work on One File

Category: Team Management & Workflow

## Summary
Files stored on server with lock/edit/unlock. Large files cause bottlenecks. Merge conflicts may require manual resolution; ancestor regression can occur.

## Use When
- Setting up version control or file sharing.

## Do This
1. Use VCS with file locking for binary assets. Lock before edit, unlock after commit. For large files, minimize simultaneous edits. Establish merging protocol. Keep backups.

## Checklist
- Version control chosen with locking support
- Team trained on lock/edit/unlock
- Conflict resolution documentation available
- Backup strategy in place

## Anti-Patterns
- Multiple people editing same file without locking
- No clear merging process
- Skipping backups

## Read Next
- [Finish Everything Within the Day](./finish-everything-within-the-day.md)

## Source Videos
- [s5u7VqDl-1I](../../evidence/s5u7VqDl-1I.md)
