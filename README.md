# Developer Toolbox (`dev-toolbox`)

A curated collection of developer scripts, utilities, and workflow optimizations.

---

## ⚡ Quick Download (Grab a script without cloning)

Download any single script directly on any PC using `curl` (pre-installed on Windows 10/11, macOS, and Linux):

```powershell
# 1. Image Compressor
curl.exe -O https://raw.githubusercontent.com/codernayeem/dev-toolbox/main/img-compress/convert.py

# 2. WSL Always-On (installs directly into Windows Startup folder)
curl.exe -o "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-wsl.vbs" https://raw.githubusercontent.com/codernayeem/dev-toolbox/main/wsl-always-on/start-wsl.vbs

# 3. Image Deduplicator
curl.exe -O https://raw.githubusercontent.com/codernayeem/dev-toolbox/main/image-similarity-dedup/dedup.py
```

---

## 🧰 Available Tools & Guides

| Directory | Category | Description |
| :--- | :--- | :--- |
| [`img-compress`](img-compress/README.md) | **Media Optimization** | Interactive batch image compressor and WebP/JPEG converter with smart dimension downscaling. |
| [`wsl-always-on`](wsl-always-on/README.md) | **Windows & WSL** | Silent VBS startup launcher to keep WSL background services running without open terminals. |
| [`wsl-compact`](wsl-compact/README.md) | **Windows & WSL** | Modern WSL 2 sparse VHD configuration and disk compacting instructions to reclaim storage. |
| [`coolify-tricks`](coolify-tricks/README.md) | **DevOps & Cloud** | Practical Docker volume permission fixes and PostgreSQL multi-database setup guide for Coolify. |
| [`image-similarity-dedup`](image-similarity-dedup/README.md) | **Media / AI** | 3-stage visual image deduplicator using SIFT keypoint matching and Laplacian sharpness ranking. |

---

## 📁 Repository Standards

```
tool-name/
├── README.md         # What it does, requirements, and usage examples
├── requirements.txt  # Dependencies (if applicable)
└── script.py / .vbs  # Clean, parameterized code with zero hardcoded credentials
```
