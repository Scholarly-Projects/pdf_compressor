#!/usr/bin/env python3
import sys
import subprocess
import platform
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

# Compression tiers with target DPI and JPEG quality
compression_settings = {
    'light':  dict(suffix='_lcom.pdf', dpi=300, quality=90),
    'medium': dict(suffix='_mcom.pdf', dpi=300, quality=75),
    'strong': dict(suffix='_scom.pdf', dpi=72,  quality=65),
}


def remove_quarantine_mac(path: Path):
    if platform.system() == 'Darwin':
        try:
            subprocess.run(['xattr', '-d', 'com.apple.quarantine', str(path)], stderr=subprocess.DEVNULL, check=False)
        except FileNotFoundError:
            print("Warning: 'xattr' command not found. Skipping quarantine removal.")
        except Exception as e:
            print(f"Warning: Could not remove quarantine attribute: {e}")


def process_pdf(input_pdf: Path, output_pdf: Path, dpi: int, quality: int):
    """
    Processes a PDF by replacing images. This version replaces the entire image
    object to avoid color space corruption issues.
    """
    print(f"\n--- Processing {input_pdf.name} ---")
    doc = fitz.open(str(input_pdf))
    images_replaced = 0
    images_skipped = 0

    # For each page, find, replace, and delete images
    for page_num, page in enumerate(doc):
        # Get a list of images on the page
        img_list = page.get_images(full=True)
        if not img_list:
            continue

        # Process images in reverse order to avoid index shifting when deleting
        for img_info in reversed(img_list):
            xref = img_info[0]
            
            # Get the image's bounding box on the page
            img_rect = page.get_image_bbox(img_info)
            if not img_rect:
                print(f"  - Page {page_num+1}, Image (xref {xref}): Could not get bounding box. Skipping.")
                images_skipped += 1
                continue

            # --- Extract and process the image ---
            try:
                img_dict = doc.extract_image(xref)
                orig_data = img_dict['image']
                img = Image.open(io.BytesIO(orig_data))

                # Calculate scaling
                src_dpi = img.info.get('dpi', (150, 150))[0]
                # --- FIX: Explicitly cast to float to handle Fraction objects ---
                scale = float(dpi) / float(src_dpi)
                new_size = (int(img.width * scale), int(img.height * scale))

                # Avoid scaling up or making zero-size images
                if new_size[0] > 0 and new_size[1] > 0 and scale < 1.0:
                    img = img.resize(new_size, Image.LANCZOS)
                    print(f"  - Page {page_num+1}, Image (xref {xref}): Resized from {img_dict['width']}x{img_dict['height']} to {new_size[0]}x{new_size[1]}")
                else:
                    print(f"  - Page {page_num+1}, Image (xref {xref}): Not resizing (scale factor: {scale:.2f}).")

                # Encode to JPEG in memory
                buf = io.BytesIO()
                img.convert('RGB').save(buf, format='JPEG', quality=quality, optimize=True)
                new_jpeg_data = buf.getvalue()

                # --- Perform the replacement ---
                # Insert the new JPEG into the page at the same position
                page.insert_image(img_rect, stream=new_jpeg_data)
                
                # Delete the original image to avoid overlap
                page.delete_image(xref)
                
                print(f"    -> Replaced image on page.")
                images_replaced += 1

            except Exception as e:
                print(f"  - ERROR processing Page {page_num+1}, Image (xref {xref}): {e}")
                images_skipped += 1

    print(f"--- Summary for {input_pdf.name}: {images_replaced} images replaced, {images_skipped} images skipped. ---")

    # Save the final PDF
    print(f"Saving to {output_pdf}...")
    doc.save(str(output_pdf), garbage=4, deflate=True, clean=True)
    doc.close()

    remove_quarantine_mac(output_pdf)

    # Compute size reduction percentage
    orig_size = input_pdf.stat().st_size
    out_size = output_pdf.stat().st_size
    reduction = (orig_size - out_size) / orig_size * 100
    print(f"Finished: {input_pdf.name} -> {output_pdf.name} | size reduced by {reduction:.1f}% ({orig_size//1024}KB → {out_size//1024}KB)")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in compression_settings:
        print("Usage: python script.py [light|medium|strong]")
        sys.exit(1)
    level = sys.argv[1]
    settings = compression_settings[level]

    input_dir = Path('A')
    output_dir = Path('B')
    output_dir.mkdir(exist_ok=True)

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    pdf_files = list(input_dir.glob('*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in '{input_dir}'.")
        sys.exit(1)

    for pdf in pdf_files:
        out = output_dir / (pdf.stem + settings['suffix'])
        try:
            process_pdf(pdf, out, settings['dpi'], settings['quality'])
        except Exception as e:
            print(f"!!!!!!!!!! FATAL ERROR processing {pdf.name}: {e} !!!!!!!!!!!")


if __name__ == '__main__':
    main()