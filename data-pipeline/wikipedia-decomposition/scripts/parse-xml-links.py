"""
Parse Wikipedia XML dumps to extract wikilinks.

Extracts internal links from article text to create links.parquet.
Uses streaming XML parsing to handle large files efficiently.

Output schema: from_id (int32), to_title (string)
"""

import re
import xml.etree.ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import Iterator
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# Paths
RAW_DIR = Path("data/wikipedia/raw")
PROCESSED_DIR = Path("data/wikipedia/processed")

# Namespace for MediaWiki XML
NS = '{http://www.mediawiki.org/xml/export-0.11/}'

# Regex to match wikilinks: [[Target]] or [[Target|Display]]
# Captures just the target (before |)
WIKILINK_RE = re.compile(r'\[\[([^\[\]|#]+)')


def extract_links_from_text(text: str) -> list[str]:
    """Extract wikilink targets from wikitext."""
    if not text:
        return []
    
    targets = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        if target:
            # Normalize: first char uppercase, spaces to underscores
            target = target.replace(' ', '_')
            if target:
                target = target[0].upper() + target[1:] if len(target) > 1 else target.upper()
                targets.append(target)
    
    return targets


def parse_xml_file(xml_path: Path) -> tuple[list[int], list[str]]:
    """
    Parse a single XML file and extract links.
    Returns (from_ids, to_titles) lists.
    """
    from_ids = []
    to_titles = []
    
    # Use iterparse for memory-efficient streaming
    context = ET.iterparse(str(xml_path), events=('end',))
    
    page_id = None
    page_ns = None
    page_text = None
    
    for event, elem in context:
        tag = elem.tag.replace(NS, '')
        
        if tag == 'id' and page_id is None:
            # First <id> in <page> is page_id
            page_id = int(elem.text) if elem.text else None
        elif tag == 'ns':
            page_ns = int(elem.text) if elem.text else 0
        elif tag == 'text':
            page_text = elem.text
        elif tag == 'page':
            # Process completed page
            if page_id is not None and page_ns == 0 and page_text:
                # Only process article namespace (0) with content
                links = extract_links_from_text(page_text)
                for target in links:
                    # Filter out non-article links (with namespace prefix)
                    if ':' not in target or target.startswith(':'):
                        # Links starting with : are mainspace
                        clean_target = target.lstrip(':')
                        if clean_target:
                            from_ids.append(page_id)
                            to_titles.append(clean_target)
            
            # Reset for next page
            page_id = None
            page_ns = None
            page_text = None
            
            # Clear element to free memory
            elem.clear()
    
    return from_ids, to_titles


def process_file_wrapper(args):
    """Wrapper for multiprocessing."""
    xml_path, file_idx, total_files = args
    start = time.time()
    from_ids, to_titles = parse_xml_file(xml_path)
    elapsed = time.time() - start
    return xml_path.name, len(from_ids), elapsed


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all decompressed XML files (not .bz2)
    xml_files = [f for f in sorted(RAW_DIR.glob('*multistream*.xml*')) 
                 if not f.name.endswith('.bz2')]
    print(f"Found {len(xml_files)} XML files to process")
    
    total_start = time.time()
    all_from_ids = []
    all_to_titles = []
    
    # Process files sequentially (parallel processing of large files doesn't help much)
    for i, xml_path in enumerate(xml_files, 1):
        file_start = time.time()
        print(f"[{i}/{len(xml_files)}] Processing {xml_path.name}...", end=' ', flush=True)
        
        from_ids, to_titles = parse_xml_file(xml_path)
        all_from_ids.extend(from_ids)
        all_to_titles.extend(to_titles)
        
        elapsed = time.time() - file_start
        print(f"{len(from_ids):,} links ({elapsed:.1f}s)")
        
        # Progress update every 10 files
        if i % 10 == 0:
            total_elapsed = time.time() - total_start
            remaining = (total_elapsed / i) * (len(xml_files) - i)
            print(f"  Progress: {len(all_from_ids):,} total links, ~{remaining/60:.0f}m remaining")
    
    total_elapsed = time.time() - total_start
    print(f"\nExtracted {len(all_from_ids):,} links in {total_elapsed:.1f}s")
    
    # Write to parquet
    print("Writing parquet...")
    table = pa.table({
        'from_id': pa.array(all_from_ids, type=pa.int32()),
        'to_title': pa.array(all_to_titles, type=pa.string()),
    })
    
    out_path = PROCESSED_DIR / "links.parquet"
    pq.write_table(table, out_path, compression='zstd')
    print(f"Wrote {out_path} ({out_path.stat().st_size / 1e9:.2f} GB)")


if __name__ == "__main__":
    main()
