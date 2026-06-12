# AI Agent Skills

A personal, gradually growing collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Cursor](https://cursor.com) agent skills. Skills are added and refined over time — this repo is a living workspace, not a finished catalog.

**Repository:** [github.com/anarefin/ai-agent-skills](https://github.com/anarefin/ai-agent-skills)

## What's included (so far)

| Skill | Trigger / usage | Purpose |
|-------|-----------------|---------|
| [`graphify`](graphify/) | `/graphify` | Turn code, docs, papers, images, or video into a queryable knowledge graph |
| [`springboot-to-ears`](springboot-to-ears/) | `/springboot-to-ears` | Reverse-engineer a Spring Boot codebase into a standalone EARS specification |
| [`grails-to-ears`](grails-to-ears/) | `/grails-to-ears` | Reverse-engineer a Grails 2.5.x codebase into a standalone EARS specification |
| [`resolve-open-questions`](resolve-open-questions/) | `/resolve-open-questions <file>` | Second-pass resolver for `[NEEDS REVIEW]` items in a Spring Boot EARS spec |
| [`ears-gap-fix`](ears-gap-fix/) | `/ears-gap-fix <file>` | Third-pass gap closer for Spring Boot EARS specs (missing rules and data model) |
| [`fix-dev-reviews`](fix-dev-reviews/) | `/fix-dev-reviews <file>` | Fourth-pass closer for developer review sections in Spring Boot EARS specs |
| [`grails-ears-gap-fix`](grails-ears-gap-fix/) | `/ears-gap-fix <file>` | Third-pass gap closer for Grails EARS specs |
| [`grails-fix-dev-reviews`](grails-fix-dev-reviews/) | `/fix-dev-reviews <file>` | Fourth-pass closer for developer review sections in Grails EARS specs |
| [`ears-to-ddd`](ears-to-ddd/) | `/ears-to-ddd <file>` | Convert a layered-architecture EARS spec into DDD/CQRS/Event Sourcing |
| [`prompt-master`](prompt-master/) | (auto on prompt requests) | Generate optimized prompts for LLMs, coding agents, and image/video tools |

More skills will be added here as they are written or adapted.

## EARS pipeline

For legacy codebases, these skills are meant to run in sequence:

```
springboot-to-ears  or  grails-to-ears
        ↓
resolve-open-questions   (optional — first pass often auto-resolves many items)
        ↓
ears-gap-fix             (third pass — code gaps)
        ↓
fix-dev-reviews          (fourth pass — human review sections)
        ↓
ears-to-ddd              (optional — architectural rewrite)
```

Each skill folder contains a `SKILL.md` with full invocation details, rules, and output format.

## Installation

### Claude Code

Clone or copy skill folders into your Claude skills directory:

```bash
git clone https://github.com/anarefin/ai-agent-skills.git ~/.claude/skills-repo

# Symlink individual skills (add more as you adopt them)
ln -s ~/.claude/skills-repo/graphify ~/.claude/skills/graphify
ln -s ~/.claude/skills-repo/springboot-to-ears ~/.claude/skills/springboot-to-ears
```

Or copy only the skills you need:

```bash
cp -R graphify springboot-to-ears ~/.claude/skills/
```

### Cursor

Copy or symlink skill folders into Cursor's skills path:

```bash
cp -R graphify ~/.cursor/skills-cursor/graphify
```

Cursor discovers skills from `~/.cursor/skills-cursor/` and project-level `.cursor/skills/`.

## Adding a new skill

1. Create a folder with a `SKILL.md` file (YAML frontmatter + instructions).
2. Add the folder to this repo and update the table in this README.
3. Symlink or copy it into `~/.claude/skills/` or `~/.cursor/skills-cursor/`.

See [Anthropic's skill authoring guide](https://docs.anthropic.com/en/docs/claude-code/skills) or Cursor's skill docs for the `SKILL.md` format.

## Local-only setup (not in this repo)

Some skills on my machine are **symlinks** to `~/.agents/skills/` (for example, the `caveman` family). Those are machine-local and excluded via `.gitignore`. They are not part of this repository.

## Third-party skills

- **prompt-master** — vendored from [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master). See [`prompt-master/README.md`](prompt-master/README.md) for upstream docs and license.

## Generated artifacts

Running certain skills produces output that should stay out of version control:

| Artifact | Produced by |
|----------|-------------|
| `graphify-out/` | `/graphify` |
| `raw/` | `/graphify add` |
| `*.original.md` | caveman-compress (local) |
| `docs/ears/*.md` | EARS extraction skills (written in target projects) |

These paths are listed in [`.gitignore`](.gitignore).

## License

Skills in this repo may carry their own licenses (see per-folder `LICENSE` files where present). The collection as a whole is maintained for personal use and gradual sharing.
