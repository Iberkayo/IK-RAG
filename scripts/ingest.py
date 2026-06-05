import os
import json
import re
import unicodedata
import fitz
import pandas as pd

# Directory definitions
RAW_DIR = r"C:\Users\iberkayo\Desktop\IK-Rag\data\raw"
PROCESSED_DIR = r"C:\Users\iberkayo\Desktop\IK-Rag\data\processed"
SYNTHETIC_DIR = r"C:\Users\iberkayo\Desktop\IK-Rag\data\synthetic"

# Ensure output directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Document mapping for raw files
DOC_MAPPING = {
    "4857-sayili-is-kanunu.pdf": ("4857 Sayılı İş Kanunu", "Mevzuat"),
    "4857-sayılı-iş-kanunu.pdf": ("4857 Sayılı İş Kanunu", "Mevzuat"),
    "yillik-ucretli-izin-yonetmeligi.pdf": ("Yıllık Ücretli İzin Yönetmeliği", "Mevzuat"),
    "yıllık-ücretli-izin-yönetmeliği.pdf": ("Yıllık Ücretli İzin Yönetmeliği", "Mevzuat"),
    "calisan-el-kitabi.pdf": ("Çalışan El Kitabı", "İK Dokümanı"),
    "calisan_el_kitabi.pdf": ("Çalışan El Kitabı", "İK Dokümanı"),
    "calisanin-el-kitabi_c5a3f74fbefd497f862880bbf49d7abe.pdf": ("Çalışan El Kitabı (Gelişim Ünv.)", "İK Dokümanı"),
    "insan-kaynaklari-el-kitabi.pdf": ("İnsan Kaynakları El Kitabı", "İK Dokümanı"),
    "2-i-nsan-kaynaklari-yo-neti-mi-prosedu-ru-1740125299.pdf": ("İnsan Kaynakları Yönetim Prosedürü", "İK Dokümanı"),
    "2-I-NSAN-KAYNAKLARI-YO-NETI-MI-PROSEDU-RU-1740125299.pdf": ("İnsan Kaynakları Yönetim Prosedürü", "İK Dokümanı"),
    "ikpr01-insan-kaynaklari-yonetim-proseduru-rev02pdf_20220307162008.pdf": ("İnsan Kaynakları Yönetim Prosedürü (Rev02)", "İK Dokümanı"),
    "insan-kaynaklari-proseduru.pdf": ("İnsan Kaynakları Yönetim Prosedürü", "İK Dokümanı")
}

def clean_turkish_text(text: str) -> str:
    if not text:
        return ""
    
    # Unicode Normalization (NFC)
    text = unicodedata.normalize("NFC", text)
    
    # Common broken Turkish encoding mappings
    char_map = {
        "þ": "ş", "Þ": "Ş",
        "ð": "ğ", "Ð": "Ğ",
        "ý": "ı", "Ý": "İ",
        "ı̇": "ı",
        "i̇": "i",
    }
    for bad, good in char_map.items():
        text = text.replace(bad, good)
        
    # Resolve line-break hyphenations
    text = re.sub(r'(\w+)-\n\s*(\w+)', r'\1\2', text)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Remove system control chars, keep newlines
    text = "".join(ch for ch in text if ch == "\n" or not unicodedata.category(ch).startswith("C"))
    
    # Normalize spacing
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Split by lines and clean
    lines = text.split("\n")
    paragraphs = []
    current_para = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            continue
        
        # Check if new line starts with a list bullet, number, or is uppercase
        is_new_indicator = (
            re.match(r'^(?:\d+\.|\*|-|•|[A-ZÇĞİÖŞÜ]{2,}\b)', line_stripped) or
            line_stripped.isupper()
        )
        
        if is_new_indicator and current_para:
            paragraphs.append(" ".join(current_para))
            current_para = [line_stripped]
        else:
            current_para.append(line_stripped)
            
    if current_para:
        paragraphs.append(" ".join(current_para))
        
    # Clean each paragraph
    cleaned_paragraphs = []
    for p in paragraphs:
        p_clean = re.sub(r'\s+', ' ', p).strip()
        if p_clean:
            cleaned_paragraphs.append(p_clean)
            
    return "\n\n".join(cleaned_paragraphs)

def extract_section(paragraph: str) -> str:
    """Try to detect section header from the paragraph."""
    p_stripped = paragraph.strip()
    if len(p_stripped) < 80:
        # Matches "Madde 1 -", "MADDE 24."
        if re.match(r'^(?:Madde\s+\d+|MADDE\s+\d+)', p_stripped):
            return p_stripped
        # Matches "1. AMAÇ", "6.2.1 GÖREV TANIMLARI"
        if re.match(r'^(?:\d+(?:\.\d+)+\s+[A-ZÇĞİÖŞÜa-zçğıiöşü])|^(?:\d+\.\s+[A-ZÇĞİÖŞÜa-zçğıiöşü])', p_stripped):
            return p_stripped
        # Matches "BİRİNCİ BÖLÜM", "İKİNCİ BÖLÜM"
        if re.match(r'^(?:[A-ZÇĞİÖŞÜ]+\s+BÖLÜM|BÖLÜM\s+[A-ZÇĞİÖŞÜ]+)', p_stripped, re.IGNORECASE):
            return p_stripped
        # Matches short all-caps paragraphs (e.g. "KAPSAM", "SORUMLULUKLAR")
        if p_stripped.isupper() and len(p_stripped) > 2 and not p_stripped.replace(" ", "").isdigit():
            return p_stripped
    return None

def is_inside_any_table(block_bbox, tables) -> bool:
    """Checks if a text block bbox falls inside any table bbox."""
    bx0, by0, bx1, by1 = block_bbox
    # Use block center point to determine membership
    cx = (bx0 + bx1) / 2
    cy = (by0 + by1) / 2
    for tab in tables:
        tx0, ty0, tx1, ty1 = tab.bbox
        # Add a small margin of 2 pixels for boundary cases
        if (tx0 - 2) <= cx <= (tx1 + 2) and (ty0 - 2) <= cy <= (ty1 + 2):
            return True
    return False

def table_to_markdown(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for row in rows:
        padded_row = row + [""] * max(0, len(headers) - len(row))
        lines.append("| " + " | ".join(padded_row[:len(headers)]) + " |")
    return "\n".join(lines)

def make_prefix(title: str, category: str, section: str) -> str:
    """Creates a metadata prefix for the chunk text to assist embedding match scores."""
    prefix_parts = []
    if title:
        prefix_parts.append(f"[Döküman: {title}]")
    if category:
        prefix_parts.append(f"[Kategori: {category}]")
    if section:
        prefix_parts.append(f"[Bölüm: {section}]")
    return " ".join(prefix_parts) + "\n"

def chunk_text(text: str, min_chunk_size=300, max_chunk_size=900) -> list:
    """Chunks text into semantic paragraphs, keeping chunk size balanced."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_size = 0
    current_section = "Genel"
    
    for p in paragraphs:
        sec = extract_section(p)
        if sec:
            current_section = sec
            
        p_len = len(p)
        if p_len > max_chunk_size:
            # Split large paragraph by sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', p)
            for s in sentences:
                s_len = len(s)
                if current_size + s_len > max_chunk_size and current_chunk:
                    chunks.append({
                        "content": " ".join(current_chunk),
                        "section": current_section
                    })
                    current_chunk = [s]
                    current_size = s_len
                else:
                    current_chunk.append(s)
                    current_size += s_len
        else:
            if current_size + p_len > max_chunk_size and current_chunk:
                chunks.append({
                    "content": " ".join(current_chunk),
                    "section": current_section
                })
                current_chunk = [p]
                current_size = p_len
            else:
                current_chunk.append(p)
                current_size += p_len
                
        if current_size >= min_chunk_size and current_size <= max_chunk_size:
            chunks.append({
                "content": " ".join(current_chunk),
                "section": current_section
            })
            current_chunk = []
            current_size = 0
            
    if current_chunk:
        chunks.append({
            "content": " ".join(current_chunk),
            "section": current_section
        })
        
    return chunks

def process_pdfs():
    all_chunks = []
    
    if not os.path.exists(RAW_DIR):
        print(f"Raw directory does not exist: {RAW_DIR}")
        return all_chunks
        
    for filename in os.listdir(RAW_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
            
        file_path = os.path.join(RAW_DIR, filename)
        print(f"\nProcessing PDF: {filename}...")
        
        # Get metadata mapping or guess
        title, category = DOC_MAPPING.get(filename, (None, None))
        if not title:
            name_no_ext = os.path.splitext(filename)[0]
            title = name_no_ext.replace("-", " ").replace("_", " ").title()
            category = "İK Dokümanı"
            
        doc = fitz.open(file_path)
        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            
            # 1. Detect Tables on Page
            tables = page.find_tables()
            tables_list = tables.tables
            
            # 2. Extract Body Text (excluding areas occupied by tables to prevent duplicate/broken text)
            blocks = page.get_text("blocks")
            body_blocks = []
            for b in blocks:
                bbox = b[:4]
                text_content = b[4]
                if is_inside_any_table(bbox, tables_list):
                    continue
                body_blocks.append(text_content)
                
            raw_body_text = "\n".join(body_blocks)
            cleaned_body_text = clean_turkish_text(raw_body_text)
            
            # 3. Chunk Body Text
            if cleaned_body_text.strip():
                text_chunks = chunk_text(cleaned_body_text)
                for chunk_idx, chunk in enumerate(text_chunks):
                    chunk_id = f"{filename}_p{page_num}_text_c{chunk_idx+1}"
                    prefix = make_prefix(title, category, chunk["section"])
                    prefixed_content = prefix + chunk["content"]
                    
                    doc_chunk = {
                        "doc_id": chunk_id,
                        "title": title,
                        "category": category,
                        "section": chunk["section"],
                        "source_file": filename,
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "content": prefixed_content
                    }
                    all_chunks.append(doc_chunk)
            
            # 4. Extract and Process Tables
            for tab_idx, tab in enumerate(tables_list):
                try:
                    df = tab.to_pandas()
                    
                    # Clean columns and strip newlines/spaces
                    cleaned_cols = []
                    for col in df.columns:
                        col_str = clean_turkish_text(str(col).replace('\n', ' ').strip())
                        cleaned_cols.append(col_str)
                    df.columns = cleaned_cols
                    
                    # Clean cell values and convert empty/null strings to None
                    def clean_cell(val):
                        if val is None:
                            return None
                        val_str = str(val).replace('\n', ' ').strip()
                        cleaned = clean_turkish_text(val_str)
                        if cleaned in ('', 'None', 'nan'):
                            return None
                        return cleaned
                        
                    df = df.map(clean_cell)
                    
                    # Forward-fill merged cells vertically, then horizontally
                    df = df.ffill(axis=0).ffill(axis=1)
                    
                    headers = df.columns.tolist()
                    rows = df.fillna("").values.tolist()
                    
                    # Store complete table as one chunk (if reasonable size)
                    full_table_md = table_to_markdown(headers, rows)
                    if full_table_md.strip():
                        # Complete table chunk
                        chunk_id = f"{filename}_p{page_num}_table_{tab_idx+1}_full"
                        prefix = make_prefix(title, category, f"Tablo {tab_idx+1}")
                        prefixed_content = prefix + full_table_md
                        
                        doc_chunk = {
                            "doc_id": chunk_id,
                            "title": title,
                            "category": category,
                            "section": f"Tablo {tab_idx+1}",
                            "source_file": filename,
                            "chunk_id": chunk_id,
                            "page": page_num,
                            "content": prefixed_content
                        }
                        all_chunks.append(doc_chunk)
                        
                        # Store table row-by-row to isolate rows (so they are searchable individually)
                        for r_idx, row in enumerate(rows):
                            row_md = table_to_markdown(headers, [row])
                            chunk_id_row = f"{filename}_p{page_num}_table_{tab_idx+1}_r{r_idx+1}"
                            prefix_row = make_prefix(title, category, f"Tablo {tab_idx+1} - Satır {r_idx+1}")
                            prefixed_content_row = prefix_row + row_md
                            
                            doc_chunk_row = {
                                "doc_id": chunk_id_row,
                                "title": title,
                                "category": category,
                                "section": f"Tablo {tab_idx+1} Satır",
                                "source_file": filename,
                                "chunk_id": chunk_id_row,
                                "page": page_num,
                                "content": prefixed_content_row
                            }
                            all_chunks.append(doc_chunk_row)
                            
                except Exception as table_err:
                    print(f"Error processing table {tab_idx+1} on page {page_num} of {filename}: {table_err}")
                    
        doc.close()
        
    print(f"\nExtracted {len(all_chunks)} chunks from PDF files (with structured tables & prefixes).")
    return all_chunks

def process_synthetics():
    all_chunks = []
    if not os.path.exists(SYNTHETIC_DIR):
        print(f"Synthetic directory does not exist: {SYNTHETIC_DIR}")
        return all_chunks
        
    for filename in os.listdir(SYNTHETIC_DIR):
        if not filename.lower().endswith(".jsonl"):
            continue
            
        file_path = os.path.join(SYNTHETIC_DIR, filename)
        print(f"Processing Synthetic JSONL: {filename}...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk_id = f"{filename}_l{line_idx+1}"
                    
                    title = data.get("title", "İş Tanımı")
                    category = data.get("category", "Sentetik İş Tanımı")
                    section = data.get("section", "Genel")
                    content = data.get("content", "")
                    
                    # Prefix synthetic content as well to align format
                    prefix = make_prefix(title, category, section)
                    prefixed_content = prefix + content
                    
                    doc_chunk = {
                        "doc_id": data.get("doc_id", chunk_id),
                        "title": title,
                        "category": category,
                        "section": section,
                        "source_file": filename,
                        "chunk_id": chunk_id,
                        "page": 1,
                        "content": prefixed_content
                    }
                    all_chunks.append(doc_chunk)
                except Exception as e:
                    print(f"Error parsing line {line_idx+1} in {filename}: {e}")
                    
    print(f"Processed {len(all_chunks)} chunks from Synthetic files.")
    return all_chunks

def main():
    pdf_chunks = process_pdfs()
    synthetic_chunks = process_synthetics()
    
    total_chunks = pdf_chunks + synthetic_chunks
    
    output_path = os.path.join(PROCESSED_DIR, "chunks.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in total_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            
    print(f"\nSaved {len(total_chunks)} total chunks to: {output_path}")
    
    # Save a metadata description of the processed run
    metadata = {
        "total_chunks": len(total_chunks),
        "pdf_chunks_count": len(pdf_chunks),
        "synthetic_chunks_count": len(synthetic_chunks),
        "files_processed": list(set(c["source_file"] for c in total_chunks))
    }
    
    meta_path = os.path.join(PROCESSED_DIR, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Saved metadata file to: {meta_path}")

if __name__ == "__main__":
    main()
