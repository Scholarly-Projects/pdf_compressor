import sys
import subprocess
import platform
from pathlib import Path

# Custom quality settings with actual downsampling controls
compression_settings = {
    'light': {
        'suffix': '_lcom.pdf',
        'ColorImageResolution': 300,
        'GrayImageResolution': 300,
        'MonoImageResolution': 300,
        'JPEGQ': 80
    },
    'medium': {
        'suffix': '_mcom.pdf',
        'ColorImageResolution': 144,
        'GrayImageResolution': 144,
        'MonoImageResolution': 144,
        'JPEGQ': 70
    },
    'strong': {
        'suffix': '_scom.pdf',
        'ColorImageResolution': 72,
        'GrayImageResolution': 72,
        'MonoImageResolution': 72,
        'JPEGQ': 60
    }
}

def remove_quarantine_mac(output_path):
    if platform.system() == 'Darwin':
        try:
            subprocess.run(['xattr', '-d', 'com.apple.quarantine', str(output_path)], stderr=subprocess.DEVNULL)
        except Exception:
            pass

def compress_with_gs(input_path, output_path, settings):
    cmd = [
        'gs',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        '-dPreserveEPSInfo=true',
        '-dAutoFilterColorImages=false',
        '-dAutoFilterGrayImages=false',
        '-dColorImageFilter=/DCTEncode',
        '-dGrayImageFilter=/DCTEncode',
        f'-dColorImageDownsampleType=/Average',
        f'-dGrayImageDownsampleType=/Average',
        f'-dMonoImageDownsampleType=/Subsample',
        f'-dColorImageResolution={settings["ColorImageResolution"]}',
        f'-dGrayImageResolution={settings["GrayImageResolution"]}',
        f'-dMonoImageResolution={settings["MonoImageResolution"]}',
        f'-dDownsampleColorImages=true',
        f'-dDownsampleGrayImages=true',
        f'-dDownsampleMonoImages=true',
        f'-dColorImageDownsampleThreshold=1.0',
        f'-dGrayImageDownsampleThreshold=1.0',
        f'-dMonoImageDownsampleThreshold=1.0',
        f'-dJPEGQ={settings["JPEGQ"]}',
        f'-sOutputFile={output_path}',
        str(input_path)
    ]
    try:
        subprocess.run(cmd, check=True)
        remove_quarantine_mac(output_path)
        print(f"Compressed: {input_path.name} -> {output_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"Error compressing {input_path.name}: {e}")

def optimize_pdfs(level):
    if level not in compression_settings:
        print("Invalid compression level. Choose from: light, medium, strong")
        sys.exit(1)

    input_dir = Path('A')
    output_dir = Path('B')
    output_dir.mkdir(exist_ok=True)

    settings = compression_settings[level]
    suffix = settings['suffix']

    for pdf_file in input_dir.glob('*.pdf'):
        output_pdf = output_dir / (pdf_file.stem + suffix)
        compress_with_gs(pdf_file, output_pdf, settings)

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in compression_settings:
        print("Usage: python script.py [light|medium|strong]")
        sys.exit(1)

    optimize_pdfs(sys.argv[1])
