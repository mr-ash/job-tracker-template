#!/usr/bin/env python3
"""Append new jobs to jobs.json, skipping any whose id or url already exists.

Usage: python3 add_jobs.py new_jobs.json
new_jobs.json must contain a JSON array of job objects (same fields as jobs.json).

Optional field `contact`: {"name", "title", "url" or "email"} or null (the default).
Only fill it when the job posting itself publicly names a recruiter or contact
person. Never guess, and never take people from LinkedIn or anywhere else.

Optional field `tailoredCv`: relative path to the job's tailored CV PDF, e.g.
"cvs/tailored/<id>.pdf" (made with tailor_tex.py), or null (the default).
The file must already exist in the repo.

Optional field `status`: a short word for where this job is, default "new".
The page shows it as a badge unless it is "new". Your Applied ticks in the
browser are separate and never change this file.
"""
import json
import os
import re
import sys

REQUIRED = ["id", "title", "company", "location", "contractType", "salary",
            "postedDate", "closingDate", "url", "cv", "note", "addedDate"]
OPTIONAL = {"contact": None, "tailoredCv": None, "status": "new"}
CONTACT_KEYS = {"name", "title", "url", "email"}
HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.path.join(HERE, "jobs.json")


def check_contact(job):
    c = job.get("contact")
    if c is None:
        return None
    jid = job.get("id", "?")
    if not isinstance(c, dict):
        sys.exit(f"Job {jid}: contact must be an object or null")
    extra = set(c) - CONTACT_KEYS
    if extra:
        sys.exit(f"Job {jid}: unknown contact fields: {', '.join(sorted(extra))}")
    if not str(c.get("name", "")).strip():
        sys.exit(f"Job {jid}: contact needs a name (or set contact to null)")
    if not (c.get("url") or c.get("email")):
        sys.exit(f"Job {jid}: contact needs a url or an email from the posting")
    if c.get("url") and not str(c["url"]).startswith(("https://", "http://")):
        sys.exit(f"Job {jid}: contact url must start with http(s)://")
    return {k: c[k] for k in ("name", "title", "url", "email") if c.get(k)}


def check_tailored_cv(job):
    p = job.get("tailoredCv")
    if p is None:
        return None
    jid = job.get("id", "?")
    if not isinstance(p, str) or not re.fullmatch(r"cvs/tailored/[a-z0-9][a-z0-9._-]*\.pdf", p):
        sys.exit(f"Job {jid}: tailoredCv must look like cvs/tailored/<id>.pdf (or be null)")
    if not os.path.isfile(os.path.join(HERE, p)):
        sys.exit(f"Job {jid}: tailoredCv file not found: {p} (run tailor_tex.py first)")
    return p


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 add_jobs.py new_jobs.json")
    with open(JOBS, encoding="utf-8") as f:
        jobs = json.load(f)
    with open(sys.argv[1], encoding="utf-8") as f:
        new = json.load(f)
    if not isinstance(new, list):
        sys.exit("Input must be a JSON array of job objects")

    ids = {j["id"] for j in jobs}
    urls = {j["url"] for j in jobs}
    added, skipped = 0, 0
    for job in new:
        missing = [k for k in REQUIRED if k not in job]
        if missing:
            sys.exit(f"Job {job.get('id', '?')} is missing fields: {', '.join(missing)}")
        if job["id"] in ids or job["url"] in urls:
            skipped += 1
            continue
        entry = {k: job[k] for k in REQUIRED}
        for k, default in OPTIONAL.items():
            entry[k] = job.get(k, default)
        entry["contact"] = check_contact(job)
        entry["tailoredCv"] = check_tailored_cv(job)
        entry["status"] = str(entry["status"] or "new").strip()[:30] or "new"
        jobs.append(entry)
        ids.add(job["id"])
        urls.add(job["url"])
        added += 1

    with open(JOBS, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Added {added} job(s), skipped {skipped} duplicate(s). Total now {len(jobs)}.")


if __name__ == "__main__":
    main()
