---
name: taf-media-library
description: Use this skill when a task plans or implements the future TAf media library for documents, videos, uploads, downloads, and persistent media storage.
---

# TAf Media Library

## When to use

Use for F038, F039, pedagogical supports, uploads, downloads, or local video
delivery planning.

## Inputs to read

- `AGENTS.md`
- relevant specs, roadmap notes, and any future media-related models, views,
  templates, or storage settings

## Rules

- Prefer `FileField` for managed uploads.
- Use persistent media storage volumes.
- Require source and license metadata.
- Keep draft media inaccessible publicly.
- Validate extension, size, MIME type, and checksum strategy.
- Plan for `/supports/`, `/supports/<slug>/`, and download/watch routes.
- Prefer native HTML `video` playback.
- Be cautious with heavy video over classroom Wi-Fi.
- Do not design heavyweight streaming in phase 1.

## Safe workflow

1. Distinguish documents from videos and draft from published assets.
2. Define access control before UI polish.
3. Confirm storage persistence and backup implications.
4. Validate that runtime media is not committed to git.

## Stop conditions

- public draft exposure risk
- unclear storage persistence
- large-video strategy exceeds local classroom constraints

## Acceptance checklist

- Media storage is persistent and bounded.
- Draft/public separation is explicit.
- Metadata and validation rules are present.
- Phase-1 scope avoids heavy streaming assumptions.
