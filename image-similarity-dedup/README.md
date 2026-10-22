# Image Similarity Deduplicator (`image-similarity-dedup`)

Detects near-identical, rotated, scaled, or augmented image duplicates using SIFT keypoint matching, automatically keeping the sharpest image in each duplicate cluster.

## Installation
```bash
pip install -r requirements.txt
```

## Usage

### Fast Run (All Stages)
```bash
python dedup.py --stage 1 2 3 --input ./raw_images --output ./clean_images --threshold 0.35
```

### Step-by-Step Workflow
```bash
# 1. Precompute features & build cache (.dedup_cache.json)
python dedup.py --stage 1 --input ./raw_images

# 2. View threshold comparison table (evaluates cutoffs 0.15 - 0.80)
python dedup.py --stage 2 --input ./raw_images

# 3. Test a specific threshold (dry-run)
python dedup.py --stage 2 --input ./raw_images --threshold 0.30

# 4. Apply deduplication and export clean images
python dedup.py --stage 3 --input ./raw_images --output ./clean_images --threshold 0.30
```

## Options
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--stage` | *(Required)* | Stages to run: `1`, `2`, `3` (e.g. `--stage 1 2 3`) |
| `--input` | *(Required)* | Input directory containing images |
| `--output` | `clean_images` | Destination folder for clean images |
| `--threshold`| `None` (sweep) | Similarity cutoff ratio (e.g. `0.30`) |
| `--batch-size`| `100` | Sliding window comparison batch size |
| `--overlap` | `40` | Sliding window overlap |
| `--workers` | CPU Cores | Number of worker threads |
| `--cache` | `.dedup_cache.json`| Custom cache file path |
