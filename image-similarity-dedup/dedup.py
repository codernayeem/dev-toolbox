import os
import sys
import json
import shutil
import argparse
import cv2
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff')

def compute_sharpness(img_path):
    """Calculates sharpness score using Laplacian variance (higher = sharper)."""
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())

def match_pair(args):
    """Worker for pairwise SIFT matching with normalized Dice ratio."""
    i, j, des_i, des_j, threshold = args
    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
    len_i, len_j = len(des_i), len(des_j)
    try:
        matches = flann.knnMatch(des_i, des_j, k=2)
        good = [m[0] for m in matches if len(m) == 2 and m[0].distance < 0.75 * m[1].distance]
        unique_matches = len(set(m.trainIdx for m in good))
        ratio = (2.0 * unique_matches) / (len_i + len_j)
        if ratio >= threshold:
            return (i, j, round(ratio, 4))
    except Exception:
        pass
    return None

# ==============================================================================
# STAGE 1: PRECOMPUTE FEATURE & BATCH OVERLAP SIMILARITY
# ==============================================================================
def run_stage_1(input_folder, cache_file, batch_size, overlap, workers, record_threshold=0.08):
    print(f"\n{'='*75}")
    print(f" STAGE 1: PRECOMPUTING (Batch Size: {batch_size}, Overlap: {overlap}, Workers: {workers})")
    print(f"{'='*75}")
    
    files = sorted([
        f for f in os.listdir(input_folder)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    ])
    
    total_files = len(files)
    if total_files == 0:
        print(f"No image files found in {input_folder}")
        return None

    print(f"Scanning input folder: {input_folder}")
    print(f"Found {total_files} total images.\n")

    sift = cv2.SIFT_create(nfeatures=400)
    images_info = []
    descriptors = []

    print("Step 1/2: Extracting SIFT Keypoints & Sharpness...")
    for idx, fname in enumerate(tqdm(files, desc="Processing Images")):
        full_path = os.path.join(input_folder, fname)
        img = cv2.imread(full_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        sharpness = compute_sharpness(full_path)
        h, w = img.shape
        scale = 512 / max(h, w)
        img_small = cv2.resize(img, (int(w * scale), int(h * scale))) if scale < 1.0 else img
        
        kp, des = sift.detectAndCompute(img_small, None)
        if des is not None and len(kp) >= 10:
            img_id = len(images_info)
            images_info.append({
                "id": img_id,
                "filename": fname,
                "sharpness": round(sharpness, 2)
            })
            descriptors.append(des)

    n_valid = len(images_info)
    print(f"\nSuccessfully indexed {n_valid} valid images.\n")

    # Generate overlapping batch pairs
    print("Step 2/2: Multithreaded Overlapping Batch Pairwise Matching...")
    step = batch_size - overlap
    if step <= 0:
        step = max(1, batch_size // 2)

    pair_tasks = set()
    for start_idx in range(0, n_valid, step):
        end_idx = min(start_idx + batch_size, n_valid)
        for i in range(start_idx, end_idx):
            for j in range(i + 1, end_idx):
                pair_tasks.add((i, j))

    print(f"Generated {len(pair_tasks)} pair candidate comparisons across sliding batches.")
    
    task_args = [
        (i, j, descriptors[i], descriptors[j], record_threshold)
        for (i, j) in pair_tasks
    ]

    matched_pairs = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for res in tqdm(executor.map(match_pair, task_args), total=len(task_args), desc="Matching Batch Pairs"):
            if res is not None:
                matched_pairs.append({
                    "img1": res[0],
                    "img2": res[1],
                    "ratio": res[2]
                })

    cache_data = {
        "input_folder": input_folder,
        "batch_size": batch_size,
        "overlap": overlap,
        "total_images": n_valid,
        "images": images_info,
        "pairs": matched_pairs
    }

    os.makedirs(os.path.dirname(os.path.abspath(cache_file)), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2)

    print(f"\n[STAGE 1 COMPLETE] Cache written to: {cache_file}")
    return cache_data

# ==============================================================================
# STAGE 2: INSPECT THRESHOLD SWEEP OR SINGLE THRESHOLD DRY-RUN
# ==============================================================================
def evaluate_threshold(cache_data, threshold):
    images = cache_data["images"]
    pairs = cache_data["pairs"]
    n = len(images)

    adj = {i: set() for i in range(n)}
    for p in pairs:
        if p["ratio"] >= threshold:
            adj[p["img1"]].add(p["img2"])
            adj[p["img2"]].add(p["img1"])

    visited = set()
    kept_count = 0
    clusters_count = 0

    for i in range(n):
        if i not in visited:
            comp = []
            q = [i]
            visited.add(i)
            while q:
                curr = q.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
            kept_count += 1
            if len(comp) > 1:
                clusters_count += 1

    discarded_count = n - kept_count
    reduction_pct = (discarded_count / n * 100) if n > 0 else 0.0

    return {
        "threshold": threshold,
        "total": n,
        "clusters": clusters_count,
        "kept": kept_count,
        "discarded": discarded_count,
        "reduction_pct": reduction_pct
    }

def run_stage_2(cache_data, threshold=None):
    total = cache_data["total_images"]
    
    if threshold is None:
        print(f"\n{'='*75}")
        print(f" STAGE 2: THRESHOLD SWEEP COMPARISON TABLE (Total Images: {total})")
        print(f"{'='*75}")
        print(f"| Threshold | Duplicate Groups | Augmented Dropped | Clean Images Kept | Reduction % |")
        print(f"|:---------:|:----------------:|:-----------------:|:-----------------:|:-----------:|")

        thresholds = [round(t, 2) for t in np.arange(0.15, 0.85, 0.05)]
        for t in thresholds:
            res = evaluate_threshold(cache_data, t)
            print(f"|   {res['threshold']:.2f}    |       {res['clusters']:4d}       |       {res['discarded']:5d}       |       {res['kept']:5d}       |   {res['reduction_pct']:6.2f}%   |")
        
        print(f"{'='*75}")
        print("To test or apply a specific threshold, pass --threshold <VALUE>")
    else:
        res = evaluate_threshold(cache_data, threshold)
        print(f"\n{'='*75}")
        print(f" STAGE 2: DRY-RUN SUMMARY FOR THRESHOLD {threshold:.4f}")
        print(f"{'='*75}")
        print(f" Total Input Images   : {res['total']}")
        print(f" Duplicate Groups     : {res['clusters']}")
        print(f" Augmented Discarded  : {res['discarded']}")
        print(f" Clean Unique Kept    : {res['kept']}")
        print(f" Data Reduction       : {res['reduction_pct']:.2f}%")
        print(f"{'='*75}")

# ==============================================================================
# STAGE 3: APPLY DEDUPLICATION & COPY CLEAN FILES TO OUTPUT FOLDER
# ==============================================================================
def run_stage_3(cache_data, threshold, output_folder):
    if threshold is None:
        threshold = 0.30
        print(f"[INFO] No threshold specified for Stage 3. Defaulting to --threshold {threshold}")

    print(f"\n{'='*75}")
    print(f" STAGE 3: APPLYING DEDUPLICATION (Threshold: {threshold})")
    print(f" Destination Folder: {output_folder}")
    print(f"{'='*75}")

    images = cache_data["images"]
    pairs = cache_data["pairs"]
    input_folder = cache_data["input_folder"]
    n = len(images)

    adj = {i: set() for i in range(n)}
    for p in pairs:
        if p["ratio"] >= threshold:
            adj[p["img1"]].add(p["img2"])
            adj[p["img2"]].add(p["img1"])

    visited = set()
    kept_images = []
    clusters_count = 0

    for i in range(n):
        if i not in visited:
            comp = []
            q = [i]
            visited.add(i)
            while q:
                curr = q.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)

            sharpest_idx = max(comp, key=lambda idx: images[idx]["sharpness"])
            kept_images.append(images[sharpest_idx])
            if len(comp) > 1:
                clusters_count += 1

    os.makedirs(output_folder, exist_ok=True)
    print(f"Copying {len(kept_images)} clean unique images to output folder...")

    for img_info in tqdm(kept_images, desc="Copying Clean Files"):
        src_p = os.path.join(input_folder, img_info["filename"])
        dst_p = os.path.join(output_folder, img_info["filename"])
        shutil.copy2(src_p, dst_p)

    discarded_count = n - len(kept_images)
    print(f"\n========================================================")
    print(f" DEDUPLICATION COMPLETE")
    print(f" Total Input Images     : {n}")
    print(f" Duplicate Groups       : {clusters_count}")
    print(f" Duplicates Discarded   : {discarded_count}")
    print(f" Clean Images Saved     : {len(kept_images)}")
    print(f" Output Location        : {output_folder}")
    print(f"========================================================\n")

# ==============================================================================
# MAIN CLI CONTROLLER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Multi-stage flat folder image deduplicator.")
    parser.add_argument("--stage", nargs="+", required=True,
                        help="Stage(s) to execute: 1 (precompute), 2 (inspect), 3 (apply). Can pass multiple e.g. --stage 1 2 3")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the flat input folder containing images")
    parser.add_argument("--output", type=str, default="clean_images",
                        help="Output folder to copy clean images (default: 'clean_images')")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Sliding window batch size (default: 100)")
    parser.add_argument("--overlap", type=int, default=40,
                        help="Sliding window overlap size (default: 40)")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Match ratio threshold (e.g. 0.30). If omitted in Stage 2, displays sweep table.")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4,
                        help="Number of CPU worker threads")
    parser.add_argument("--cache", type=str, default=None,
                        help="Custom path for cache JSON file (default: <input_folder>/.dedup_cache.json)")

    args = parser.parse_args()

    input_folder = os.path.abspath(args.input)
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    cache_file = args.cache or os.path.join(input_folder, ".dedup_cache.json")

    # Map stage input flags (support both '1', '2', '3' and 'precompute', 'inspect', 'apply')
    stages_to_run = set()
    for s in args.stage:
        s_clean = str(s).lower().strip()
        if s_clean in ['1', 'precompute']:
            stages_to_run.add(1)
        elif s_clean in ['2', 'inspect']:
            stages_to_run.add(2)
        elif s_clean in ['3', 'apply']:
            stages_to_run.add(3)

    cache_data = None

    # STAGE 1
    if 1 in stages_to_run:
        cache_data = run_stage_1(input_folder, cache_file, args.batch_size, args.overlap, args.workers)

    # Load cache data if Stage 2 or 3 is running without Stage 1
    if (2 in stages_to_run or 3 in stages_to_run) and cache_data is None:
        if not os.path.exists(cache_file):
            print(f"Error: Cache file '{cache_file}' not found. Please run --stage 1 first!")
            sys.exit(1)
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

    # STAGE 2
    if 2 in stages_to_run:
        run_stage_2(cache_data, args.threshold)

    # STAGE 3
    if 3 in stages_to_run:
        output_folder = os.path.abspath(args.output)
        run_stage_3(cache_data, args.threshold, output_folder)

if __name__ == "__main__":
    main()
