// ---------------------------------------------------------------------------
// Your settings. This is the only file you need to edit to make the tracker yours.
// Keep the quotes and commas exactly as they are; just change the text inside.
// ---------------------------------------------------------------------------
window.JOB_TRACKER_CONFIG = {
  // Shown in the top bar and the browser tab.
  title: "My Job Tracker",

  // Used in the file names of downloaded CVs, e.g. "Your Name CV - Acme Designer.pdf".
  yourName: "Your Name",

  // Added to LinkedIn "Find people" / "Recruiters" searches, e.g. "United Kingdom", "Germany", "Canada".
  country: "Your Country",

  // Location filter chips. A job goes under the first chip whose "match" words appear in its
  // "location" text (not case-sensitive). Everything else goes under otherLocationLabel.
  locations: [
    { label: "Your City", match: ["your city"] },
    { label: "Remote",    match: ["remote"] }
  ],
  otherLocationLabel: "Other",

  // One or two sentences about you, used in the "Copy referral message" text.
  // Only say things that are true and on your CV.
  pitch: "I'm a [your role] with [one or two real highlights from your CV].",

  // Your base CVs. "slug" must match a file in cvs/base/ (cvs/base/<slug>.tex and .pdf).
  // A job's "cv" field must be the "name" here; the page turns it into the slug.
  resumes: [
    { slug: "base-cv", name: "Base CV", desc: "My main CV. Every tailored CV starts from this one." }
  ],

  // Date style, e.g. "en-GB" (26 Oct 2026) or "en-US" (Oct 26, 2026). Leave empty for the browser default.
  dateLocale: "en-GB",

  // Prefix for the browser storage that remembers your Applied ticks. Change it only if you host
  // two trackers on the same website address.
  storageKey: "jobTracker"
};
