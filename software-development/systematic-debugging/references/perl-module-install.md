# Perl Module Installation (user-writable)

## Problem

Installing Perl modules via `Makefile.PL && make install` fails with:

```
ERROR: Can't create '/usr/local/man/man3'
mkdir /usr/local/man/man3: Permission denied
```

The Makefile hardcodes man directory paths even when `PREFIX=` or `INSTALLMAN3DIR=` are passed.

## Solution

Bypass `make install` entirely. Use `ExtUtils::Install` directly to copy only the library files to a user-writable location:

```bash
perl -I. -MExtUtils::Install -e 'install({ "blib/lib" => "$HOME/perl5/lib" })'
```

This installs everything under `blib/lib` to the target directory without touching any man pages.

## Step-by-step

```bash
# 1. Build the module
perl Makefile.PL && make

# 2. Install libs to user directory (skip man pages)
perl -I. -MExtUtils::Install -e 'install({ "blib/lib" => "$HOME/perl5/lib" })'

# 3. Use the module
PERL5LIB=$HOME/perl5/lib perl -M<ModuleName> -e '...'
```

For Jcode specifically:
```bash
perl -I. -MExtUtils::Install -e 'install({ "blib/lib" => "/home/thomas/perl5/lib" })'
PERL5LIB=/home/thomas/perl5/lib perl -MJcode -e 'print Jcode->new("日本語")->utf8'
```

## Persist PERL5LIB

Add to shell profile:
```bash
echo 'export PERL5LIB=$HOME/perl5/lib' >> ~/.bashrc
source ~/.bashrc
```

Or use inline for one-off commands:
```bash
PERL5LIB=$HOME/perl5/lib perl -MMyModule ...
```

## Why the Makefile approaches fail

| Approach | Why it fails |
|----------|-------------|
| `make install PREFIX=$HOME` | Makefile still hardcodes `INSTALLMAN3DIR=/usr/local/man/man3` |
| `make install INSTALLSITEMAN=''` | Same — man dir is hardcoded, not configurable via these vars |
| `make install INSTALLMAN3DIR=''` | Some Makefiles ignore empty string and fall back to default |

Direct `ExtUtils::Install` call is the only reliable approach when you lack write access to `/usr/local`.

## Other user-writable Perl lib dirs

If `$HOME/perl5/lib` conflicts with something, alternatives:
- `$HOME/perl/lib`
- `$HOME/.local/lib/perl5`
- Any writable directory — just set `PERL5LIB` accordingly.