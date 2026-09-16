"""
Pull the text out of the project's methodology PDF and Word reports, so the study
limits can be read from the documents rather than inferred from the code.

Dependency-free: .docx is a zip of XML, and PDF text is extracted with whatever
reader happens to be available.

Read-only.
"""

import glob
import os
import re
import zipfile

FOLDER = r"D:\Yusra\I4 Safety Ana;ysis"

# Phrases that mark where the study extent is described.
KEYWORDS = [
    "limit", "extent", "study area", "begin", "end", "terminus", "termini",
    "from ", " to ", "mainline", "ramp", "gore", "interchange", "milepost",
    "mile post", "MP ", "segment", "Bethlehem", "McIntosh", "Branch Forbes",
    "influence area", "250", "crash", "analysis period",
]


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if re.match(r"word/(document|header|footer)", n)]
        out = []
        for n in names:
            xml = z.read(n).decode("utf-8", "replace")
            xml = re.sub(r"</w:p>", "\n", xml)
            xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
            out.append(re.sub(r"<[^>]+>", "", xml))
    return "\n".join(out)


def pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return None
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def show(label, text, limit_lines=70):
    print("=" * 74)
    print(label)
    print("=" * 74)
    if text is None:
        print("  (no PDF reader available - install pypdf)")
        return
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    print(f"  {len(lines)} non-empty lines\n")

    hits = [ln for ln in lines
            if any(k.lower() in ln.lower() for k in KEYWORDS) and len(ln) > 25]

    seen, shown = set(), 0
    for ln in hits:
        k = ln[:90]
        if k in seen:
            continue
        seen.add(k)
        print("  | " + ln[:250])
        shown += 1
        if shown >= limit_lines:
            print("  ... (truncated)")
            break
    print()


for path in sorted(glob.glob(os.path.join(FOLDER, "*.docx"))):
    if os.path.basename(path).startswith("~$"):
        continue
    show(os.path.basename(path), docx_text(path))

for path in sorted(glob.glob(os.path.join(FOLDER, "*.pdf"))):
    show(os.path.basename(path), pdf_text(path))
