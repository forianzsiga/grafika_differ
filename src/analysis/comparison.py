"""Image comparison functionality using PIL."""

import logging
from pathlib import Path
from typing import List

from PIL import Image, ImageChops


def generate_comparison(inputs: List[Path], output_dir: Path) -> None:
    """Generate absolute pixel-wise diffs between matching frames in two runs.
    
    Args:
        inputs: List of exactly two input directories
        output_dir: Directory to save comparison results
    """
    if len(inputs) != 2:
        raise ValueError("Comparison mode expects exactly two input directories")
    
    first_dir, second_dir = inputs
    for directory in (first_dir, second_dir):
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Input directory not found: {directory}")
    
    output_dir.mkdir(parents=True, exist_ok=True)

    first_files = {path.name: path for path in first_dir.glob("*.png")}
    second_files = {path.name: path for path in second_dir.glob("*.png")}
    shared_names = sorted(first_files.keys() & second_files.keys())
    
    if not shared_names:
        raise SystemExit("No matching frames to compare; ensure filenames align")

    unmatched_first = sorted(first_files.keys() - second_files.keys())
    unmatched_second = sorted(second_files.keys() - first_files.keys())
    for name in unmatched_first:
        logging.warning("Skipping frame present only in first input: %s", name)
    for name in unmatched_second:
        logging.warning("Skipping frame present only in second input: %s", name)

    processed = 0
    for name in shared_names:
        out_name = Path(name).stem + "_diff" + Path(name).suffix
        output_path = output_dir / out_name
        
        with Image.open(first_files[name]) as img_a, Image.open(second_files[name]) as img_b:
            if img_a.size != img_b.size:
                logging.warning(
                    "Skipping %s due to size mismatch (%s vs %s)",
                    name,
                    img_a.size,
                    img_b.size,
                )
                continue
            if img_a.mode != img_b.mode:
                img_b = img_b.convert(img_a.mode)
            diff = ImageChops.difference(img_a, img_b)
            diff.save(output_path)
            logging.info("Wrote diff frame: %s", output_path)
            processed += 1
    
    logging.info("Completed diff generation for %d frame(s)", processed)
