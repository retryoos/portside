// ─────────────────────────────────────────────────────────────────────────
//  survey.js — renders the form from questions.js, validates, and posts each
//  submission to the Google Apps Script Web App named in config.js.
//
//  Pure vanilla JS, no build step. Reads two globals:
//    SURVEY  (questions.js)  — the question set
//    CONFIG  (config.js)     — ENDPOINT_URL + DEMO_MODE
// ─────────────────────────────────────────────────────────────────────────

(function () {
  "use strict";

  const sectionsEl = document.getElementById("sections");
  const form = document.getElementById("surveyForm");
  const submitBtn = document.getElementById("submitBtn");
  const statusEl = document.getElementById("formStatus");
  const doneEl = document.getElementById("done");
  const formWrap = document.getElementById("survey");
  const progressFill = document.getElementById("progressFill");
  const progressCount = document.getElementById("progressCount");

  // Flat list of all questions, in order, for validation + progress.
  const allQuestions = SURVEY.sections.flatMap((s) => s.questions);
  // Questions that count toward "answered" progress (optional ones excluded).
  const requiredQuestions = allQuestions.filter((q) => !q.optional);

  // ── Consent gate ──────────────────────────────────────────────────────────
  // The survey (#survey) starts hidden in the markup; it is revealed only after
  // the visitor ticks the consent box and presses Begin.
  const consentEl = document.getElementById("consent");
  const consentCheck = document.getElementById("consentCheck");
  const beginBtn = document.getElementById("beginBtn");
  const contactEl = document.getElementById("consentContact");

  if (CONFIG.CONTACT_EMAIL) {
    const a = document.createElement("a");
    a.href = "mailto:" + CONFIG.CONTACT_EMAIL;
    a.textContent = CONFIG.CONTACT_EMAIL;
    contactEl.replaceChildren(a);
  }

  consentCheck.addEventListener("change", () => {
    beginBtn.disabled = !consentCheck.checked;
  });

  beginBtn.addEventListener("click", () => {
    if (!consentCheck.checked) return;
    consentEl.hidden = true;
    formWrap.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
    // The reveal sections were laid out while hidden; nudge any now in view.
    revealInView();
  });

  // ── Intro copy ──────────────────────────────────────────────────────────
  document.getElementById("introEyebrow").textContent = SURVEY.intro.eyebrow;
  document.getElementById("introTitle").textContent = SURVEY.intro.title;
  document.getElementById("introBody").textContent = SURVEY.intro.body;

  // ── Render ────────────────────────────────────────────────────────────────
  let qNumber = 0;
  SURVEY.sections.forEach((section) => {
    const sec = el("section", "section reveal");

    const head = el("div", "section__head");
    head.appendChild(el("p", "text-eyebrow eyebrow", section.eyebrow));
    head.appendChild(el("h2", "text-h2", section.title));
    if (section.note) head.appendChild(el("p", "section__note text-body", section.note));
    sec.appendChild(head);

    section.questions.forEach((q) => {
      qNumber += 1;
      sec.appendChild(renderQuestion(q, qNumber));
    });

    sectionsEl.appendChild(sec);
  });

  function renderQuestion(q, num) {
    const card = el("div", "q");
    card.dataset.qid = q.id;

    const prompt = el("div", "q__prompt");
    prompt.appendChild(el("span", "q__num", String(num).padStart(2, "0")));
    const title = el("span", "q__title", q.question);
    if (q.optional) {
      const opt = el("span", "q__optional", "Optional");
      title.appendChild(opt);
    }
    prompt.appendChild(title);
    card.appendChild(prompt);

    if (q.type === "text") {
      const wrap = el("div", "q__text");
      const ta = document.createElement("textarea");
      ta.className = "field";
      ta.name = q.id;
      ta.placeholder = q.placeholder || "Type your answer";
      ta.addEventListener("input", () => {
        clearInvalid(card);
        updateProgress();
      });
      wrap.appendChild(ta);
      card.appendChild(wrap);
    } else if (q.type === "likert") {
      // 7-point agree scale. Radios are named q.id with values 1-7, so the
      // generic single-choice getAnswer() path picks them up unchanged.
      const wrap = el("div", "likert");
      const row = el("div", "likert__scale");
      row.setAttribute("role", "radiogroup");
      for (let k = 1; k <= 7; k++) {
        const label = el("label", "likert__opt");
        const input = document.createElement("input");
        input.type = "radio";
        input.name = q.id;
        input.value = String(k);
        input.id = `${q.id}__${k}`;
        input.setAttribute("aria-label", `${k} of 7, ${LIKERT_ANCHORS[k - 1]}`);
        input.addEventListener("change", () => {
          clearInvalid(card);
          updateProgress();
        });
        label.appendChild(input);
        label.appendChild(el("span", "likert__dot", String(k)));
        row.appendChild(label);
      }
      wrap.appendChild(row);
      const anchors = el("div", "likert__anchors");
      anchors.appendChild(el("span", null, LIKERT_ANCHORS[0]));
      anchors.appendChild(el("span", null, LIKERT_ANCHORS[6]));
      wrap.appendChild(anchors);
      card.appendChild(wrap);
    } else {
      const isMulti = q.type === "multi";
      const opts = el("div", "q__options");
      opts.setAttribute("role", isMulti ? "group" : "radiogroup");

      q.answer.forEach((choice, i) => {
        const id = `${q.id}__${i}`;
        const label = el("label", `opt ${isMulti ? "opt--multi" : "opt--single"}`);

        const input = document.createElement("input");
        input.type = isMulti ? "checkbox" : "radio";
        input.name = q.id;
        input.value = choice;
        input.id = id;

        const isOther = /^other$/i.test(choice);
        input.addEventListener("change", () => {
          clearInvalid(card);
          toggleOther(card, q);
          updateProgress();
        });
        if (isOther) input.dataset.other = "true";

        label.appendChild(input);
        label.appendChild(el("span", "opt__mark"));
        label.appendChild(el("span", "opt__label", choice));
        opts.appendChild(label);
      });
      card.appendChild(opts);

      // Hidden "Other, please specify" text field, revealed on selection.
      if (q.answer.some((c) => /^other$/i.test(c))) {
        const other = el("div", "q__other");
        other.dataset.otherFor = q.id;
        const inp = document.createElement("input");
        inp.type = "text";
        inp.className = "field";
        inp.placeholder = "Please specify";
        inp.dataset.otherText = q.id;
        inp.addEventListener("input", () => clearInvalid(card));
        other.appendChild(inp);
        card.appendChild(other);
      }
    }

    const err = el("p", "q__error", q.optional ? "" : "Please answer this question.");
    card.appendChild(err);

    return card;
  }

  // ── "Other" reveal ────────────────────────────────────────────────────────
  function toggleOther(card, q) {
    const other = card.querySelector(`[data-other-for="${q.id}"]`);
    if (!other) return;
    const otherChecked = !!card.querySelector('input[data-other="true"]:checked');
    other.classList.toggle("show", otherChecked);
    if (otherChecked) {
      const inp = other.querySelector("input");
      if (inp) inp.focus();
    }
  }

  // ── Answer collection ─────────────────────────────────────────────────────
  function getAnswer(q) {
    const card = document.querySelector(`.q[data-qid="${q.id}"]`);
    if (q.type === "text") {
      const ta = card.querySelector("textarea");
      return ta.value.trim();
    }
    if (q.type === "multi") {
      const checked = [...card.querySelectorAll('input[type="checkbox"]:checked')];
      return checked.map((c) => resolveValue(c, card)).filter(Boolean);
    }
    const picked = card.querySelector('input[type="radio"]:checked');
    return picked ? resolveValue(picked, card) : "";
  }

  // For an "Other" selection, substitute the typed text when present.
  function resolveValue(input, card) {
    if (input.dataset.other === "true") {
      const txt = card.querySelector("[data-other-text]");
      const typed = txt && txt.value.trim();
      return typed ? `Other: ${typed}` : "Other";
    }
    return input.value;
  }

  function isAnswered(q) {
    const a = getAnswer(q);
    return Array.isArray(a) ? a.length > 0 : a.length > 0;
  }

  // ── Progress ──────────────────────────────────────────────────────────────
  function updateProgress() {
    const done = requiredQuestions.filter(isAnswered).length;
    const total = requiredQuestions.length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    progressFill.style.width = pct + "%";
    progressCount.textContent = `${done} / ${total}`;
  }

  // ── Validation ────────────────────────────────────────────────────────────
  function clearInvalid(card) {
    card.classList.remove("invalid");
  }

  function validate() {
    let firstInvalid = null;
    requiredQuestions.forEach((q) => {
      const card = document.querySelector(`.q[data-qid="${q.id}"]`);
      const ok = isAnswered(q);
      card.classList.toggle("invalid", !ok);
      if (!ok && !firstInvalid) firstInvalid = card;
    });
    return firstInvalid;
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.classList.remove("error");
    statusEl.textContent = "";

    const firstInvalid = validate();
    if (firstInvalid) {
      statusEl.classList.add("error");
      statusEl.textContent = "Please answer the highlighted questions before submitting.";
      firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    const payload = buildPayload();

    submitBtn.disabled = true;
    statusEl.textContent = "Submitting your answers…";

    try {
      await send(payload);
      showDone();
    } catch (err) {
      console.error("Survey submission failed:", err);
      submitBtn.disabled = false;
      statusEl.classList.add("error");
      statusEl.textContent =
        "Something went wrong submitting your answers. Please try again in a moment.";
    }
  });

  function buildPayload() {
    const responses = {};
    allQuestions.forEach((q) => {
      const a = getAnswer(q);
      responses[q.id] = Array.isArray(a) ? a.join("; ") : a;
    });
    return {
      submittedAt: new Date().toISOString(),
      userAgent: navigator.userAgent,
      responses,
    };
  }

  // Post to the Apps Script Web App. We send as text/plain to dodge a CORS
  // preflight (Apps Script does not answer OPTIONS), and use no-cors so the
  // opaque response still resolves — the script writes the row regardless.
  async function send(payload) {
    if (CONFIG.DEMO_MODE || !CONFIG.ENDPOINT_URL) {
      console.info("[DEMO_MODE] Submission payload (not sent):", payload);
      await wait(700);
      return;
    }
    await fetch(CONFIG.ENDPOINT_URL, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(payload),
    });
  }

  function showDone() {
    formWrap.hidden = true;
    document.getElementById("progress").hidden = true;
    doneEl.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ── Scroll reveal ─────────────────────────────────────────────────────────
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Reveal any .reveal currently within the viewport. Used as a safety net when
  // the survey is unhidden after consent (sections laid out while hidden may not
  // trigger the observer until the next scroll).
  function revealInView() {
    document.querySelectorAll(".reveal:not(.in)").forEach((n) => {
      const r = n.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) n.classList.add("in");
    });
  }

  if (reduce) {
    document.querySelectorAll(".reveal").forEach((n) => n.classList.add("in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
    );
    document.querySelectorAll(".reveal").forEach((n) => io.observe(n));
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }
  function wait(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  updateProgress();
})();
