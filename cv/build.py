"""Build tailored CVs (HTML + PDF) from Markdown.

Usage (from the repo root):
  python cv/build.py                                    every role, with private details
  python cv/build.py ai                                 one role, with private details
  python cv/build.py new Bosch "Robotics Engineer" ai   create an application in the career repo
  python cv/build.py ../career/applications/X.md        build the CV for one application
  python cv/build.py --public                           every role WITHOUT private details (website)
  python cv/build.py --json                             CV data for the website

Public content lives in content/cv/ (master.md, roles/). Private details (phone, ...)
live in the career repo next to this one (../career/private.yml, or set CAREER_DIR).
They are only added to non-public builds, whose output goes to ../career/output/.

PDFs are printed with Microsoft Edge or Chrome in headless mode, so no LaTeX or
extra software is needed.
"""
import base64
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
CONTENT = SITE / "content" / "cv"
CAREER = Path(os.environ.get("CAREER_DIR", SITE.parent / "career")).resolve()
PUBLIC_OUT = SITE / "public" / "cv"
JSON_OUT = SITE / "src" / "data" / "cv.json"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
PRIVATE_KEYS = {"phone", "address", "birth_date"}   # never in a public build, even if added to master.md
TAG_RE = re.compile(r"\s*\{([\w\s,-]+)\}\s*$")
MAX_PAGES = 2


# ---------------------------------------------------------------- parsing

def read_md(path):
    """Return (front_matter_dict, body) of a Markdown file."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v) for v in value]


def filter_by_tags(body, active):
    """Drop lines (or whole ### entries) whose {tags} don't match the active tags."""
    kept, skip_level = [], 0
    for line in body.splitlines():
        level = len(line) - len(line.lstrip("#")) if line.startswith("#") else 0
        if skip_level and level and level <= skip_level:
            skip_level = 0
        if skip_level:
            continue
        m = TAG_RE.search(line)
        if m:
            tags = {t for t in re.split(r"[,\s]+", m.group(1)) if t}
            if not tags & active:
                skip_level = level
                continue
            line = line[:m.start()]
        kept.append(line)
    return "\n".join(kept)


def split_sections(body):
    sections, name = {}, None
    for line in body.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            sections[name] = []
        elif name:
            sections[name].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def role_names():
    return sorted(p.stem for p in (CONTENT / "roles").glob("*.md"))


def file_stem(person, role_name):
    return f"{person.get('file_name', 'CV')}_{role_name}"


def load_person(public):
    """Header fields from master.md, plus ../career/private.yml unless public."""
    person, _ = read_md(CONTENT / "master.md")
    person = {k: v for k, v in person.items() if k not in PRIVATE_KEYS}
    if public:
        return person
    private = CAREER / "private.yml"
    if not private.is_file():
        sys.exit(f"{private} not found. Clone the career repo next to this one, set CAREER_DIR, "
                 "or use --public for a CV without private details.")
    return {**person, **(yaml.safe_load(private.read_text(encoding="utf-8")) or {})}


def load_role(role_name, app=None, app_body=""):
    """Return (role, headline, summary, sections, order, photo) for a role, filtered by its tags."""
    app = app or {}
    _, master = read_md(CONTENT / "master.md")
    role_file = CONTENT / "roles" / f"{role_name}.md"
    if not role_file.is_file():
        sys.exit(f"Unknown role '{role_name}'. Available: {', '.join(role_names())}")
    role, role_summary = read_md(role_file)

    active = set(as_list(role.get("tags")) or [role_name]) | set(as_list(app.get("extra_tags")))
    master = filter_by_tags(strip_comments(master), active)
    summary = strip_comments(app_body).strip() or strip_comments(role_summary).strip()
    headline = app.get("headline") or role.get("headline", "")
    photo = app.get("photo", role.get("photo", True))
    sections = split_sections(master)
    order = as_list(role.get("sections")) or ["Summary", *sections]
    return role, headline, summary, sections, order, photo


# ---------------------------------------------------------------- rendering

def md(text):
    return markdown.markdown(text, extensions=["sane_lists"])


def md_inline(text):
    return re.sub(r"^<p>(.*)</p>$", r"\1", md(text.strip()), flags=re.S)


def render_entry(head, rest):
    """'### Title @ Org | Place | Dates' -> structured HTML entry."""
    fields = [f.strip() for f in head.split("|")]
    title, place, dates = fields[0], "", ""
    if len(fields) == 2:
        dates = fields[1]
    elif len(fields) > 2:
        place, dates = ", ".join(fields[1:-1]), fields[-1]
    role, _, org = title.partition(" @ ")
    sub = ", ".join(x for x in (org.strip(), place) if x)
    out = ['<div class="entry"><div class="entry-head">',
           f'<span class="entry-title">{md_inline(role)}</span>',
           f'<span class="entry-date">{md_inline(dates)}</span></div>']
    if sub:
        out.append(f'<div class="entry-sub">{md_inline(sub)}</div>')
    if rest.strip():
        out.append(md(rest))
    out.append("</div>")
    return "".join(out)


def render_section(text):
    parts = re.split(r"(?m)^### ", text)
    out = [md(parts[0])] if parts[0].strip() else []
    for part in parts[1:]:
        head, _, rest = part.partition("\n")
        out.append(render_entry(head, rest))
    return "".join(out)


def render_body(summary, sections, order):
    """Return [(section title, html)] in the role's order."""
    out = []
    for name in order:
        if name == "Summary":
            if summary:
                out.append(("Professional Summary", md(summary)))
        elif sections.get(name):
            out.append((name, render_section(sections[name])))
        else:
            print(f"  ! section '{name}' not found in master.md")
    return out


def render_html(person, headline, summary, sections, order, photo):
    contact = " · ".join(html.escape(person[k]) for k in ("email", "phone", "location") if person.get(k))
    links = " · ".join(f'<a href="https://{l}">{html.escape(l)}</a>' for l in person.get("links", []))
    photo_html = ""
    if photo:
        p = CONTENT / person.get("photo", "")
        if p.is_file():
            data = base64.b64encode(p.read_bytes()).decode()
            photo_html = f'<img class="photo" src="data:image/jpeg;base64,{data}" alt="">'
    body = "".join(f"<section><h2>{html.escape(name)}</h2>{content}</section>"
                   for name, content in render_body(summary, sections, order))
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{html.escape(person['name'])} – CV</title>
<style>{css}</style></head>
<body><header>{photo_html}
<h1>{html.escape(person['name'])}</h1>
<div class="headline">{html.escape(headline)}</div>
<div class="contact">{contact}</div>
<div class="contact">{links}</div>
</header>
{body}
</body></html>"""


# ---------------------------------------------------------------- output

def find_browser():
    for b in BROWSERS:
        if Path(b).is_file():
            return b
    for name in ("msedge", "chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def print_pdf(html_path, pdf_path):
    browser = find_browser()
    if not browser:
        print("  ! Edge/Chrome not found: HTML written, PDF skipped")
        return False
    pdf_path.unlink(missing_ok=True)
    # Linux CI runners restrict Chrome's sandbox; the HTML printed here is our own.
    sandbox = ["--no-sandbox"] if sys.platform.startswith("linux") else []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([browser, "--headless", "--disable-gpu", *sandbox, f"--user-data-dir={profile}",
                        "--no-pdf-header-footer", "--print-to-pdf-no-header",
                        f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                       capture_output=True, timeout=120)
    return pdf_path.is_file()


def page_count(pdf_path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def checks(html_text, keywords):
    text = html.unescape(re.sub(r"<[^>]+>", " ", html_text)).lower()
    if "todo" in text:
        print("  ! CV still contains TODO placeholders (fill them in master.md)")
    if keywords:
        missing = [k for k in keywords if k.lower() not in text]
        print(f"  keywords from job ad found: {len(keywords) - len(missing)}/{len(keywords)}")
        if missing:
            print(f"  ! missing (add them if you truly have the skill): {', '.join(missing)}")


def build(role_name, out_dir, app=None, app_body="", out_name=None, public=False):
    app = app or {}
    person = load_person(public)
    _, headline, summary, sections, order, photo = load_role(role_name, app, app_body)

    page = render_html(person, headline, summary, sections, order, photo)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = out_name or file_stem(person, role_name)
    html_path, pdf_path = out_dir / f"{name}.html", out_dir / f"{name}.pdf"
    html_path.write_text(page, encoding="utf-8")
    print(f"- {role_name}{' / ' + app['company'] if app.get('company') else ''}{' (public)' if public else ''}")
    if print_pdf(html_path, pdf_path):
        pages = page_count(pdf_path)
        warn = f"  ! over {MAX_PAGES} pages, consider trimming" if pages and pages > MAX_PAGES else ""
        print(f"  {pdf_path} ({pages} pages){warn}")
        if public:
            html_path.unlink()   # the website only offers the PDF
    checks(page, as_list(app.get("keywords")))


def export_json():
    """Write the public CV data (every role, already rendered to HTML) for the website."""
    person = load_person(public=True)
    roles = []
    for name in role_names():
        role, headline, summary, sections, order, _ = load_role(name)
        roles.append({"id": name, "headline": headline, "website": bool(role.get("website")),
                      "pdf": f"/cv/{file_stem(person, name)}.pdf",
                      "sections": [{"title": t, "html": h} for t, h in render_body(summary, sections, order)]})
    data = {"person": {k: person[k] for k in ("name", "email", "location", "links") if k in person},
            "roles": roles}
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"- website data: {JSON_OUT.relative_to(SITE).as_posix()}")


def build_application(path):
    path = Path(path)
    app, body = read_md(path)
    if not app.get("role"):
        sys.exit(f"{path}: set 'role:' in the front matter")
    person, _ = read_md(CONTENT / "master.md")
    company = re.sub(r"[^\w-]+", "", str(app.get("company", path.stem)).replace(" ", "-"))
    build(app["role"], CAREER / "output" / path.stem, app, body, f"{person.get('file_name', 'CV')}_{company}")


def new_application(company, position, role):
    today = datetime.date.today()
    slug = re.sub(r"[^\w-]+", "", company.replace(" ", "-"))
    path = CAREER / "applications" / f"{today:%Y-%m}_{slug}.md"
    if path.exists():
        sys.exit(f"{path} already exists")
    text = (CAREER / "applications" / "_template.md").read_text(encoding="utf-8")
    for key, val in {"company": company, "position": position, "role": role, "date": f"{today}"}.items():
        text = text.replace("{" + key + "}", val)
    path.write_text(text, encoding="utf-8")
    rel = Path(os.path.relpath(path)).as_posix()
    print(f"Created {rel}\nEdit it (keywords, optional summary), then run:\n  python cv/build.py {rel}")


def main(args):
    flags = {a for a in args if a.startswith("--")}
    args = [a for a in args if not a.startswith("--")]
    if flags - {"--public", "--json"}:
        sys.exit(f"Unknown option: {', '.join(flags - {'--public', '--json'})}")
    if flags:
        if args:
            sys.exit("--public and --json always build every role; don't pass role names")
        if "--json" in flags:
            export_json()
        if "--public" in flags:
            for role in role_names():
                build(role, PUBLIC_OUT, public=True)
    elif not args:
        for role in role_names():
            build(role, CAREER / "output" / "general")
    elif args[0] == "new":
        if len(args) != 4:
            sys.exit('Usage: python cv/build.py new <Company> "<Position>" <role>')
        new_application(*args[1:])
    elif args[0].endswith(".md"):
        build_application(args[0])
    else:
        for role in args:
            build(role, CAREER / "output" / "general")


if __name__ == "__main__":
    main(sys.argv[1:])
