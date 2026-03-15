---
description: Git configuration rules for the Tabot project (ddapueto account)
globs: ["**/*"]
---

# Git Rules — Cuenta ddapueto

Este proyecto usa la cuenta **ddapueto** (personal), NO damiandapueto (empresa).

## SSH Config
- Host: `github.com` → key `~/.ssh/id_ed25519_personal` → cuenta **ddapueto**
- Host: `github-empresa` → key `~/.ssh/id_ed25519_empresa` → cuenta **damiandapueto**

## Remote URL
El remote de este proyecto DEBE usar:
```
git@github.com:ddapueto/tabot.git
```
NUNCA `github-empresa:...` — eso iria a la cuenta equivocada.

## Git Config Local (ya configurado)
```bash
git config user.name "ddapueto"
git config user.email "ddapueto@users.noreply.github.com"
```

## Commits
- Idioma: espanol
- Formato: `tipo: descripcion breve`
- Tipos: feat, fix, refactor, test, docs, ci, chore
- Siempre incluir trailer: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`

## Branches
- `main`: rama principal, siempre estable
- `feat/issue-N-descripcion`: features
- `fix/issue-N-descripcion`: bug fixes
- Cada PR debe referenciar su issue: `Closes #N`

## Push
Antes de push, verificar que el remote es correcto:
```bash
git remote -v
# Debe mostrar: git@github.com:ddapueto/tabot.git
```

## GitHub CLI (gh)
La CLI `gh` esta logueada como `damiandapueto`, NO como `ddapueto`.
Para operaciones en este repo, usar SSH + git directo para push/pull.
Para crear issues/milestones/PRs, usar `gh` con `--repo ddapueto/tabot`
(funciona porque el repo es publico).
