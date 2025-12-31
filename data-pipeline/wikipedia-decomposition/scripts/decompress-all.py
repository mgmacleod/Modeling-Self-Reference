"""
Decompress all Wikipedia dump files (.gz and .bz2)
Run from project root: python data-pipeline/wikipedia-decomposition/scripts/decompress-all.py
"""

import bz2
import gzip
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

RAW_DIR = Path("data/wikipedia/raw")

def decompress_gz(gz_path: Path) -> tuple[str, float]:
    """Decompress a .gz file, return (filename, size_gb)"""
    out_path = gz_path.with_suffix('')
    if out_path.exists():
        return (gz_path.name, -1)  # Already exists
    
    with gzip.open(gz_path, 'rb') as f_in:
        with open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return (gz_path.name, out_path.stat().st_size / 1e9)

def decompress_bz2(bz2_path: Path) -> tuple[str, float]:
    """Decompress a .bz2 file, return (filename, size_gb)"""
    out_path = bz2_path.with_suffix('')  # removes .bz2
    if out_path.exists():
        return (bz2_path.name, -1)  # Already exists
    
    with bz2.open(bz2_path, 'rb') as f_in:
        with open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return (bz2_path.name, out_path.stat().st_size / 1e9)

def main():
    start = time.time()
    
    # Get all compressed files
    gz_files = list(RAW_DIR.glob("*.gz"))
    bz2_files = list(RAW_DIR.glob("*.bz2"))
    
    print(f"Found {len(gz_files)} .gz files and {len(bz2_files)} .bz2 files")
    print(f"Output directory: {RAW_DIR.absolute()}")
    print()
    
    # Decompress .gz files first (smaller, faster)
    if gz_files:
        print("=== Decompressing .gz files ===")
        for gz in gz_files:
            print(f"  {gz.name}...", end=" ", flush=True)
            name, size = decompress_gz(gz)
            if size < 0:
                print("(already exists, skipped)")
            else:
                print(f"done ({size:.2f} GB)")
        print()
    
    # Decompress .bz2 files in parallel (many files, CPU-bound)
    if bz2_files:
        print(f"=== Decompressing {len(bz2_files)} .bz2 files (parallel) ===")
        completed = 0
        total_size = 0
        
        # Use 4 workers - bz2 is CPU-intensive
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(decompress_bz2, f): f for f in bz2_files}
            
            for future in as_completed(futures):
                name, size = future.result()
                completed += 1
                if size < 0:
                    print(f"  [{completed}/{len(bz2_files)}] {name} (skipped)")
                else:
                    total_size += size
                    print(f"  [{completed}/{len(bz2_files)}] {name} -> {size:.2f} GB")
        
        print(f"\nTotal decompressed XML: {total_size:.1f} GB")
    
    elapsed = time.time() - start
    print(f"\n=== Complete in {elapsed/60:.1f} minutes ===")

if __name__ == "__main__":
    main()
