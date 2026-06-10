---
name: security-audit
description: "Full-suite machine security audit — multi-dimensional scan across OS, services, ports, firewall, users, cron, packages, and malware defense."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [security, audit, hardening, firewall, malware, linux]
    related_skills: [systematic-debugging]
---

# Security Audit

## Overview

A thorough, repeatable security audit of a Linux machine. Structured as a checklist — run all checks, then act on findings by severity.

**Target:** Ubuntu/Debian-based Linux. Adjust commands for other distros.

## When to Use

- User asks for a security audit
- After any infrastructure change (new packages, services, firewall rules)
- Before exposing a machine to the public internet
- Periodic hygiene (quarterly recommended)

## The Audit Checklist

Run ALL checks before proposing any fixes. Do not patch mid-audit.

### 1. OS & Kernel
```bash
uname -a
cat /etc/os-release | head -5
uptime
```

### 2. Running Services
```bash
ps aux --sort=-%cpu | head -20
systemctl --type=service --state=running --no-pager
```
Flag: unexpected services, processes running as root, high CPU usage.

### 3. Open Ports
```bash
ss -tulnp
# or: netstat -tulnp
```
Flag: ports on 0.0.0.0 (all interfaces) that should be localhost-only.

### 4. Port → Process Mapping (for suspicious ports)
```bash
sudo lsof -i :PORT
# Example: sudo lsof -i :40783
```
Shows PID, user, and command for each listener.

### 5. Firewall Status
```bash
sudo iptables -L -n
sudo ufw status verbose
```
Flag: INPUT policy ACCEPT (dangerous), no ufw installed.

### 6. User Accounts & Sudoers
```bash
getent group sudo
getent group wheel
cat /etc/passwd | grep -E ":(0|1000):"
```
Flag: root login enabled, password-less sudo, unexpected users.

### 7. SSH Configuration
```bash
cat /etc/ssh/sshd_config | grep -E "^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|PermitEmptyPasswords|Port)"
```
Flag: PermitRootLogin yes, PasswordAuthentication yes, no PubkeyAuthentication.

### 8. Cron Jobs
```bash
ls -la /etc/cron.d/ /etc/cron.daily/ /etc/cron.hourly/
crontab -l
```
Flag: unexpected cron entries, scripts calling unknown binaries.

### 9. Setuid Binaries
```bash
find /usr -perm -4000 -type f 2>/dev/null
```
Flag: unexpected suid binaries, especially in /usr/local.

### 10. World-Writable Files (outside home/tmp)
```bash
find / -perm -002 -type f 2>/dev/null | grep -v proc | grep -v sys | grep -v "/home/thomas" | grep -v "/run/user" | grep -v "/tmp"
```
Flag: any world-writable system files.

### 11. Recently Modified Binaries
```bash
find /usr/bin /usr/sbin /bin /sbin -mtime -7 -type f 2>/dev/null
```
Flag: unexpected binary modifications in last week.

### 12. Package Security
```bash
dpkg -l | grep -E "^ii.*$(uname -r)"
apt list --upgradable
systemctl status unattended-upgrades
```
Flag: out-of-date kernel/headers, unattended-upgrades not running.

### 13. Malware Scanners
```bash
which chkrootkit rkhunter clamscan 2>/dev/null
rkhunter --version 2>/dev/null || echo "rkhunter: not installed"
```
Flag: none installed — high risk for a machine exposed to internet.

### 14. Docker Containers
```bash
docker ps -a
docker port --all
ss -tulnp | grep docker
```
Flag: unexpected containers, Docker listening on unexpected ports.

### 15. Login Failures
```bash
grep -c "Failed password" /var/log/auth.log 2>/dev/null || grep -c "Failed password" /var/log/secure 2>/dev/null || echo "Cannot read auth log"
last -20
```
Flag: many failed logins, unexpected login sources.

### 16. NTP / Time Sync
```bash
timedatectl
chronyc tracking 2>/dev/null | head -5
```
Flag: time not synchronized, large offset — can indicate tampering or misconfiguration.

## Output Format

```
## Security Audit — HOSTNAME

### 🔴 HIGH RISK
[findings]

### 🟡 MODERATE
[findings]

### 🟢 GOOD
[findings]

## Recommendations (priority order)
1. [highest priority fix]
2. ...
```

Sort by risk severity. Include exact commands in the fix section.

## Post-Audit Actions

### High Risk → Fix immediately
1. Enable firewall: `sudo ufw default deny incoming && sudo ufw allow 22/tcp && sudo ufw enable`
2. Bind exposed services to 127.0.0.1 if not needed externally
3. Install malware scanners: `sudo apt install -y rkhunter chkrootkit`

### Moderate → Fix within 24h
1. Disable unused services (`systemctl disable --now avahi-daemon`)
2. Investigate unknown listening ports
3. Remove world-writable files outside home/tmp

### Informational → Fix at next maintenance window
1. Configure apparmor profiles
2. Set up periodic rootkit scans via cron
3. Review sudo group membership

## Common Findings Reference

See `references/common-findings.md` for known patterns and their severity assessment.

## Pitfalls

### Always identify the process behind a port before deciding if it's risky

`ss -tulnp` shows a port is open → immediately run `sudo lsof -i :PORT` to identify the owning process. A port on 0.0.0.0 is not necessarily bad — it depends on WHAT is listening.

Example: `containerd` (Docker runtime) on localhost:40783 is normal and expected. A random Python script binding to 0.0.0.0 is bad.

### Don't trust a service name — verify the binary path

A process named "python3" could be the PM dashboard server or something else. Use `ps aux | grep PID` to see the full command line, or `ls -la /proc/PID/exe` for the actual binary.

### ufw delete requires interactive confirmation

`sudo ufw delete N` prompts for `y` confirmation. In script context, it blocks. Workaround: delete rules by number in REVERSE order (delete highest numbers first so numbers don't shift), or use `sudo ufw delete allow PORT/tcp` (by service name). Do NOT pipe to stdin — the agent blocks `sudo -S` via stdin.

### dpkg interrupted — fix first before installing new packages

If `apt install` reports `dpkg was interrupted`, run `sudo dpkg --configure -a` before any further installs. Failure to do this leaves the package manager in a broken state.

### Firewall rules persist across reboots but aren't tracked in dotfiles

ufw rules are live immediately but aren't git-tracked. If you configure firewall rules, document them in a reference file or dotfiles repo so they can be reproduced on a fresh install.