#!/usr/bin/env python3
"""
Image Compression & WebP/JPEG Converter
A simple, robust tool to batch compress, resize, and convert images for web optimization.
Smart Skip: Automatically skips already-converted images unless they exceed max dimensions.
"""

import os
import sys
from pathlib import Path
import argparse

# Ensure UTF-8 output on Windows consoles to prevent cp1252 charmap errors
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Supported input image extensions
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}

def format_size(num_bytes: int) -> str:
    """Formats bytes into human readable format (KB, MB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

def get_images(directory: Path):
    """Finds all supported image files in the target directory (non-recursive)."""
    images = []
    for file_path in sorted(directory.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            if not file_path.name.endswith(".tmp.webp") and not file_path.name.endswith(".tmp.jpg"):
                images.append(file_path)
    return images

def resize_image(img, max_dim: int):
    """Resizes image maintaining aspect ratio if larger than max_dim."""
    from PIL import Image
    if max_dim <= 0:
        return img
    
    w, h = img.size
    longest = max(w, h)
    if longest > max_dim:
        scale = max_dim / longest
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return img

def check_image_status(input_path: Path, output_dir: Path, target_fmt: str, max_dim: int):
    """
    Checks if an image needs conversion or can be skipped based on format and max dimensions.
    Returns: (needs_processing: bool, reason: str, dimensions: tuple or None)
    """
    from PIL import Image

    target_ext = ".webp" if target_fmt == "webp" else ".jpg"
    is_same_format = input_path.suffix.lower() == target_ext
    target_file = output_dir / f"{input_path.stem}{target_ext}"

    # Case 1: File is already in target format (e.g. x.webp when converting to webp)
    if is_same_format:
        try:
            with Image.open(input_path) as img:
                w, h = img.size
            if max_dim > 0 and max(w, h) > max_dim:
                return True, f"oversized ({w}x{h} > {max_dim}px max)", (w, h)
            else:
                dim_str = f"{w}x{h}" if max_dim > 0 else "no resize limit"
                return False, f"already {target_fmt.upper()} within limits ({dim_str})", (w, h)
        except Exception:
            return True, "could not inspect dimensions", None

    # Case 2: Target converted file already exists in output folder (e.g. x.webp exists for x.png)
    if target_file.exists():
        try:
            with Image.open(target_file) as img:
                tw, th = img.size
            if max_dim > 0 and max(tw, th) > max_dim:
                return True, f"existing {target_file.name} is oversized ({tw}x{th} > {max_dim}px)", (tw, th)
            else:
                dim_str = f"{tw}x{th}" if max_dim > 0 else "exists"
                return False, f"{target_file.name} already exists within limits ({dim_str})", (tw, th)
        except Exception:
            return True, f"existing {target_file.name} unreadable, re-converting", None

    # Case 3: Regular conversion (new format, target does not exist)
    return True, "new conversion", None

def convert_single_image(input_path: Path, output_dir: Path, target_fmt: str,
                         quality: int, max_dim: int, keep_original: bool):
    """
    Converts and optimizes a single image file.
    Returns (success: bool, original_size: int, new_size: int, message: str)
    """
    from PIL import Image, ImageOps, ImageSequence

    orig_size = input_path.stat().st_size
    target_ext = ".webp" if target_fmt == "webp" else ".jpg"
    
    base_name = input_path.stem
    out_file = output_dir / f"{base_name}{target_ext}"
    temp_out_file = output_dir / f"{out_file.stem}.tmp{target_ext}"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(input_path) as img:
            # Auto-orient image based on EXIF camera orientation
            img = ImageOps.exif_transpose(img)

            # Handle animated GIFs when converting to WebP
            if target_fmt == "webp" and getattr(img, "is_animated", False):
                frames = []
                durations = []
                for frame in ImageSequence.Iterator(img):
                    f = frame.copy()
                    if max_dim > 0:
                        f = resize_image(f, max_dim)
                    if f.mode not in ("RGB", "RGBA"):
                        f = f.convert("RGBA")
                    frames.append(f)
                    durations.append(frame.info.get("duration", 100))
                
                if frames:
                    frames[0].save(
                        temp_out_file,
                        format="WEBP",
                        save_all=True,
                        append_images=frames[1:],
                        duration=durations,
                        loop=0,
                        quality=quality,
                        method=6
                    )
            else:
                # Handle static images or JPEG conversion
                processed = resize_image(img, max_dim)

                if target_fmt == "webp":
                    # WebP supports RGBA natively
                    if processed.mode not in ("RGB", "RGBA"):
                        processed = processed.convert("RGBA" if "transparency" in processed.info else "RGB")
                    processed.save(
                        temp_out_file,
                        format="WEBP",
                        quality=quality,
                        method=6,
                        optimize=True
                    )
                else:  # JPEG
                    # JPEG does not support alpha channel; composite on white background
                    if processed.mode in ("RGBA", "LA") or ("transparency" in processed.info):
                        bg = Image.new("RGB", processed.size, (255, 255, 255))
                        mask = processed.split()[-1] if processed.mode == "RGBA" else None
                        bg.paste(processed, mask=mask)
                        processed = bg
                    elif processed.mode != "RGB":
                        processed = processed.convert("RGB")
                    
                    processed.save(
                        temp_out_file,
                        format="JPEG",
                        quality=quality,
                        optimize=True
                    )

        # Replace destination file atomically
        if out_file.exists():
            out_file.unlink()
        temp_out_file.rename(out_file)

        new_size = out_file.stat().st_size
        savings = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0

        # Delete original only if requested and output is distinct
        if not keep_original and input_path.resolve() != out_file.resolve():
            try:
                input_path.unlink()
                del_note = " (original deleted)"
            except Exception as e:
                del_note = f" (could not delete original: {e})"
        else:
            del_note = ""

        msg = f"  [OK] {input_path.name} -> {out_file.name} [{format_size(orig_size)} -> {format_size(new_size)}, {savings:+.1f}%]{del_note}"
        return True, orig_size, new_size, msg

    except Exception as e:
        if temp_out_file.exists():
            temp_out_file.unlink()
        return False, orig_size, 0, f"  [FAIL] {input_path.name}: {str(e)}"

def main():
    parser = argparse.ArgumentParser(
        description="Batch compress, resize, and convert images to WebP or JPEG with smart dimension checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-i", "--input", dest="input_dir", default=".",
        help="Input folder containing images"
    )
    parser.add_argument(
        "-o", "--output", dest="output_dir", default=None,
        help="Output folder to save optimized images (default: same as input folder)"
    )
    parser.add_argument(
        "-f", "--format", dest="fmt", choices=["webp", "jpg", "jpeg"], default="webp",
        help="Target format (webp or jpg)"
    )
    parser.add_argument(
        "-q", "--quality", dest="quality", type=int, default=85,
        help="Quality level (1-100)"
    )
    parser.add_argument(
        "-m", "--max-dim", dest="max_dim", type=int, default=1920,
        help="Maximum width or height in pixels. Set to -1 to disable resizing"
    )
    parser.add_argument(
        "--delete-original", dest="delete_original", action="store_true", default=False,
        help="Delete original files after successful conversion"
    )
    parser.add_argument(
        "-y", "--yes", dest="skip_confirm", action="store_true", default=False,
        help="Skip confirmation prompt and run immediately"
    )

    args = parser.parse_args()

    # Validate quality
    if not (1 <= args.quality <= 100):
        print("[ERROR] Quality must be between 1 and 100.")
        sys.exit(1)

    # Validate Pillow library
    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] Pillow is not installed.")
        print("        Install it using: pip install -r requirements.txt (or pip install Pillow)")
        sys.exit(1)

    # Normalize paths
    input_path = Path(args.input_dir).resolve()
    if not input_path.exists() or not input_path.is_dir():
        print(f"[ERROR] Input directory '{input_path}' does not exist.")
        sys.exit(1)

    output_path = Path(args.output_dir).resolve() if args.output_dir else input_path
    target_format = "jpg" if args.fmt in ("jpg", "jpeg") else "webp"

    # Find images
    images = get_images(input_path)
    if not images:
        print(f"[INFO] No supported images found in: {input_path}")
        print(f"       Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
        sys.exit(0)

    # Smart Pre-scan: determine which files need processing vs skipping
    to_process = []
    to_skip = []

    for img_file in images:
        needs_proc, reason, _ = check_image_status(
            input_path=img_file,
            output_dir=output_path,
            target_fmt=target_format,
            max_dim=args.max_dim
        )
        if needs_proc:
            to_process.append((img_file, reason))
        else:
            to_skip.append((img_file, reason))

    keep_original = not args.delete_original
    is_interactive = not args.skip_confirm

    # Display Configuration & Interactive Confirmation
    print("=" * 65)
    print("                IMAGE OPTIMIZATION SETTINGS")
    print("=" * 65)
    print(f" Input Directory   : {input_path}")
    print(f" Output Directory  : {output_path}")
    print(f" Target Format     : {target_format.upper()}")
    print(f" Quality           : {args.quality}")
    print(f" Max Dimension     : {'No resize (-1)' if args.max_dim <= 0 else f'{args.max_dim}px (aspect ratio preserved)'}")
    print(f" Keep Originals    : {'Yes' if keep_original else 'No (WILL DELETE ORIGINALS)'}")
    print(f" Images Found      : {len(images)} total file(s)")
    print(f"   -> To Convert   : {len(to_process)} file(s)")
    print(f"   -> To Skip      : {len(to_skip)} file(s) (already {target_format.upper()} & within size limits)")
    print("=" * 65)

    if not to_process:
        print(f"\n[INFO] All {len(images)} image(s) already meet target format and dimension criteria. Nothing to do!")
        sys.exit(0)

    if is_interactive:
        try:
            choice = input("\nProceed with optimization? [Y/n]: ").strip().lower()
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

        if choice not in ("", "y", "yes"):
            print("Operation canceled by user.")
            sys.exit(0)

    print("\nProcessing images...")
    print("-" * 65)

    # Show skipped images briefly if any
    for img_file, reason in to_skip:
        print(f"  [SKIP] {img_file.name} ({reason})")

    converted_count = 0
    total_orig_bytes = 0
    total_new_bytes = 0

    for img_file, _ in to_process:
        orig_file_size = img_file.stat().st_size
        total_orig_bytes += orig_file_size

        success, orig_sz, new_sz, msg = convert_single_image(
            input_path=img_file,
            output_dir=output_path,
            target_fmt=target_format,
            quality=args.quality,
            max_dim=args.max_dim,
            keep_original=keep_original
        )
        print(msg)
        if success:
            converted_count += 1
            total_new_bytes += new_sz
        else:
            total_new_bytes += orig_sz

    # Summary
    print("-" * 65)
    print(f"[DONE] Completed: {converted_count} converted, {len(to_skip)} skipped.")
    if converted_count > 0 and total_orig_bytes > 0:
        saved_bytes = total_orig_bytes - total_new_bytes
        savings_pct = (saved_bytes / total_orig_bytes) * 100
        print(f"  Converted Size: {format_size(total_orig_bytes)} -> {format_size(total_new_bytes)}")
        print(f"  Space Saved:    {format_size(saved_bytes)} ({savings_pct:.1f}% reduction)")
    print("=" * 65)

if __name__ == "__main__":
    main()