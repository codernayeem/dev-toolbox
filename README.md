# Developer Toolbox (`dev-toolbox`)

A curated collection of developer scripts, utilities, and workflow optimizations.

---

## 🧰 Available Tools & Guides

| Directory | Category | Description |
| :--- | :--- | :--- |
| [`coolify-tricks`](coolify-tricks/README.md) | **DevOps & Cloud** | Practical Docker volume permission fixes and PostgreSQL multi-database setup guide for Coolify. |
| [`image-similarity-dedup`](image-similarity-dedup/README.md) | **Media / AI** | 3-stage visual image deduplicator using SIFT keypoint matching and Laplacian sharpness ranking. |
| [`img-compress`](img-compress/README.md) | **Media Optimization** | Interactive batch image compressor and WebP/JPEG converter with smart dimension downscaling. |
| [`wsl-always-on`](wsl-always-on/README.md) | **Windows & WSL** | Silent VBS startup launcher to keep WSL background services running without open terminals. |
| [`wsl-compact`](wsl-compact/README.md) | **Windows & WSL** | Modern WSL 2 sparse VHD configuration and disk compacting instructions to reclaim storage. |

---

## 📁 Repository Standards

Every tool inside this toolbox adheres to the following structure:

```
tool-name/
├── README.md         # What it does, requirements, and usage examples
├── requirements.txt  # Python package dependencies (if applicable)
└── script.py / .vbs  # Clean, parameterized code with zero hardcoded credentials
```

### Contributing a New Utility
1. Create a dedicated subdirectory for your utility.
2. Ensure **no personal information, machine-specific paths, credentials, or secrets** are included.
3. Provide a clear `README.md` and define dependencies in a `requirements.txt`.
