# WSL 2 Disk Compaction (`wsl-compact`)

Reclaim host disk space from growing WSL 2 virtual hard disks (`ext4.vhdx`).

---

## Method 1: Modern WSL (Windows 11 / WSL 2.0+)

### Automatic Shrinking (Sparse VHD)
Run once to automatically shrink the disk whenever files are deleted inside WSL:
```cmd
wsl --shutdown
wsl --manage <DistroName> --set-sparse true
```

### One-Time Compact
```cmd
wsl --shutdown
wsl --compact <DistroName>
```

---

## Method 2: Traditional `diskpart` (Legacy)

1. Find your VHDX path in PowerShell:
   ```powershell
   Get-ChildItem -Path "$env:LOCALAPPDATA\wsl", "$env:LOCALAPPDATA\Packages" -Filter "ext4.vhdx" -Recurse | Select-Object FullName
   ```
2. Open **Command Prompt as Admin** and run:
   ```cmd
   wsl --shutdown
   diskpart
   select vdisk file="<PATH_TO_ext4.vhdx>"
   attach vdisk readonly
   compact vdisk
   detach vdisk
   exit
   ```

*(Tip: Run `sudo apt-get clean && docker system prune -a` inside Linux before compacting to maximize reclaimed space).*
