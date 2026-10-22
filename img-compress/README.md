# Image Compressor & Converter (`img-compress`)

Batch compress, resize, and convert images to **WebP** or **JPEG**. Automatically skips already-converted images unless they exceed max dimensions.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python convert.py                             # Convert current folder to WebP (1920px max, Q85)
python convert.py -i ./photos -o ./out        # Custom input & output folders
python convert.py -f jpg -q 90                # Convert to JPEG (quality 90)
python convert.py -m -1                       # Keep original resolution (no resizing)
python convert.py -y                          # Skip confirmation prompt
python convert.py --delete-original           # Delete source files after conversion
```

## Options
| Flag | Default | Description |
| :--- | :--- | :--- |
| `-i, --input` | `.` | Input folder |
| `-o, --output` | *(input)* | Output folder |
| `-f, --format` | `webp` | Target format (`webp`, `jpg`) |
| `-q, --quality`| `85` | Quality (`1-100`) |
| `-m, --max-dim`| `1920` | Max width/height px (`-1` to disable) |
| `--delete-original` | `False` | Delete source images |
| `-y, --yes` | `False` | Non-interactive mode |
