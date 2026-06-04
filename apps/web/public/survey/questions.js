// Survey questions for the maritime AI-agent research study.
//
// This instrument is grounded in UTAUT2 (Venkatesh, Thong & Xu 2012). The core
// of the model is a set of REFLECTIVE constructs, each measured by three items
// on a 7-point "strongly disagree to strongly agree" Likert scale:
//
//   PE  Performance Expectancy   (perceived benefit)
//   EE  Effort Expectancy        (perceived ease of use)
//   TR  Trust                    (AI-specific extension)
//   SI  Social Influence
//   FC  Facilitating Conditions
//   BI  Behavioral Intention     (the dependent variable)
//
// The UTAUT2 consumer constructs (Hedonic Motivation, Price Value, Habit) are
// intentionally omitted: they fit an emerging, organizational, not-yet-adopted
// technology poorly (floor effects, no personal monetary cost). Age, gender,
// experience and seniority are collected as moderators.
//
// Two non-UTAUT2 batteries are kept as antecedent / covariate variables, NOT as
// reflective acceptance scales: the objective knowledge checks (an AI-literacy
// covariate) and the capability ratings (a perceived-capability index). They
// also keep the survey varied and engaging.
//
// Question `type` drives the renderer (survey.js):
//   "single"  one choice            (radio pills)
//   "multi"   several choices       (checkbox pills)
//   "likert"  7-point agree scale   (numbered scale, stored 1-7)
//   "text"    free-form answer      (textarea)

const SURVEY = {
  intro: {
    eyebrow: "Research survey",
    title: "AI agents at work in maritime shipping",
    body:
      "An academic study on how maritime professionals see and adopt AI agents. " +
      "Around 35 quick questions, about nine minutes. Your answers are anonymous " +
      "and feed a research project at the American College of Greece AI Lab.",
  },

  sections: [
    {
      title: "About you",
      eyebrow: "Section 1",
      questions: [
        {
          id: "department",
          type: "single",
          question:
            "Which department best describes the work you do in the maritime shipping industry?",
          answer: [
            "Chartering",
            "Operations and port calls",
            "Post-fixture, laytime and demurrage",
            "Commercial, sale and purchase",
            "Technical and maintenance",
            "Crewing",
            "Compliance, safety and quality (HSEQ)",
            "Legal, insurance and claims",
            "Finance, accounting and invoicing",
            "Procurement and supply",
            "IT and digital",
            "Strategy and management",
          ],
        },
        {
          id: "seniority",
          type: "single",
          question: "Which best describes your role level?",
          answer: [
            "Board or C-level",
            "Senior management",
            "Middle management",
            "Specialist or professional",
            "Junior or entry-level",
            "Support or administrative",
          ],
        },
        {
          id: "experience_years",
          type: "single",
          question: "How long have you worked in the maritime industry?",
          answer: [
            "Less than 2 years",
            "2 to 5 years",
            "6 to 10 years",
            "11 to 20 years",
            "More than 20 years",
          ],
        },
        {
          id: "region",
          type: "single",
          question: "Which region are you mainly based in?",
          answer: [
            "Europe",
            "Middle East and Africa",
            "East Asia (incl. China, Japan, Korea)",
            "South and Southeast Asia (incl. India, Singapore)",
            "North America",
            "Latin America",
            "Oceania",
            "Prefer not to say",
          ],
        },
        {
          id: "age_band",
          type: "single",
          question: "What is your age?",
          answer: ["Under 25", "25 to 34", "35 to 44", "45 to 54", "55 or older", "Prefer not to say"],
        },
        {
          id: "gender",
          type: "single",
          question: "What is your gender?",
          answer: ["Female", "Male", "Another term", "Prefer not to say"],
        },
      ],
    },

    {
      title: "Your experience with AI agents",
      eyebrow: "Section 2",
      note:
        "Where you stand with AI agents today. Tell us how much you agree with each " +
        "statement, from strongly disagree to strongly agree.",
      questions: [
        // Use Behavior - current use (reflective)
        {
          id: "ub1",
          type: "likert",
          question: "I currently use AI agents in my work.",
        },
        {
          id: "ub2",
          type: "likert",
          question: "Using AI agents has become part of how I work.",
        },
        {
          id: "ub3",
          type: "likert",
          question: "I regularly rely on AI agents to get work tasks done.",
        },
        // AI Familiarity (self-assessed) - reflective covariate
        {
          id: "fam1",
          type: "likert",
          question: "I have a clear understanding of what AI agents can and cannot do.",
        },
        {
          id: "fam2",
          type: "likert",
          question: "I could confidently explain how an AI agent differs from a simple chatbot.",
        },
        {
          id: "fam3",
          type: "likert",
          question: "I understand the limitations of AI agents.",
        },
      ],
    },

    {
      title: "What AI agents can do in your work",
      eyebrow: "Section 3",
      note:
        "For each statement, assume the agent has access to the relevant information " +
        "and systems, then tell us how much you agree, from strongly disagree to " +
        "strongly agree.",
      questions: [
        // Perceived Capability - reflective antecedent
        {
          id: "cap_drafting",
          type: "likert",
          question:
            "An AI agent could draft a complex document that cross-references several sources, with a person reviewing.",
        },
        {
          id: "cap_find_fix_errors",
          type: "likert",
          question:
            "An AI agent could review a long document, find factual mistakes, and correct them.",
        },
        {
          id: "cap_customer_support",
          type: "likert",
          question:
            "An AI agent could handle a routine customer or support request from start to finish.",
        },
        {
          id: "cap_audio",
          type: "likert",
          question:
            "An AI agent could listen to a recorded call and produce an accurate summary with action points.",
        },
        {
          id: "cap_video",
          type: "likert",
          question:
            "An AI agent could watch a video, such as an inspection recording, and flag anything unusual.",
        },
        {
          id: "cap_high_stakes",
          type: "likert",
          question: "An AI agent could be trusted to make a high-stakes operational decision on its own.",
        },
      ],
    },

    {
      title: "How you see AI agents in your work",
      eyebrow: "Section 4",
      note:
        "For each statement, tell us how much you agree, from strongly disagree to " +
        "strongly agree. There are no right answers, only your honest view.",
      questions: [
        // Performance Expectancy
        {
          id: "pe1",
          type: "likert",
          question: "Using AI agents would help me complete my work tasks more quickly.",
        },
        {
          id: "pe2",
          type: "likert",
          question: "Using AI agents would improve the quality of my work.",
        },
        {
          id: "pe3",
          type: "likert",
          question: "Overall, AI agents would be useful in my day-to-day work.",
        },
        // Effort Expectancy
        {
          id: "ee1",
          type: "likert",
          question: "Learning to work with AI agents would be easy for me.",
        },
        {
          id: "ee2",
          type: "likert",
          question: "I would find it easy to get an AI agent to do what I want.",
        },
        {
          id: "ee3",
          type: "likert",
          question: "I could become skilful at working with AI agents.",
        },
        // Trust (AI-specific extension)
        {
          id: "tr1",
          type: "likert",
          question:
            "I would trust an AI agent's output enough to act on it after a quick review.",
        },
        {
          id: "tr2",
          type: "likert",
          question: "AI agents are generally reliable for professional work.",
        },
        {
          id: "tr3",
          type: "likert",
          question:
            "I would be comfortable that an AI agent keeps my work data secure and confidential.",
        },
        // Social Influence
        {
          id: "si1",
          type: "likert",
          question: "People whose opinion I value would support my using AI agents at work.",
        },
        {
          id: "si2",
          type: "likert",
          question:
            "Clients and colleagues increasingly expect work in my field to involve AI agents.",
        },
        {
          id: "si3",
          type: "likert",
          question: "Leaders in my organisation encourage using AI agents.",
        },
        // Facilitating Conditions
        {
          id: "fc1",
          type: "likert",
          question: "My organisation has the resources needed to adopt AI agents.",
        },
        {
          id: "fc2",
          type: "likert",
          question: "I have the knowledge needed to start using AI agents in my work.",
        },
        {
          id: "fc3",
          type: "likert",
          question: "Support would be available to me if I had trouble using an AI agent.",
        },
        // Behavioral Intention (dependent variable)
        {
          id: "bi1",
          type: "likert",
          question: "I intend to use AI agents in my work over the next 12 months.",
        },
        {
          id: "bi2",
          type: "likert",
          question: "I expect my use of AI agents at work to increase.",
        },
        {
          id: "bi3",
          type: "likert",
          question: "I would recommend adopting AI agents to my team.",
        },
      ],
    },
  ],
};

// The 7-point Likert anchors, used by the renderer for the acceptance section.
// Stored values are the numbers 1 (strongly disagree) to 7 (strongly agree).
const LIKERT_ANCHORS = [
  "Strongly disagree",
  "Disagree",
  "Somewhat disagree",
  "Neutral",
  "Somewhat agree",
  "Agree",
  "Strongly agree",
];
