# AGENTS.md

This repository is maintained with help from AI coding agents.
This document defines how an agent should behave when working here.

If something is unclear, prefer the smallest safe change and leave a short note with assumptions.

## Core working agreements

- Keep changes small, focused, and directly relevant to the requested task.
- Prefer existing patterns in the repository over introducing new abstractions.
- Do not add new dependencies unless explicitly requested.
- Do not perform broad architecture changes unless explicitly requested.
- Do not edit generated/derived files by hand (see below).
- Do not commit secrets or credentials.
- Avoid unrelated refactors or formatting-only churn.
- If behavior changes, verify impact with at least one local sanity check.

## Definition of done

A task is complete when:

- The requested behavior is implemented.
- Existing behavior outside the task remains unaffected.
- Relevant docs/config are updated when behavior or workflow changes.
- A local sanity check was run (see Validation).
- No unrelated files were modified.

## Validation

Use the following checks as relevant:

- Unit/integration tests: `make test` (or `uv run --group dev pytest`)
- Syntax/import check: `python3 -m compileall main.py game`
- Run game manually (when needed): `make run`
- Build smoke check for packaging tasks (macOS): `make build`

## Generated / derived files (do not edit by hand)

These are generated or build outputs and should not be manually edited:

- `build/**`
- `dist/**`
- `__pycache__/**`
- `asteroids.spec` (PyInstaller-generated in current workflow)
- `.release/**` (release script output)

If a generated artifact needs changes, update its source inputs or build command instead.

## Project layout (current)

- `main.py` - Entrypoint and game state machine (`menu`, `playing`, `game_over`)
- `game/config/` - Constants and tuning values
- `game/core/` - Shared base entities (`CircleShape`)
- `game/entities/` - Gameplay entities (`Player`, `Asteroid`, `Shot`, `Explosion`)
- `game/systems/` - Systems/spawners (`AsteroidField`)
- `game/render/` - Rendering/presentation and startup loading
- `game/utils/` - Resource pathing and logging helpers
- `images/` - Backgrounds/menu/loading UI imagery
- `sprites/` - Entity sprites and variants
- `scripts/release.py` - SemVer + changelog/release note preparation
- `.github/workflows/release.yml` - Manual release + cross-platform binary pipeline

## Workflow conventions

- Dependency/runtime tooling: `uv`
- Common dev commands: `make sync`, `make run`, `make build`, `make open`
- Keep game tunables in `game/config/constants.py` rather than hardcoding in entities/renderers.
- Reuse `game/utils/resources.py` (`asset_path`, `asset_glob`) for asset lookups.
- Preserve fixed game viewport composition (centered game area + optional border framing).

## Packaging and release conventions

- Release flow is manual via GitHub Actions `workflow_dispatch`.
- SemVer/changelog are driven by `scripts/release.py` and commit messages.
- Binary packaging uses PyInstaller and bundles `images/` + `sprites/`.
- Do not modify release/tag automation behavior unless explicitly requested.

## Safety rules

- Never expose tokens, secrets, or local credential files.
- Never remove gameplay guards/validations without explicit instruction.
- Avoid destructive git commands unless explicitly requested.
- Git commits/tags/releases are performed by humans unless explicitly delegated.

## When in doubt

- Choose the least invasive solution.
- Keep momentum with pragmatic, reversible changes.
- Leave a short note on assumptions, follow-up checks, or tradeoffs.
