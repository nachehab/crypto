# OpenClaw Skills Loading Notes

## Skill directory precedence

1. `<workspace>/skills` (highest)
2. `~/.openclaw/skills`
3. bundled skills
4. `skills.load.extraDirs` (lowest precedence)

## Workspace convention for this repo

- Workspace skills are stored under `skills/<skill-name>/`.
- Each skill folder keeps its own `SKILL.md`, scripts, and wrappers.
- `SKILL.md` is not stored outside skill directories.

## Environment injection

Use `openclaw.json` skill entries instead of shell-only exports:

- `skills.entries.<skill>.env` for required env vars.
- `skills.entries.<skill>.apiKey` for primary API key mapping when supported.
