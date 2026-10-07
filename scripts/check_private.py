"""Stop private data from reaching this public repo.

  python scripts/check_private.py --staged    files staged for commit (run by the pre-commit hook)
  python scripts/check_private.py --all       every tracked file
  python scripts/check_private.py dist        every file in a folder (CI checks the built site)

Rules:
  - values listed in ../career/private-patterns.txt (phone, ID, address, ...). That list
    lives in the private repo so it never leaks what it protects (set CAREER_DIR if the
    career repo is elsewhere). Without it, only the built-in rules run.
  - built-in: international phone numbers, photos with GPS location, file types that
    belong in the career repo (PDF, Word, zip), and (--staged) a commit email that is
    not your GitHub noreply address. In a built folder the PDFs are the public CVs,
    so their text is checked instead.

Findings show the file, line and rule, never the matched value: CI logs are public.
"""
import io
import os
import re
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
CAREER = Path(os.environ.get("CAREER_DIR", SITE.parent / "career")).resolve()
PATTERNS_FILE = CAREER / "private-patterns.txt"

PHONE_RE = re.compile(r"\+\d[\d\s().-]{7,}\d")
BLOCKED_TYPES = {".pdf", ".doc", ".docx", ".odt", ".zip", ".7z", ".rar"}
PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
TEXT_TYPES = {".md", ".mdx", ".astro", ".html", ".htm", ".css", ".js", ".mjs", ".ts", ".json",
              ".yml", ".yaml", ".toml", ".txt", ".xml", ".svg", ".py", ".sh", ".csv", ""}
SKIP_DIRS = {"node_modules", ".git", ".astro"}


# ---------------------------------------------------------------- rules

def load_patterns():
    """Return [(line number in patterns file, compiled regex)]."""
    if not PATTERNS_FILE.is_file():
        return None
    patterns = []
    for n, raw in enumerate(PATTERNS_FILE.read_text(encoding="utf-8").splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 6 and re.fullmatch(r"[\d\s+().-]+", value):
            # numbers match however they are spaced or dashed
            regex = r"[\s().-]*".join(digits)
        else:
            regex = r"\s+".join(re.escape(w) for w in value.split())
        patterns.append((n, re.compile(regex, re.I)))
    return patterns


def check_text(path, text, patterns):
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for match in PHONE_RE.finditer(line):
            if len(re.sub(r"\D", "", match.group())) >= 9:
                found.append(f"{path}:{n}: looks like a phone number")
        for pattern_line, regex in patterns:
            if regex.search(line):
                found.append(f"{path}:{n}: matches private-patterns.txt line {pattern_line}")
    return found


def photo_has_gps(data):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        return bool(Image.open(io.BytesIO(data)).getexif().get_ifd(0x8825))
    except Exception:
        return False


def pdf_text(data):
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)


def check_file(path, data, patterns, built):
    """built=True for generated output (dist), where PDFs are the public CVs: read them instead of blocking."""
    suffix = Path(path).suffix.lower()
    found = []
    for pattern_line, regex in patterns:
        if regex.search(path):
            found.append(f"{path}: file name matches private-patterns.txt line {pattern_line}")
    if built and suffix == ".pdf":
        found += check_text(path, pdf_text(data), patterns)
    elif suffix in BLOCKED_TYPES:
        found.append(f"{path}: {suffix} files belong in the career repo (they can't be checked for private data)")
    elif suffix in PHOTO_TYPES:
        gps = photo_has_gps(data)
        if gps:
            found.append(f"{path}: photo contains GPS location; re-export it without metadata")
        elif gps is None:
            print(f"  ! Pillow not installed, can't check {path} for GPS location (pip install Pillow)")
    elif suffix in TEXT_TYPES and b"\0" not in data[:8000]:
        found += check_text(path, data.decode("utf-8", errors="ignore"), patterns)
    return found


# ---------------------------------------------------------------- sources

def git(*args):
    return subprocess.run(["git", *args], cwd=SITE, capture_output=True, check=True).stdout


def staged_files():
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").decode().split("\0")
    return [(n, git("show", f":{n}")) for n in names if n]


def tracked_files():
    names = git("ls-files", "-z").decode().split("\0")
    return [(n, (SITE / n).read_bytes()) for n in names if n and (SITE / n).is_file()]


def folder_files(folder):
    folder = Path(folder)
    return [(p.relative_to(folder).as_posix(), p.read_bytes()) for p in sorted(folder.rglob("*"))
            if p.is_file() and not SKIP_DIRS & set(p.parts)]


def check_commit_email():
    email = git("config", "user.email").decode().strip()
    if not email.endswith("@users.noreply.github.com"):
        return [f"commit email is not your GitHub noreply address; run:\n"
                f"    git config user.email \"<id>+<username>@users.noreply.github.com\""]
    return []


def main(args):
    if args == ["--staged"]:
        files, found = staged_files(), check_commit_email()
    elif args == ["--all"]:
        files, found = tracked_files(), []
    elif len(args) == 1 and Path(args[0]).is_dir():
        files, found = folder_files(args[0]), []
    else:
        sys.exit(__doc__)

    patterns = load_patterns()
    if patterns is None:
        if args == ["--staged"]:
            sys.exit(f"Privacy check: {PATTERNS_FILE} not found, so the commit is blocked.\n"
                     "Clone the career repo next to this one, or set CAREER_DIR.")
        print("Privacy check: no private-patterns.txt, running built-in rules only")
        patterns = []

    built = args not in (["--staged"], ["--all"])
    for path, data in files:
        found += check_file(path, data, patterns, built)
    if found:
        print("Privacy check failed:\n  " + "\n  ".join(found))
        sys.exit(1)
    print(f"Privacy check passed ({len(files)} files)")


if __name__ == "__main__":
    main(sys.argv[1:])
