# Obsidian App Launch Troubleshooting (Linux)

## Failure Mode A — GPU Crash

Obsidian exits immediately with `GPU process isn't usable. Goodbye.` — the Chromium GPU process crashes before the window renders.

**Root cause:** Haswell integrated GPU has incomplete Vulkan support. The iHD VAAPI driver (`iHD_drv_video.so`) fails.

**Error transcript:**
```
xdg-settings: default-url-scheme-handler not implemented for xfce
MESA-INTEL: warning: Haswell Vulkan support is incomplete
libva error: /usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so init failed
[5572:0526/215728.292774:FATAL:gpu_data_manager_impl_private.cc:415] GPU process isn't usable. Goodbye.
```

**Fix — GPU flags:**
```bash
snap run obsidian --disable-gpu --disable-software-rasterizer
```

**System context:** Intel Haswell-ULT, Xfce, X11 session.

---

## Failure Mode B — Snap Exits Silently (May 2026)

`snap run obsidian` exits with code 1, no window, no error output. Process dies cleanly in ~1 second. No GPU crash message.

**Root cause:** Snap environment/confinement breakage — not a GPU issue. GPU flags no longer help. The snap binary itself cannot launch the Electron process.

**Fix — Replace snap with official tarball:**

```bash
# 1. Remove snap
snap remove obsidian

# 2. Download and install official tarball
cd /tmp
curl -L https://github.com/obsidianmd/obsidian-releases/releases/download/v1.12.7/obsidian_1.12.7_amd64.tar.gz -o obsidian.tar.gz
tar -xzf obsidian.tar.gz
sudo mv Obsidian /opt/obsidian

# 3. Wrapper (preserves --disable-gpu for GPU stability on Haswell)
cat > ~/.local/bin/obsidian << 'EOF'
#!/bin/bash
exec /opt/obsidian/Obsidian --disable-gpu "$@"
EOF
chmod +x ~/.local/bin/obsidian

# 4. Desktop entry
cat > ~/.local/share/applications/obsidian.desktop << 'EOF'
[Desktop Entry]
Name=Obsidian
Exec=/opt/obsidian/Obsidian --disable-gpu %U
Terminal=false
Type=Application
Icon=/opt/obsidian/resources/obsidian.png
StartupWMClass=obsidian
MimeType=x-scheme-handler/obsidian;
Categories=Office;
EOF
chmod +x ~/.local/share/applications/obsidian.desktop

# 5. Pin to desktop
cp ~/.local/share/applications/obsidian.desktop ~/Desktop/obsidian.desktop
chmod +x ~/Desktop/obsidian.desktop
```

> **Note:** `--disable-gpu` is still needed even with the tarball — Haswell GPU stability issue persists across install methods.

**Verification:**
```bash
ps aux | grep obsi | grep -v grep
# Should show: obsidian (main), obsidian --type=zygote, obsidian --type=renderer
```

---

## Why `--disable-gpu` Is Still Needed

Obsidian is Electron/Chromium-based. On Haswell it tries VAAPI decode → fails → GPU process crashes. `--disable-gpu` kills all GPU paths at once for clean CPU-only startup — no functional impact for a note-taking app.

## Chromium Flags Reference

- `--disable-gpu` — disable GPU hardware acceleration
- `--disable-software-rasterizer` — disable SwiftShader fallback
- `--in-process-gpu` — run GPU in-process (extra stability)
- `--no-sandbox` — disable Chromium sandbox
- `--disable-gpu-compositing` — disable GPU compositing layer

## If Tarball Also Fails

1. Check binary: `ls -la /opt/obsidian/Obsidian`
2. Check libraries: `ldd /opt/obsidian/Obsidian | head -10`
3. Check libva driver: `apt list --installed 2>/dev/null | grep -i vaapi`
4. Try flatpak as last resort
