import sys
import os
from pathlib import Path
from pikepdf import Pdf, Optimization

# Compression presets
compression_presets = {
    'light': Optimization(
        compress_streams=True,
        image_quality=95,
        recompress_images=True
    ),
    'medium': Optimization(
        compress_streams=True,
        image_quality=85,
        recompress_images=True
    ),
    'heavy': Optimization(
        compress_streams=True,
        image_quality=60,
        recompress_images=True
    )
}

def optimize_pdfs(compression_level):
    input_dir = Path('A')
    output_dir = Path('B')
    output_dir.mkdir(exist_ok=True)

    suffix = {
        'light': '_lcom.pdf',
        'medium': '_mcom.pdf',
        'heavy': '_hcom.pdf'
    }[compression_level]

    preset = compression_presets[compression_level]

    for pdf_path in input_dir.glob('*.pdf'):
        output_path = output_dir / (pdf_path.stem + suffix)
        try:
            with Pdf.open(pdf_path) as pdf:
                pdf.save(output_path, optimize=preset)
            print(f"Optimized: {pdf_path.name} -> {output_path.name}")
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['light', 'medium', 'heavy']:
        print("Usage: python script.py [light|medium|heavy]")
        sys.exit(1)

    optimize_pdfs(sys.argv[1])
