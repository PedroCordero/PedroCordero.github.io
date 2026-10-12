# pedrocordero.hu

My website (projects + CV) and the source of every CV I send.
Built with [Astro](https://astro.build), published free on GitHub Pages.

**You only edit Markdown in `content/`.** Everything else rebuilds itself.

```
content/
├── cv/
│   ├── master.md        everything I've done: the single source for CV and website
│   ├── roles/           one file per CV type (headline, summary, section order)
│   ├── logos/           optional organisation logos for the home page (see below)
│   └── photo.jpg
├── projects/
│   ├── _template.md     copy this to start a project
│   └── <name>/          one folder per project: index.md + its images
└── pages/
    ├── home.md          home page: tagline + About text
    └── *.md             any other file becomes a page in the menu

cv/                      CV builder (Python)
src/                     website code (Astro)
public/media/            videos (Markdown can't optimize them, so they're served as-is)
scripts/check_private.py privacy check, runs on every commit and every publish
```

## Setup (once per computer)

1. Install [Node.js](https://nodejs.org) 22.12 or newer and Python 3.
2. Clone this repo and the private `career` repo **side by side**:
   ```
   Portfolio/
   ├── site/      this repo
   └── career/    private repo (phone, applications, letters)
   ```
3. In this folder:
   ```
   npm install
   pip install -r cv/requirements.txt
   git config user.email "65003489+PedroCordero@users.noreply.github.com"
   ```
   `npm install` also switches on the privacy check for commits.

## Everyday use

| I want to… | Do this |
|---|---|
| See the site while editing | `npm run dev`, then open http://localhost:4321. It reloads as you type. |
| Add a project | Copy `content/projects/_template.md` to `content/projects/<name>/index.md` and fill it in |
| Hide a project for now | `draft: true` in its front matter |
| Update my CV | Edit `content/cv/master.md` (format notes are at the top of that file) |
| Publish | Commit and push. GitHub rebuilds the site in about 2 minutes. |

Publishing only happens while the repository variable `PUBLISH` is `true`
(`gh variable set PUBLISH --body true`; set it to `false` to pause). Builds and privacy
checks run on every push regardless.

## Home page

The design is adapted from [Starfolio](https://github.com/webrating/starfolio) (MIT, notice in `LICENSES/starfolio.txt`). Each section is filled from Markdown:

| Section | Comes from |
|---|---|
| "Hi, I'm …" + the line under it | first word of `name` in `master.md`, `tagline` in `content/pages/home.md` |
| About | the text of `content/pages/home.md` |
| Work Experience, Education, Skills, Publications, Honours & awards | the sections with those names in `master.md`, as filtered for the website role (`website: true` in `content/cv/roles/`, else the first role) |
| Research & projects | `content/projects/`, featured first, then newest |
| Contact | `email` and the LinkedIn link in `master.md` |

**Logos:** experience and education rows show the organisation's initials. To show a logo instead, save it as
`content/cv/logos/<name>.png` (or .jpg/.webp), where `<name>` is the organisation in lowercase with dashes,
e.g. `european-knowledge-center.png`, `eotvos-lorand-university.png`.

**Colors and fonts:** the `oklch(...)` values in `src/styles/global.css` (`:root` = light, `.dark` = dark).

## CVs

| Command | Result |
|---|---|
| `python cv/build.py` | Every role, **with** phone → `../career/output/general/` |
| `python cv/build.py ai` | One role, with phone |
| `python cv/build.py new Bosch "Robotics Engineer" ai` | New application file in `../career/applications/` |
| `python cv/build.py ../career/applications/2026-10_Bosch.md` | Tailored CV → `../career/output/2026-10_Bosch/`, plus a job-ad keyword check |
| `python cv/build.py --public` | Every role **without** phone → `public/cv/` (offered on the website) |

The website's CV page shows the role marked `website: true` in `content/cv/roles/` (otherwise the first one) and offers every role's public PDF.

PDFs are printed by Microsoft Edge (or Chrome), so no LaTeX or Word is needed.

## Privacy

This repo is public. Private data lives only in `../career`:

- `career/private.yml`: phone and other details added to CVs sent to companies, never to the website.
- `career/private-patterns.txt`: values that must never be public. Every commit is checked against it, and the check reports only the line that matched, never the value.
- The check also blocks phone numbers, photos with GPS location, PDF/Word/zip files, and commits made with an email other than the GitHub noreply address.
- On every publish, GitHub runs the same check on the repo and on the built site, including the text of the public CV PDFs.

Run it by hand with `npm run check:private`.
