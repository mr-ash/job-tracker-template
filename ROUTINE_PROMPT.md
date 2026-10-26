# Daily job-search routine for Claude

This is a ready-made prompt for a scheduled Claude Code task (Anthropic calls these "routines" or
"scheduled tasks"). Once a day Claude opens your repo, looks for new jobs, makes a tailored CV for each,
adds them to the tracker and pushes, and your site updates by itself.

## Setting it up (once)

1. You need a Claude plan that includes Claude Code on the web (Pro, Max, Team or Enterprise), with
   your GitHub account connected to it.
2. Go to **claude.ai/code**, open the scheduled tasks / routines page (or type `/schedule` in Claude
   Code) and create a new one.
3. **Repository:** pick your job-tracker repo.
4. **Schedule:** daily, at a time that suits you.
5. **Environment:**
   - **Network access:** set it to **Full** (or Custom, adding the job sites you use). The default
     "trusted" list blocks most job boards, so Claude wouldn't be able to read postings.
   - **Setup script** (so Claude can build PDF CVs):
     ```bash
     sudo apt-get update && sudo apt-get install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended poppler-utils
     ```
6. **Pushing:** by default Claude pushes to a branch starting with `claude/`, which your site doesn't
   publish. The prompt below tells it to push to `main` instead. If GitHub blocks that (for example a
   branch-protection rule on `main`), either allow it in the repo settings or merge Claude's branch
   yourself each day.
7. Paste the prompt below, after replacing the four `[...]` placeholders. Run it once by hand and check
   the result before leaving it on a schedule.

## The prompt (copy everything in the box)

```text
You maintain my job tracker in this repository. Read ADDING_JOBS.md first and follow it exactly.

Each run, find NEW job openings posted in roughly the last 7 days that match:
- Target roles: [TARGET ROLES]          (e.g. Product Designer, UX Designer, UI Designer)
- Locations: [LOCATIONS]                (e.g. London, or Remote within the UK)
- Seniority: [SENIORITY]                (e.g. junior to mid-level, or internships)
- Exclude: [EXCLUSIONS]                 (e.g. unpaid roles, gambling companies, roles needing 5+ years)

Where to look: company careers pages, LinkedIn job posts, Indeed and other well-known job boards.
Prefer the employer's own posting URL when you can find it. Only include jobs whose posting you have
actually opened and read. Aim for quality over quantity: about 3 to 10 good matches a day is plenty.
If you find nothing new and suitable, change nothing and say so.

For each job:
1. Skip it if jobs.json already has the same id or the same url (also skip near-identical reposts of
   a job already listed).
2. Build a job entry as described in ADDING_JOBS.md, including: title, company, location, contractType,
   salary (only if the posting lists it, otherwise null), url (the posting link), postedDate and
   closingDate (only if shown, otherwise null; never guess), addedDate (today, YYYY-MM-DD),
   status "new", cv "Base CV", a one-line note on why it fits, and contact only if the posting itself
   names a recruiter.
3. Make a tailored CV: write cvs/tailored/<id>.json and run
   python3 tailor_tex.py cvs/tailored/<id>.json
   Tailoring rules, no exceptions: only reorder, emphasise and reword what is already in
   cvs/base/base-cv.tex. Never invent or add experience, employers, tools, skills, qualifications,
   dates, numbers or metrics. Do not use --allow-new-terms, allowTerms or allowSkills. If the script
   rejects an edit, make the edit closer to the original wording instead of forcing it through.
   Set "tailoredCv": "cvs/tailored/<id>.pdf" on the job. Look at the PDF
   (pdftoppm -r 60 -png -f 1 -l 1 ...) to check it isn't broken.
4. Put all new jobs in one JSON array in /tmp/new_jobs.json and run
   python3 add_jobs.py /tmp/new_jobs.json

Then commit and push straight to main (not to a new branch), so the website redeploys:
   git add jobs.json cvs/tailored
   git commit -m "Add jobs YYYY-MM-DD"
   git push origin HEAD:main
If the push to main is rejected, push to a branch instead and say so clearly in your summary.

Never edit cvs/base/, config.js, index.html or the scripts. Never put personal details in notes.
Finish with a short summary: how many jobs you added (title @ company, one line each), how many you
skipped as duplicates, and anything that went wrong.
```

## Tips

- Want fewer, better jobs? Make `[EXCLUSIONS]` and `[SENIORITY]` more specific.
- If a run adds a job you don't want, delete its entry from `jobs.json` (and its two files in
  `cvs/tailored/`). Deleted jobs may come back if they're still posted; add the company or role to
  `[EXCLUSIONS]` to stop that.
- Claude can make mistakes. Always read a tailored CV before you send it.
