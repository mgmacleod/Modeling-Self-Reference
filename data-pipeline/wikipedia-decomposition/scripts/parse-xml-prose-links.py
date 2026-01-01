#!/usr/bin/env python3
"""
Parse Wikipedia XML dumps to extract PROSE-ONLY wikilinks with order preservation.

This is the N-Link theory parser. It:
1. Strips templates ({{...}}) - removes navboxes, infoboxes, citations
2. Strips tables ({|...|}) - removes structured data
3. Strips refs (<ref>...</ref>) - removes reference content
4. Strips comments (<!--...-->) - removes HTML comments
5. Strips galleries (<gallery>...</gallery>)
6. Extracts [[wikilinks]] from remaining prose text
7. Preserves link order (critical for N-Link traversal)

Output schema: from_id (int32), link_position (int32), to_title (string)
- link_position is 1-indexed (1st link, 2nd link, etc.)
- Order is preserved for N-Link function: f_N(page) = Nth link

For N-Link theory background, see:
  llm-facing-documentation/theories-proofs-conjectures/unified-inference-theory.md
"""

import re
import xml.etree.ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import time

# Paths
RAW_DIR = Path("data/wikipedia/raw")
PROCESSED_DIR = Path("data/wikipedia/processed")
OUTPUT_FILE = PROCESSED_DIR / "links_prose.parquet"

# Namespace for MediaWiki XML
NS = '{http://www.mediawiki.org/xml/export-0.11/}'

# Regex to match wikilinks: [[Target]] or [[Target|Display]]
# Captures just the target (before | or #)
WIKILINK_RE = re.compile(r'\[\[([^\[\]|#]+)')


def strip_templates(text: str) -> str:
    """
    Remove {{...}} template blocks recursively, handling nested templates.
    
    Templates include: infoboxes, navboxes, citation templates, etc.
    These create artificial link clustering (gravity wells) that distort
    N-Link basin structure.
    """
    result = text
    max_iterations = 100  # Prevent infinite loops on malformed wikitext
    
    for _ in range(max_iterations):
        # Find innermost template (no {{ inside)
        # This handles nesting by removing from inside out
        match = re.search(r'\{\{[^{}]*\}\}', result)
        if not match:
            break
        result = result[:match.start()] + result[match.end():]
    
    return result


def strip_tables(text: str) -> str:
    """
    Remove {|...|} table blocks.
    
    Tables contain structured data with repetitive link patterns
    that would create artificial N-Link convergence.
    """
    result = text
    max_iterations = 50
    
    for _ in range(max_iterations):
        # Find table start
        start = result.find('{|')
        if start == -1:
            break
        
        # Find matching end, handling nested tables
        depth = 1
        pos = start + 2
        while pos < len(result) and depth > 0:
            if result[pos:pos+2] == '{|':
                depth += 1
                pos += 2
            elif result[pos:pos+2] == '|}':
                depth -= 1
                pos += 2
            else:
                pos += 1
        
        result = result[:start] + result[pos:]
    
    return result


def strip_refs(text: str) -> str:
    """Remove <ref>...</ref> and <ref .../> blocks."""
    # Self-closing refs
    result = re.sub(r'<ref[^>]*/>', '', text)
    # Refs with content (non-greedy)
    result = re.sub(r'<ref[^>]*>.*?</ref>', '', result, flags=re.DOTALL | re.IGNORECASE)
    return result


def strip_comments(text: str) -> str:
    """Remove <!-- ... --> HTML comments."""
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def strip_galleries(text: str) -> str:
    """Remove <gallery>...</gallery> blocks."""
    return re.sub(r'<gallery[^>]*>.*?</gallery>', '', text, flags=re.DOTALL | re.IGNORECASE)


def strip_nowiki(text: str) -> str:
    """Remove <nowiki>...</nowiki> blocks (literal text, not parsed)."""
    return re.sub(r'<nowiki>.*?</nowiki>', '', text, flags=re.DOTALL | re.IGNORECASE)


def strip_math(text: str) -> str:
    """Remove <math>...</math> blocks."""
    return re.sub(r'<math[^>]*>.*?</math>', '', text, flags=re.DOTALL | re.IGNORECASE)


def strip_code(text: str) -> str:
    """Remove <code>...</code> and <syntaxhighlight>...</syntaxhighlight> blocks."""
    result = re.sub(r'<code>.*?</code>', '', text, flags=re.DOTALL | re.IGNORECASE)
    result = re.sub(r'<syntaxhighlight[^>]*>.*?</syntaxhighlight>', '', result, flags=re.DOTALL | re.IGNORECASE)
    result = re.sub(r'<source[^>]*>.*?</source>', '', result, flags=re.DOTALL | re.IGNORECASE)
    return result


def clean_wikitext(text: str) -> str:
    """
    Clean wikitext to extract prose-only content.
    
    Order matters: strip nested structures from inside out,
    then remove remaining markup.
    """
    if not text:
        return ""
    
    # 1. Remove elements that might contain templates/tables
    result = strip_comments(text)      # Remove comments first
    result = strip_nowiki(result)      # Remove literal blocks
    result = strip_math(result)        # Remove math blocks
    result = strip_code(result)        # Remove code blocks
    
    # 2. Remove refs (may contain templates)
    result = strip_refs(result)
    
    # 3. Remove templates (from inside out)
    result = strip_templates(result)
    
    # 4. Remove tables
    result = strip_tables(result)
    
    # 5. Remove galleries
    result = strip_galleries(result)
    
    return result


def extract_links_ordered(text: str) -> list[str]:
    """
    Extract wikilink targets from cleaned wikitext, preserving order.
    
    Returns list of normalized target titles in document order.
    This order is CRITICAL for N-Link traversal.
    """
    if not text:
        return []
    
    targets = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target:
            continue
            
        # Skip non-article namespace links (File:, Category:, etc.)
        # But keep links that start with : (explicit mainspace)
        if ':' in target and not target.startswith(':'):
            continue
        
        # Clean leading : for mainspace links
        target = target.lstrip(':')
        if not target:
            continue
        
        # Normalize: spaces to underscores
        target = target.replace(' ', '_')
        
        # Normalize: first char uppercase (MediaWiki convention)
        target = target[0].upper() + target[1:] if len(target) > 1 else target.upper()
        
        targets.append(target)
    
    return targets


def parse_xml_file(xml_path: Path) -> tuple[list[int], list[int], list[str]]:
    """
    Parse a single XML file and extract prose-only links with positions.

    Returns (from_ids, positions, to_titles) lists.
    Position is 1-indexed (1st link, 2nd link, etc.)
    """
    from_ids = []
    positions = []
    to_titles = []

    try:
        # Use iterparse for memory-efficient streaming
        context = ET.iterparse(str(xml_path), events=('end',))

        page_id = None
        page_ns = None
        page_text = None

        for event, elem in context:
            tag = elem.tag.replace(NS, '')

            if tag == 'id' and page_id is None:
                page_id = int(elem.text) if elem.text else None
            elif tag == 'ns':
                page_ns = int(elem.text) if elem.text else 0
            elif tag == 'text':
                page_text = elem.text
            elif tag == 'page':
                # Process completed page
                if page_id is not None and page_ns == 0 and page_text:
                    # Clean wikitext (strip templates, tables, refs, etc.)
                    clean_text = clean_wikitext(page_text)

                    # Extract links in order
                    links = extract_links_ordered(clean_text)

                    # Add with positions (1-indexed)
                    for pos, target in enumerate(links, start=1):
                        from_ids.append(page_id)
                        positions.append(pos)
                        to_titles.append(target)

                # Reset for next page
                page_id = None
                page_ns = None
                page_text = None

                # Clear element to free memory
                elem.clear()

    except ET.ParseError as e:
        print(f"  WARNING: XML parse error in {xml_path.name}: {e}")
        print(f"  Skipping corrupted file. {len(from_ids)} links extracted before error.")

    return from_ids, positions, to_titles


def main():
    start_time = time.time()
    
    # Find all XML files (not .bz2)
    xml_files = sorted([
        f for f in RAW_DIR.glob("enwiki-*.xml*")
        if not f.name.endswith('.bz2') and f.is_file()
    ])
    
    if not xml_files:
        print("No XML files found in", RAW_DIR)
        print("Expected files like: enwiki-YYYYMMDD-pages-articles-multistream*.xml")
        return
    
    print(f"Found {len(xml_files)} XML files to process")
    print("Extracting PROSE-ONLY links (templates, tables, refs stripped)")
    print()
    
    # Accumulate results
    all_from_ids = []
    all_positions = []
    all_to_titles = []
    
    total_links = 0
    
    for i, xml_file in enumerate(xml_files, 1):
        file_start = time.time()
        
        from_ids, positions, to_titles = parse_xml_file(xml_file)
        
        all_from_ids.extend(from_ids)
        all_positions.extend(positions)
        all_to_titles.extend(to_titles)
        
        file_links = len(from_ids)
        total_links += file_links
        elapsed = time.time() - file_start
        
        print(f"[{i}/{len(xml_files)}] {xml_file.name}... {file_links:,} links ({elapsed:.1f}s)")
        
        # Progress update every 10 files
        if i % 10 == 0:
            total_elapsed = time.time() - start_time
            rate = total_links / total_elapsed
            remaining = (len(xml_files) - i) * (total_elapsed / i)
            print(f"  Progress: {total_links:,} total links, ~{remaining/60:.0f}m remaining")
    
    total_elapsed = time.time() - start_time
    print()
    print(f"Extracted {total_links:,} prose-only links in {total_elapsed:.1f}s")
    
    # Write to parquet
    print("Writing parquet...")
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    table = pa.table({
        'from_id': pa.array(all_from_ids, type=pa.int32()),
        'link_position': pa.array(all_positions, type=pa.int32()),
        'to_title': pa.array(all_to_titles, type=pa.string()),
    })
    
    pq.write_table(
        table,
        OUTPUT_FILE,
        compression='zstd',
        compression_level=3,
    )
    
    size_gb = OUTPUT_FILE.stat().st_size / (1024**3)
    print(f"Wrote {OUTPUT_FILE} ({size_gb:.2f} GB)")
    
    # Summary stats
    print()
    print("=== Summary ===")
    print(f"Total prose links: {total_links:,}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Schema: (from_id, link_position, to_title)")
    print(f"  - link_position is 1-indexed for N-Link: f_N(page) = Nth link")


if __name__ == "__main__":
    main()
