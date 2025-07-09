# Setup Instructions for pdf_compressor

## Activate Environment

macOS/Linux:

bash
python3 -m venv .venv
source .venv/bin/activate

Windows

python -m venv .venv
.venv\Scripts\activate

## Install Libraries

pip install pymupdf Pillow pikepdf

## Place PDF files into the A directory.

## Then run the script with one of the following commands:

python script.py light

python script.py medium

python script.py strong

## Optimized PDFs will be saved to the B directory with a corresponding suffix:

_lcom.pdf for light

_mcom.pdf for medium

_scom.pdf for strong

## Check Output

find B -name "*.pdf" -exec du -k {} + | sort -n | awk '{printf "%s KB\t%s\n", $1, $2}'
