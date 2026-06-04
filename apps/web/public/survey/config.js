// ─────────────────────────────────────────────────────────────────────────
//  SURVEY CONFIG  —  the only file you need to edit to go live.
// ─────────────────────────────────────────────────────────────────────────
//
// This is a fully static site. To collect answers in Google Sheets without a
// server, it posts each submission to a Google Apps Script Web App that is
// bound to your sheet. Setup takes about three minutes; see SETUP.md for the
// step-by-step (it includes the script you paste into Apps Script).
//
// Once you deploy the Apps Script Web App, paste its URL below. That URL is
// the "API key" for this project — nothing else needs to change.

const CONFIG = {
  // Paste your Google Apps Script Web App URL here. It looks like:
  //   https://script.google.com/macros/s/AKfyc.../exec
  ENDPOINT_URL: "https://script.google.com/macros/s/AKfycbzSfhuSSU3YcoyPVELThm2zTp3GPbDPLcz_V-eWp0yZAno9poiA4oudRn0k09Lvs-w/exec",

  // Leave true while you have not deployed yet: submissions are logged to the
  // browser console and the success screen still shows, so you can preview the
  // full flow. Set to false the moment ENDPOINT_URL is live.
  DEMO_MODE: false,

  // Contact address shown on the consent screen for questions about the
  // research. Leave empty to fall back to naming the AI Lab without a link.
  CONTACT_EMAIL: "",
};
