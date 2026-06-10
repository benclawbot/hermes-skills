# Shell Initialization on Ubuntu (Mac hardware)

Thomas's environment: Ubuntu Linux on MacBook Air. Shell is `bash`. The standard login-shell initialization chain is broken for non-interactive terminals.

## The Problem

When Thomas opens a new terminal (`gnome-terminal`), it starts as a **login shell** → runs `.bash_profile` → runs `.profile` → runs `.bashrc`.

But `.bashrc` has the standard interactive-guard at the top:

```bash
case $- in
    *i*) ;;
      *) return;;
esac
```

So login shells — which have `$-` without `i` — hit `return` before ever sourcing `.bash_aliases`. Result: all aliases (including `generic`) are **not found** in new terminal sessions.

## The Fix Applied

Sourced `.bash_aliases` from two places that bypass the `.bashrc` interactive gate:

1. **`.profile`** — sourced by login shells before `.bashrc` decision:
```bash
# Load bash aliases (for both interactive and login shells)
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
```

2. **`.bash_profile`** — also sources `.bashrc` for interactive login shells:
```bash
# Load .bashrc for interactive shells
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
```

## Verification

```bash
bash -l -c "alias generic 2>/dev/null && echo 'works' || echo 'not found'"
# Expected: works
```

## When Adding New Aliases

All aliases go in `~/.bash_aliases` only. Do NOT add to `.bashrc` or `.profile` directly — that creates duplicate sourcing paths and maintenance mess. `.bash_aliases` is the single source of truth for user aliases.

## Other Affected Machines

This issue affects any Ubuntu/Linux system where:
- Terminal emulators start as **login shells** (not interactive non-login)
- `.bashrc` has the standard `case $-` guard
- `.profile` doesn't explicitly source `.bash_aliases`

On Arch/Manjaro the guard logic may differ. On macOS default Terminal.app, the shell is `zsh` — aliases go in `~/.zshrc` instead.