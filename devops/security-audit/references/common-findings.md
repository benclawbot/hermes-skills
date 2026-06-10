# Security Audit — Common Findings Reference

Quick severity reference for findings frequently encountered on Thomas's machine (Ubuntu, desktop use, Hermes gateway running).

## High Risk Findings

| Finding | Severity | Action |
|---------|----------|--------|
| iptables INPUT policy = ACCEPT | 🔴 HIGH | Install and enable ufw: `sudo ufw default deny incoming && sudo ufw enable` |
| Service binding to 0.0.0.0 on a high port (>8000) | 🔴 HIGH | Bind to 127.0.0.1 or firewall the port with ufw |
| No malware scanners installed | 🔴 HIGH | `sudo apt install -y rkhunter chkrootkit` |
| SSH server running with password auth | 🔴 HIGH | Disable password auth in sshd_config, use key-based auth only |
| Unknown process on a high port | 🔴 HIGH | `sudo lsof -i :PORT` → identify binary → research if legitimate |

## Moderate Risk Findings

| Finding | Severity | Action |
|---------|----------|--------|
| apparmor loaded but no enforce/complain profiles | 🟡 MODERATE | Investigate what should be confined; enable profiles |
| Docker/containerd running but no containers used | 🟡 MODERATE | Consider `systemctl disable --now docker` if unused |
| avahi-daemon (mDNS/Bonjour) running | 🟡 MODERATE | `systemctl disable --now avahi-daemon` if not using AirDrop/zeroconf |
| cups-browsed.service running | 🟡 MODERATE | Historically a local privesc vector; disable if no network printing |
| sudo group membership for desktop user | 🟡 MODERATE | Normal on single-user desktops — acceptable, document only |
| Unknown port listening on localhost only | 🟡 MODERATE | Verify with `sudo lsof -i :PORT` — if containerd/docker, normal |
| World-writable files in home directory | 🟡 MODERATE | Usually venv locks or npm cache — benign, ignore |
| User crontabs disabled | 🟡 MODERATE | Check if any automation was intentionally disabled — may need restoring |

## Good Findings (no action needed)

| Finding | Status |
|---------|--------|
| unattended-upgrades.service active and running | ✅ Good |
| chrony NTP sync healthy (stratum 3, <1ms offset) | ✅ Good |
| No failing login attempts in auth log | ✅ Good |
| Kernel and headers up to date | ✅ Good |
| No held packages | ✅ Good |
| No recently modified system binaries | ✅ Good |
| No root login available | ✅ Good |
| SSH not installed or not listening | ✅ Good |

## Port Reference (Thomas's Machine)

| Port | Process | Risk | Notes |
|------|---------|------|-------|
| 22 | sshd (if installed) | 🔴 if open to internet | Should be restricted or key-only |
| 53 | systemd-resolved | ✅ | localhost DNS resolver |
| 631 | cupsd | 🟡 | CUPS printing — disable if no network printer |
| 8765 | pm-dashboard-server.py | ✅ | Now bound to 127.0.0.1 (was 8766 on 0.0.0.0) |
| 40783 | containerd (Docker) | ✅ | Docker runtime — normal if Docker used |
| 5353 | avahi-daemon | 🟡 | mDNS — disable if not using Bonjour features |

## Firewall Rule Management

### Adding rules
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 631/tcp    # CUPS printing
sudo ufw deny 8766/tcp    # block old exposed port
```

### Deleting rules
```bash
# First list with numbers
sudo ufw status numbered
# Delete by number — do HIGHEST numbers first (reverse order)
# so that lower numbers don't shift after each deletion
sudo ufw delete 3
sudo ufw delete 5
```
**Note:** `sudo ufw delete N` prompts for `y` confirmation interactively. In automation, delete by service name: `sudo ufw delete allow 22/tcp`.

### Verify firewall is actually blocking
```bash
# Confirm a denied port is not reachable
curl -s -o /dev/null -w "%{http_code}" http://localhost:8766/
# Should return 000 (connection refused) if ufw deny is active
```

## Post-Audit Fix Priority

1. **Firewall first** — always. Default-deny blocks new exposure while you investigate other findings.
2. **Exposed services second** — bind to 127.0.0.1 or firewall the port.
3. **Malware scanners third** — install rkhunter/chkrootkit before exposing to internet.
4. **Disable unused services** — avahi, cups-browsed, docker (if not used).
5. **Document everything** — firewall rules, disabled services, installed scanners.