# Setup Instructions for pdf_compressor

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate

python -m venv .venv
.venv\Scripts\activate

pip install pikepdf

Place PDF files into the A directory.

Then run the script with one of the following commands:

python script.py light

python script.py medium

python script.py heavy

Optimized PDFs will be saved to the B directory with a corresponding suffix:

_lcom.pdf for light

_mcom.pdf for medium

_hcom.pdf for heavy
