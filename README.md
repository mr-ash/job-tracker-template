# Job Tracker

A simple website that shows your job shortlist, one card per job, newest first. On each card you can:

- open the job posting,
- download a CV tailored to that job (made from your own CV, never with made-up facts),
- find people or recruiters at the company on LinkedIn, and copy a ready-written referral message,
- tick **Applied** once you've applied.

It works on your phone and laptop, has light and dark mode, and can be installed like an app
("Add to Home Screen"). There is no server, database or login: it is a handful of files, and the job
list is one file called `jobs.json`. You can add jobs by hand, or let Claude add them every day for
you (see `ROUTINE_PROMPT.md`).

## What's in the folder

| File | What it is |
|---|---|
| `index.html` | The website itself. You don't need to touch it. |
| `config.js` | **Your settings**: name, title, location filters, referral pitch. Edit this. |
| `jobs.json` | The list of jobs. Starts with one example job; delete it when you add real ones. |
| `cvs/base/base-cv.tex` | **Your CV** in LaTeX. Starts as a "Your Name" placeholder; replace it with yours. |
| `cvs/base/base-cv.pdf` | The PDF built from it. |
| `cvs/tailored/` | One tailored CV per job: a small `.json` "what to change" file and the `.pdf`. |
| `tailor_tex.py` | Makes a tailored CV from your base CV and a `.json` file. |
| `add_jobs.py` | Adds jobs to `jobs.json`, skipping duplicates. |
| `ADDING_JOBS.md` | Detailed how-to for adding jobs and tailoring CVs (for you or Claude). |
| `ROUTINE_PROMPT.md` | A prompt to paste into Claude so it finds jobs for you every day. |
| `sw.js`, `manifest.webmanifest`, `icons/` | Make it installable as an app and work offline. |
| `_headers`, `.nojekyll` | Small settings files for Cloudflare Pages and GitHub Pages. |

## Step 1: put it on your own GitHub

You need a free GitHub account.

- **If you received this as a GitHub template:** click **Use this template → Create a new repository**.
- **If you received a zip:** on GitHub click **+ → New repository**, give it a name (e.g. `job-tracker`)
  and create it. On the new repo's page click **uploading an existing file**, drag in everything from
  the unzipped folder (including the `cvs` and `icons` folders), and click **Commit changes**.
  (The files starting with a dot, `.nojekyll` and `.gitignore`, can be hidden on Mac and Windows; they
  are nice to have but not essential.)

**Public or private?** If the repo and site are public, anyone with the link can see your jobs and
your CVs (including the phone number and email on them). The page asks search engines not to list it,
but that isn't a lock. Cloudflare Pages works fine with a private repo; GitHub Pages needs a public repo
unless you pay for GitHub.

## Step 2: put it online

Pick one.

**Cloudflare Pages (free, works with private repos)**
1. Sign in at dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Choose your repo.
3. Build settings: framework preset **None**, build command **empty**, build output directory **`/`**
   (just the root of the repo).
4. **Save and Deploy.** After a minute you get a link like `https://your-project.pages.dev`.
   Every time something is pushed to `main`, it updates by itself.

**GitHub Pages (free, public repos)**
1. In your repo: **Settings → Pages**.
2. Source: **Deploy from a branch**, branch **main**, folder **/ (root)**, **Save**.
3. After a minute or two your site is at `https://<your-username>.github.io/<repo-name>/`.

Open the link on your phone and use **Add to Home Screen** (or the Install button) to get it as an app.

## Step 3: make it yours

1. **Settings:** edit `config.js` on GitHub (click the file, then the pencil icon). Change your name, the
   page title, your country, the location chips and the referral pitch. Keep the quotes and commas.
2. **Your CV:** open `cvs/base/base-cv.tex` and replace the placeholder content with your real CV. It uses
   the popular "Jake's Resume" LaTeX layout. Keep the building blocks the same (`\resumeSubheading`,
   `\resumeItem{...}`, and skills lines like `\textbf{Tools}{: Figma, Framer}`), because the tailoring
   script reads them. One page is best.
   - Then rebuild the PDF: `python3 tailor_tex.py --render-base` (needs LaTeX, see below). If you
     don't have LaTeX, you can paste the `.tex` into Overleaf (free), download the PDF, and upload it
     as `cvs/base/base-cv.pdf`. Or just let the Claude routine do it on its first run: ask it to
     "rebuild the base CV PDF".
3. **Delete the example job:** remove the example entry from `jobs.json` (leave `[]` if it's empty) and
   delete the two `example-company-...` files in `cvs/tailored/`.

## The jobs file

`jobs.json` is a list of jobs, each looking like this:

```json
{
  "id": "acme-product-designer-london",
  "title": "Product Designer",
  "company": "Acme",
  "location": "London (hybrid)",
  "contractType": "Full-time",
  "salary": "£45k–£55k",
  "postedDate": "2026-10-20",
  "closingDate": null,
  "url": "https://acme.example/jobs/123",
  "cv": "Base CV",
  "note": "Design-systems heavy, matches my last role",
  "contact": null,
  "addedDate": "2026-10-26",
  "tailoredCv": "cvs/tailored/acme-product-designer-london.pdf",
  "status": "new"
}
```

- `id` is a short unique name. Don't change it later: your Applied ticks are saved against it.
- Unknown salary or dates are `null` (no quotes).
- `addedDate` decides which day the job appears under.
- `status` is optional; anything other than `new` (e.g. `interview`) shows as a label on the card.

Full details are in `ADDING_JOBS.md`.

**About the Applied tick:** ticks are saved in the browser you tick them in, so your phone and laptop
keep separate ticks. Clearing your browser data clears them too.

## How the tailored CVs work

For each job there's a small file `cvs/tailored/<id>.json` that says what to change, for example: "move
this bullet to the top", "reword this bullet to use the posting's words", "put these skills first". Then

```bash
python3 tailor_tex.py cvs/tailored/<id>.json
```

builds `cvs/tailored/<id>.pdf`. Put that path in the job's `tailoredCv` field, and the card gets a
**Download tailored CV** button.

The one rule: **a tailored CV only reorders, emphasises and rewords what's already in your base CV. It
never invents experience, tools, dates or numbers.** The script helps enforce this: it refuses an edit
that brings in new numbers, acronyms or names that aren't already in your CV, refuses to add skills you
don't list, and refuses a CV that's longer than the original. Still, read a tailored CV before you send it.

The example in `cvs/tailored/` shows a spec and its PDF.

To build CVs on your own computer you need Python 3 and LaTeX:
- Mac: install MacTeX (or BasicTeX) and poppler (`brew install poppler`).
- Windows: easiest inside WSL (Ubuntu), then the Linux command below.
- Linux: `sudo apt-get install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended poppler-utils`

You don't need any of this if you let Claude do it (see below).

## Let Claude add jobs every day

Open `ROUTINE_PROMPT.md`. It explains how to create a daily scheduled task in Claude Code on the web,
and gives you a prompt to paste in with four blanks to fill: the roles, locations and seniority you
want, and what to exclude. Each day Claude finds new jobs, skips ones you already have, makes a
tailored CV for each, adds them to `jobs.json`, and pushes to `main`, so your site updates by itself.

## Trying it on your computer (optional)

In the folder, run `python3 -m http.server 8000` and open http://localhost:8000. (Opening `index.html`
by double-clicking won't load the jobs; it needs to be served like this.)

## Credits

The CV layout is based on Jake Gutierrez's "Jake's Resume" LaTeX template (MIT licence; the
attribution is kept at the top of `base-cv.tex`). The site uses the Onest font from Google Fonts.
