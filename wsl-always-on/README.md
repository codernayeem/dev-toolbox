# WSL Always On (`wsl-always-on`)

Launches WSL 2 silently in the background on Windows startup (no console window) so Docker, servers, and background services stay online.

---

## Setup

1. Press <kbd>Win</kbd> + <kbd>R</kbd>, type `shell:startup`, and press Enter.
2. Copy [`start-wsl.vbs`](start-wsl.vbs) into this Startup folder.
3. *(Optional)* Edit `start-wsl.vbs` in Notepad if your distribution is not `Ubuntu`.

## Verify
```powershell
wsl --list --running
```
