#!/usr/bin/env python3
import sys
import subprocess
import platform
import tempfile
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
import pikepdf

# Compression tiers with target DPI and JPEG quality
compression_settings = {
    'light':  dict(suffix='_lcom.pdf', dpi=300, quality=80),
    'medium': dict(suffix='_mcom.pdf', dpi=144, quality=65),
    'strong': dict(suffix='_scom.pdf', dpi=72,  quality=50),
}


def remove_quarantine_mac(path: Path):
    if platform.system() == 'Darwin':
        try:
            subprocess.run(['xattr', '-d', 'com.apple.quarantine', str(path)], stderr=subprocess.DEVNULL)
        except Exception:
            pass


def process_pdf(input_pdf: Path, output_pdf: Path, dpi: int, quality: int):
    doc = fitz.open(str(input_pdf))

    # For each page, extract and recompress images with fallback
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            img_dict = doc.extract_image(xref)
            orig_data = img_dict['image']
            img = Image.open(io.BytesIO(orig_data))

            # Calculate scaling
            src_dpi = img.info.get('dpi', (300, 300))[0]
            scale = dpi / src_dpi
            new_size = (int(img.width * scale), int(img.height * scale))
            if new_size[0] > 0 and new_size[1] > 0:
                img = img.resize(new_size, Image.LANCZOS)

            # Encode to JPEG
            buf = io.BytesIO()
            img.convert('RGB').save(buf, format='JPEG', quality=quality)
            new_data = buf.getvalue()

            # Only replace if smaller
            if len(new_data) < len(orig_data):
                doc.update_stream(xref, new_data)

    # Save intermediate PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmpf:
        tmp_path = Path(tmpf.name)
    try:
        doc.save(tmp_path, garbage=4, deflate=True)
    finally:
        doc.close()

    # Optimize structure
    with pikepdf.open(tmp_path) as pdf:
        pdf.save(str(output_pdf), linearize=True, compress_streams=True)
    tmp_path.unlink()

    remove_quarantine_mac(output_pdf)
    # Compute size reduction percentage
    orig_size = input_pdf.stat().st_size
    out_size = output_pdf.stat().st_size
    reduction = (orig_size - out_size) / orig_size * 100
    print(f"Compressed: {input_pdf.name} -> {output_pdf.name} | size reduced by {reduction:.1f}% ({orig_size//1024}KB → {out_size//1024}KB)")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in compression_settings:
        print("Usage: python script.py [light|medium|strong]")
        sys.exit(1)
    level = sys.argv[1]
    settings = compression_settings[level]

    input_dir = Path('A')
    output_dir = Path('B')
    output_dir.mkdir(exist_ok=True)

    for pdf in input_dir.glob('*.pdf'):
        out = output_dir / (pdf.stem + settings['suffix'])
        try:
            process_pdf(pdf, out, settings['dpi'], settings['quality'])
        except Exception as e:
            print(f"Error processing {pdf.name}: {e}")


if __name__ == '__main__':
    main()
