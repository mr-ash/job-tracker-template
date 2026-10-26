# Adding jobs (how-to for you or an AI agent)

The page (`index.html`) reads `jobs.json` every time it opens. Adding jobs means adding entries to
`jobs.json` (with `add_jobs.py`), making a tailored CV for each one (with `tailor_tex.py`), then
committing and pushing. Your host (Cloudflare Pages or GitHub Pages) redeploys every push to `main`
on its own. Run every command from the repo root.

## The job entry

```json
{
  "id": "company-title-location",
  "title": "Job title",
  "company": "Company",
  "location": "Remote",
  "contractType": "Full-time",
  "salary": "£40k–£50k",
  "postedDate": "2026-10-20",
  "closingDate": "2026-11-22",
  "url": "https://...",
  "cv": "Base CV",
  "note": "Short reason it fits",
  "contact": null,
  "addedDate": "2026-10-26",
  "tailoredCv": "cvs/tailored/company-title-location.pdf",
  "status": "new"
}
```

- `id`: a stable lowercase slug, `company-title-location`. Never change it once it's published, because
  Applied ticks are saved against the id.
- `salary`, `postedDate`, `closingDate`: use `null` when the posting doesn't show them. Never guess.
- `addedDate`: the day the job was added (YYYY-MM-DD). The page groups jobs by this, newest first.
- `location`: free text. The location chips in `config.js` match words in it (e.g. "Remote").
- `company`: for recruitment-agency posts that don't name the employer, write the agency name followed
  by `(recruiter)`, e.g. `"Acme Recruiting (recruiter)"`.
- `cv`: the base CV `name` exactly as in `config.js` (`"Base CV"` by default).
- `contact` (optional, default `null`): only when the posting itself names a recruiter or hiring
  contact: `{"name": "...", "title": "...", "url": "..."}` (or `"email"` instead of `"url"`). Never
  guess, and never look people up elsewhere.
- `tailoredCv` (optional, default `null`): `cvs/tailored/<id>.pdf`. `add_jobs.py` refuses the job if
  the file doesn't exist yet, so make the CV first.
- `status` (optional, default `"new"`): a short word. Anything other than `new` shows as a badge on
  the card (e.g. `"interview"`). The Applied tick on the page is separate and is stored in the browser.

## Tailored CVs (`tailor_tex.py`)

The base CV is `cvs/base/base-cv.tex` (LaTeX, Jake's Resume template), built to `base-cv.pdf`.

Honesty rules, always:
- Only reword, reorder or emphasise what is already in the base CV. Use the posting's keywords only
  where the CV genuinely supports them.
- Never invent experience, tools, employers, qualifications, dates or metrics.
- Keep it the same length. The script refuses a PDF with a different page count from the base.

Write a spec file `cvs/tailored/<id>.json` (see the example one in that folder):

```json
{
  "jobId": "company-title-location",
  "title": "Job title",
  "company": "Company",
  "baseCv": "base-cv",
  "source": "posting",
  "sourceUrl": "https://...",
  "keywords": ["design systems", "prototyping"],
  "edits": [{"from": "exact \\resumeItem text from the .tex", "to": "reworded plain text"}],
  "reorder": [["item C", "item A", "item B"]],
  "skills": [{"label": "Tools", "items": ["Figma", "Framer"]}],
  "honesty": "Reworded and reordered base CV content only."
}
```

- `edits`: `from` is the text inside one `\resumeItem{...}` (as written in the .tex with `\&`, or as
  plain text with `&`). `to` is plain text, no LaTeX commands; the script escapes `& % $ # _` itself.
- `reorder`: each group is the full text of bullets from one job or project, in the new order.
- `skills`: reorder or trim one skills line (`Tools`, `Design`, `Programming`, ...). Items must already
  be in the base CV.
- If the posting can't be opened, use a reliable copy and set `"source": "mirror"` plus `sourceUrl`.
  With no description at all, tailor from the title only and set `"source": "title-only"`.
- The script rejects new numbers, acronyms, CamelCase names and capitalised words (tools, employers,
  products) that aren't in the base CV. Only use `--allow-new-terms` (or the spec's `allowTerms` /
  `allowSkills`) after checking the fact really is in the person's background, and say where it came
  from in `honesty`.
- More layout options (adding/removing bullets, section order, extra header links) are described at
  the top of `tailor_tex.py`.
- To list the bullets you can use: `grep -o '\\resumeItem{.*}' cvs/base/base-cv.tex`

Tools needed (once per machine):
`sudo apt-get install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended poppler-utils`

## Daily steps

1. `git pull`
2. Write the new jobs as a JSON array to a scratch file outside the repo (e.g. `/tmp/new_jobs.json`),
   with `"cv": "Base CV"` and `"tailoredCv": "cvs/tailored/<id>.pdf"` on each.
3. For each job, write `cvs/tailored/<id>.json`, then build it:
   `python3 tailor_tex.py cvs/tailored/<id>.json`
   Check it looks right: `pdftoppm -r 60 -png -f 1 -l 1 cvs/tailored/<id>.pdf /tmp/check` and open
   `/tmp/check-1.png`.
4. Add the jobs (duplicates by `id` or `url` are skipped automatically):
   `python3 add_jobs.py /tmp/new_jobs.json`
5. Commit and push to `main`:
   `git add jobs.json cvs/tailored && git commit -m "Add jobs YYYY-MM-DD" && git push origin HEAD:main`
6. The host redeploys in a minute or two.

## Changing the base CV

Edit `cvs/base/base-cv.tex`, then run `python3 tailor_tex.py --render-base` to rebuild
`cvs/base/base-cv.pdf`. Old tailored CVs stay as they were; rebuild them by re-running their specs if
you like (a spec fails if a bullet it quotes no longer exists, so update the spec first).
