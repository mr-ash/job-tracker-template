#!/usr/bin/env python3
"""Make a job-specific CV PDF from your LaTeX base CV, without inventing anything.

The rule: a tailored CV may only reorder, emphasise and reword what is already in the
base CV. It never adds experience, tools, employers, dates or metrics. The guardrails
below enforce as much of that as a script can; the rest is up to whoever writes the spec.

Usage (from the repo root, where this file lives):
  python3 tailor_tex.py cvs/tailored/<job-id>.json   -> cvs/tailored/<job-id>.pdf
  python3 tailor_tex.py --render-base [base-cv]      -> cvs/base/<name>.pdf from its .tex

Spec (cvs/tailored/<job-id>.json):
  {
    "jobId": "<id in jobs.json>", "title": "...", "company": "...",
    "baseCv": "base-cv",                              # cvs/base/<baseCv>.tex (default base-cv)
    "source": "posting", "sourceUrl": "https://...", "keywords": ["..."],
    "edits":   [{"from": "<exact \\resumeItem text>", "to": "<reworded plain text>"}],
    "reorder": [["<item text>", "<item text>", ...]],  # new order, items from ONE list
    "skills":  [{"label": "Tools", "items": ["Figma", "Rive", ...]}],  # reorder/trim a line
    "pdfTitle": "Your Name CV - <Company> <Role>",     # optional; default uses the CV heading name
    "honesty": "Reworded and reordered base CV content only."
  }

Optional layout keys (all off unless present, so existing specs render as before):
    "addItems":     [{"after": "<item text>", "text": "<new plain text>"}],  # or "before"; anchor is
                                                      # matched after edits; text is term-checked
    "removeItems":  ["<item text>"],                  # drop a bullet
    "removeRows":   ["<first field of a \\resumeSubheading>"],  # e.g. a school row
    "sectionOrder": ["Experience", "Projects", "Skills", "Education"],  # every \\section, once
    "headerLinks":  [{"label": "Motion design", "url": "https://..."}],  # appended to the contact line
    "removeSkillsLines": ["Platforms"],
    "allowSkills":  ["Brand Identity"],               # skills you verified, beyond the base lines
    "allowTerms":   ["Webflow"],                      # per-spec version of --allow-new-terms

"from" may be the TeX source text (with \\&) or the plain text (with &); "to" is plain
text and is LaTeX-escaped here, so write & % $ # _ normally. Guardrails (all fatal):
  * every "from" must match exactly one \\resumeItem in the base;
  * "to" may not add numbers, acronyms, CamelCase names or capitalised words (tools,
    employers, products) that do not already appear in the base CV;
  * skills lines may only be reordered or trimmed, never given items the base lacks;
  * the PDF must have the same page count as the base PDF.
--allow-new-terms skips only the term check, for terms you verified are genuinely yours.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(HERE, "cvs", "base")
OUT_DIR = os.path.join(HERE, "cvs", "tailored")
SPECIALS = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(s):
    return "".join(SPECIALS.get(c, c) for c in s)


def unesc(s):
    s = s.replace(r"\textbackslash{}", "\\").replace(r"\textasciitilde{}", "~").replace(r"\textasciicircum{}", "^")
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)
    return s.replace("---", "\u2014").replace("--", "\u2013")


def norm(s):
    return re.sub(r"\s+", " ", unesc(s)).strip()


def braced(tex, i):
    """tex[i] == '{'; return index just past the matching '}'."""
    depth = 0
    j = i
    while j < len(tex):
        c = tex[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise SystemExit("Unbalanced braces in base CV")


def body_start(tex):
    return tex.index(r"\begin{document}")


def items(tex):
    """[(start, end, inner_start, inner_end, list_no)] for every \\resumeItem{...} in the body."""
    out, list_no = [], 0
    pos = body_start(tex)
    pat = re.compile(r"\\resumeItemListStart|\\resumeItem\{|^\s*%.*$", re.M)
    for m in pat.finditer(tex, pos):
        if m.group(0).lstrip().startswith("%"):
            continue
        if m.group(0) == r"\resumeItemListStart":
            list_no += 1
            continue
        b = m.end() - 1
        e = braced(tex, b)
        out.append((m.start(), e, b + 1, e - 1, list_no))
    return out


def skills_lines(tex):
    """{label: (start, end, [items])} for lines like \\textbf{Tools}{: a, b, c}."""
    out = {}
    for m in re.finditer(r"\\textbf\{([^{}]+)\}\{:", tex[body_start(tex):]):
        s = body_start(tex) + m.start()
        b = body_start(tex) + m.end() - 2
        e = braced(tex, b)
        inner = tex[b + 2:e - 1]
        out[unesc(m.group(1)).strip()] = (b, e, [x.strip() for x in inner.split(",") if x.strip()])
    return out


def plain_text(tex):
    body = tex[body_start(tex):]
    body = re.sub(r"(?m)^\s*%.*$", "", body)
    body = re.sub(r"\\href\{[^{}]*\}", "", body)
    body = re.sub(r"\\[a-zA-Z]+\*?", " ", body)
    return unesc(re.sub(r"[{}$|]", " ", body))


TERM_RE = re.compile(r"\b(?:[A-Z][A-Za-z]*[A-Z][A-Za-z/]*|[A-Z]{2,}|\d[\d.,/:%+]*)")


def check_terms(base_plain, new_text, where, allow):
    base_words = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z.+-]*[A-Za-z+]|[A-Za-z]", base_plain)}
    base_terms = {m.group(0) for m in TERM_RE.finditer(base_plain)}
    bad = set()
    for m in TERM_RE.finditer(new_text):
        t = m.group(0).rstrip(".,:%")
        if t in base_terms or m.group(0) in base_terms:
            continue
        if not all(p.lower() in base_words or p in base_terms for p in t.split("/") if p):
            bad.add(t)
    # Capitalised words after the first word: tool, product or employer names.
    words = re.findall(r"[A-Za-z][A-Za-z.+-]*[A-Za-z+]|[A-Za-z]", new_text)
    for i, w in enumerate(words):
        if i and w[0].isupper() and w.lower() not in base_words:
            bad.add(w)
    if bad and not allow:
        raise SystemExit(f"Honesty guard: {where} introduces terms not in the base CV: {', '.join(sorted(bad))}\n"
                         "Remove them, or re-run with --allow-new-terms if you verified they are genuinely yours.")
    return sorted(bad)


def cv_name(tex):
    """The name in the CV heading, e.g. \\textbf{\\Huge \\scshape Your Name}, for PDF metadata."""
    m = re.search(r"\\scshape\s+([^{}\\]+?)\s*\}", tex[body_start(tex):])
    return unesc(m.group(1)).strip() if m else "CV"


def find_item(tex, text, used):
    want = norm(text)
    hits = [it for it in items(tex) if norm(tex[it[2]:it[3]]) == want and it[0] not in used]
    if len(hits) != 1:
        raise SystemExit(f"Base CV has {len(hits)} \\resumeItem matching: {text[:90]!r}")
    return hits[0]


def ensure_tools():
    for tool in ("pdflatex", "pdfinfo"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found. Install: sudo apt-get install -y texlive-latex-base "
                             "texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended poppler-utils")


def compile_pdf(tex_src, out_pdf):
    ensure_tools()
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "cv.tex")
        open(src, "w", encoding="utf-8").write(tex_src)
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "cv.tex"],
                           cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.isfile(os.path.join(tmp, "cv.pdf")):
            log = open(os.path.join(tmp, "cv.log"), encoding="utf-8", errors="replace").read()
            err = "\n".join(l for l in log.splitlines() if l.startswith("!"))[:1500]
            raise SystemExit(f"pdflatex failed:\n{err or r.stdout[-1500:]}")
        shutil.copyfile(os.path.join(tmp, "cv.pdf"), out_pdf)
    return pages(out_pdf)


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))


def base_paths(name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name or ""):
        raise SystemExit("baseCv must be a slug like base-cv")
    tex = os.path.join(BASE_DIR, name + ".tex")
    if not os.path.isfile(tex):
        raise SystemExit(f"Base CV not found: {os.path.relpath(tex, HERE)}")
    return tex, os.path.join(BASE_DIR, name + ".pdf")


def render_base(name):
    tex, pdf = base_paths(name)
    n = compile_pdf(open(tex, encoding="utf-8").read(), pdf)
    print(f"{os.path.relpath(pdf, HERE)}: {n} page(s)")


def tailor(spec_path, allow_new_terms=False):
    spec = json.load(open(spec_path, encoding="utf-8"))
    job_id = spec.get("jobId", "")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", job_id):
        raise SystemExit("Spec needs a jobId slug (lowercase letters, digits, . _ -)")
    base_tex, base_pdf = base_paths(spec.setdefault("baseCv", "base-cv"))
    tex = open(base_tex, encoding="utf-8").read()
    base_plain = plain_text(tex)
    if not os.path.isfile(base_pdf) or os.path.getmtime(base_pdf) < os.path.getmtime(base_tex):
        render_base(spec["baseCv"])
    base_pages = pages(base_pdf)
    flagged = []
    added = []

    # 1. Reorder items within one list (positions are swapped, text untouched).
    for group in spec.get("reorder", []):
        used, found = set(), []
        for text in group:
            it = find_item(tex, text, used)
            used.add(it[0])
            found.append(it)
        if len({it[4] for it in found}) != 1:
            raise SystemExit("A reorder group mixes items from different jobs/projects")
        slots = sorted(found, key=lambda it: it[0])
        texts = [tex[it[0]:it[1]] for it in found]
        for slot, new in sorted(zip(slots, texts), key=lambda p: -p[0][0]):
            tex = tex[:slot[0]] + new + tex[slot[1]:]

    # 2. Reword items.
    edits = []
    used = set()
    for e in spec.get("edits", []):
        it = find_item(tex, e["from"], used)
        used.add(it[0])
        to = re.sub(r"\s+", " ", e["to"]).strip()
        if not to:
            raise SystemExit(f"Empty replacement for: {e['from'][:80]!r}")
        bad = [t for t in check_terms(base_plain, to, "", True) if t not in spec.get("allowTerms", [])]
        if bad and not allow_new_terms:
            raise SystemExit(f"Honesty guard: edit of {e['from'][:50]!r} introduces terms not in the base CV: "
                             f"{', '.join(bad)}\nAdd them to allowTerms only if verified.")
        flagged += bad
        edits.append((it, esc(to)))
    for it, new in sorted(edits, key=lambda p: -p[0][2]):
        tex = tex[:it[2]] + new + tex[it[3]:]


    # 2b. Add new bullets next to an existing one (anchor text as it reads after edits).
    allow_terms = set(spec.get("allowTerms", []))
    for a in spec.get("addItems", []):
        text = re.sub(r"\s+", " ", a.get("text", "")).strip()
        anchor = a.get("after") or a.get("before")
        if not text or not anchor:
            raise SystemExit("addItems entries need \"text\" and \"after\" or \"before\"")
        bad = check_terms(base_plain, text, f"new item {text[:50]!r}", True)
        bad = [t for t in bad if t not in allow_terms]
        if bad and not allow_new_terms:
            raise SystemExit(f"Honesty guard: new item {text[:50]!r} introduces terms not in the base CV: "
                             f"{', '.join(bad)}\nAdd them to allowTerms only if verified.")
        flagged += bad
        it = find_item(tex, anchor, set())
        new = "\\resumeItem{" + esc(text) + "}"
        if a.get("after"):
            tex = tex[:it[1]] + "\n          " + new + tex[it[1]:]
        else:
            tex = tex[:it[0]] + new + "\n          " + tex[it[0]:]
        added.append(text)

    # 2c. Remove bullets.
    for text in spec.get("removeItems", []):
        it = find_item(tex, text, set())
        line_start = tex.rfind("\n", 0, it[0]) + 1
        if tex[line_start:it[0]].strip() == "":
            end = it[1] + 1 if tex[it[1]:it[1] + 1] == "\n" else it[1]
            tex = tex[:line_start] + tex[end:]
        else:
            tex = tex[:it[0]] + tex[it[1]:]

    # 2d. Remove whole \resumeSubheading rows (e.g. school rows) by their first field.
    for name in spec.get("removeRows", []):
        hits = []
        for m in re.finditer(r"\\resumeSubheading\b", tex[body_start(tex):]):
            st = body_start(tex) + m.start()
            j, args = st + len(r"\resumeSubheading"), []
            for _ in range(4):
                while tex[j].isspace():
                    j += 1
                if tex[j] != "{":
                    raise SystemExit("Unexpected \\resumeSubheading layout")
                e = braced(tex, j)
                args.append(tex[j + 1:e - 1])
                j = e
            if norm(args[0]) == norm(name):
                hits.append((st, j))
        if len(hits) != 1:
            raise SystemExit(f"Base CV has {len(hits)} \\resumeSubheading rows named {name!r}")
        st, en = hits[0]
        line_start = tex.rfind("\n", 0, st) + 1
        if tex[en:en + 1] == "\n":
            en += 1
        tex = tex[:line_start] + tex[en:]

    # 3. Skills lines: reorder or trim only (plus any skills listed in allowSkills).
    for s in spec.get("skills", []):
        lines = skills_lines(tex)
        label = s.get("label", "")
        if label not in lines:
            raise SystemExit(f"No skills line labelled {label!r} (have: {', '.join(lines)})")
        all_base = {norm(x).lower() for _, _, xs in skills_lines(open(base_tex, encoding='utf-8').read()).values() for x in xs}
        new_items = [re.sub(r"\s+", " ", x).strip() for x in s.get("items", []) if str(x).strip()]
        allowed = {x.lower() for x in spec.get("allowSkills", [])}
        extra = [x for x in new_items if x.lower() not in all_base and x.lower() not in allowed]
        if extra:
            raise SystemExit(f"Honesty guard: skills line {label!r} adds items not in the base CV: {', '.join(extra)}")
        if not new_items:
            raise SystemExit(f"Skills line {label!r} would be empty")
        b, e, _ = lines[label]
        tex = tex[:b] + "{: " + ", ".join(esc(x) for x in new_items) + "}" + tex[e:]


    for label in spec.get("removeSkillsLines", []):
        m = re.search(r"[ \t]*\\textbf\{" + re.escape(esc(label)) + r"\}\{:", tex)
        if not m:
            raise SystemExit(f"No skills line labelled {label!r} to remove")
        e = braced(tex, m.end() - 2)
        tail = re.match(r"[ \t]*(\\\\)?[ \t]*\n?", tex[e:])
        tex = tex[:m.start()] + tex[e + tail.end():]

    # 4. Section order: every \section exactly once, in the order given.
    if spec.get("sectionOrder"):
        start = tex.index(r"\section{", body_start(tex))
        end = tex.index(r"\end{document}")
        starts = [m.start() for m in re.finditer(r"\\section\{", tex[start:end])]
        chunks = {}
        for k, st in enumerate(starts):
            seg = tex[start + st:start + (starts[k + 1] if k + 1 < len(starts) else end - start)]
            seg = re.sub(r"(\s*(%[^\n]*|\\vspace\{[^}]*\}))*\s*$", "", seg)
            name = re.match(r"\\section\{([^}]*)\}", seg).group(1)
            chunks[name] = seg
        order = spec["sectionOrder"]
        if sorted(order) != sorted(chunks):
            raise SystemExit(f"sectionOrder must list each section once: {', '.join(chunks)}")
        tex = tex[:start] + "\n\\vspace{0.1cm}\n\n".join(chunks[n] for n in order) + "\n\n" + tex[end:]

    # 5. Extra links on the contact line.
    if spec.get("headerLinks"):
        i = tex.index(r"\end{center}", body_start(tex))
        line_end = tex.rfind("\n", 0, i)
        links = "".join(f" $|$\n    \\href{{{l['url']}}}{{{esc(l['label'])}}}" for l in spec["headerLinks"])
        if any(re.search(r"[\s{}\\%]", l["url"]) for l in spec["headerLinks"]):
            raise SystemExit("headerLinks urls must be plain URLs")
        tex = tex[:line_end] + links + tex[line_end:]

    author = cv_name(tex)
    title = spec.get("pdfTitle") or f"{author} CV - {spec.get('company', '')} {spec.get('title', '')}".strip()
    tex = tex.replace(r"\begin{document}",
                      "\\hypersetup{pdftitle={%s},pdfauthor={%s}}\n\\begin{document}" % (esc(title), esc(author)), 1)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUT_DIR, job_id + ".pdf")
    tmp_pdf = out_pdf + ".tmp"
    n = compile_pdf(tex, tmp_pdf)
    if n != base_pages:
        os.remove(tmp_pdf)
        raise SystemExit(f"Tailored CV is {n} page(s) but the base is {base_pages}. Shorten the edits.")
    os.replace(tmp_pdf, out_pdf)
    rel = os.path.relpath(out_pdf, HERE)
    print(f"{rel}: {n} page(s), {len(edits)} edit(s), {len(spec.get('reorder', []))} reorder(s), "
          f"{len(spec.get('skills', []))} skills line(s)" + (f", {len(added)} new item(s)" if added else "") + (f"; allowed new terms: {', '.join(flagged)}" if flagged else ""))
    print(f'jobs.json: "tailoredCv": "{rel}"')


def main():
    args = sys.argv[1:]
    allow = "--allow-new-terms" in args
    args = [a for a in args if a != "--allow-new-terms"]
    if args[:1] == ["--render-base"]:
        render_base(args[1] if len(args) > 1 else "base-cv")
    elif len(args) == 1:
        tailor(args[0], allow)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
