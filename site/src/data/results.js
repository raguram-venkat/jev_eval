// Real numbers from one live run against Jev (TypeSafe AI's System One model),
// 2026-09-30, model jev-1.13.0. 2,040 predictions, 0 failed requests.
// Source: results/20260930T185023Z/ in the jev-eval repo (predictions.jsonl, summary.csv).
//
// ECE (e1) and the selective-prediction gate (e4, Banking77 conditions) are scored
// against Jev's own self-reported `confidence` field, not max(probabilities) — Choice
// and Score return both on the wire, and they aren't the same number (see DECISIONS.md).
// Noul (BoolQ) has no separate confidence field, so its e4 row still uses p(yes), the
// only signal that ever existed there.

export const manifest = {
  model: "jev-1.13.0",
  runDate: "Sep 30, 2026",
  totalPredictions: 2040,
  failedRequests: 0,
  repoUrl: "https://github.com/raguram-venkat/jev_eval",
};

export const e1 = [
  { k: 2, n: 240, accuracy: 0.9875, accuracyLo: 0.9708, accuracyHi: 1.0, ece: 0.0054, chance: 0.5 },
  { k: 5, n: 450, accuracy: 0.9778, accuracyLo: 0.9622, accuracyHi: 0.9889, ece: 0.0148, chance: 0.2 },
  { k: 20, n: 450, accuracy: 0.8933, accuracyLo: 0.8644, accuracyHi: 0.92, ece: 0.0493, chance: 0.05 },
  { k: 77, n: 300, accuracy: 0.7933, accuracyLo: 0.7433, accuracyHi: 0.8401, ece: 0.0942, chance: 0.013 },
];

export const e2 = {
  n: 300,
  accuracy: 0.91,
  accuracyLo: 0.88,
  accuracyHi: 0.94,
  auroc: 0.974,
  aurocLo: 0.9595,
  aurocHi: 0.9863,
  brier: 0.0643,
  baselineAccuracy: 0.5,
  baselineBrier: 0.25,
};

export const e3 = {
  n: 300,
  mae: 0.3811,
  maeLo: 0.329,
  maeHi: 0.4272,
  exactAccuracy: 0.6667,
  exactAccuracyLo: 0.6167,
  exactAccuracyHi: 0.7234,
  spearman: 0.925,
  baselineMae: 1.2,
  baselineExactAccuracy: 0.2,
  // rows = true stars (1-5), cols = predicted stars (1-5)
  confusion: [
    [48, 12, 0, 0, 0],
    [11, 33, 15, 1, 0],
    [0, 7, 34, 18, 1],
    [1, 0, 4, 31, 24],
    [0, 1, 0, 5, 54],
  ],
};

// Real coverage/accuracy curves: sorted by Jev's self-reported confidence desc (BoolQ
// excepted, see note above), cumulative accuracy per coverage level, downsampled to 18
// points. [coverage, accuracy] pairs.
export const e4 = [
  {
    source: "E1, k=20",
    n: 450,
    coverage90: 0.98,
    coverage95: 0.8467,
    curve: [[0.0022,1],[0.06,1],[0.12,0.963],[0.1778,0.975],[0.2378,0.9813],[0.2956,0.985],[0.3533,0.9874],[0.4133,0.9892],[0.4711,0.9906],[0.5311,0.9916],[0.5889,0.9849],[0.6489,0.9829],[0.7067,0.978],[0.7644,0.9709],[0.8244,0.9596],[0.8822,0.9345],[0.9422,0.9151],[1,0.8933]],
  },
  {
    source: "E1, k=77",
    n: 300,
    coverage90: 0.7133,
    coverage95: 0.5667,
    curve: [[0.0033,1],[0.0633,1],[0.12,1],[0.18,1],[0.2367,1],[0.2967,0.9888],[0.3567,0.9813],[0.4133,0.9839],[0.4733,0.9718],[0.53,0.9623],[0.59,0.9435],[0.6467,0.9278],[0.7067,0.9104],[0.7667,0.8826],[0.8233,0.8785],[0.8833,0.8491],[0.94,0.8227],[1,0.7933]],
  },
  {
    source: "E2 (BoolQ)",
    n: 300,
    coverage90: 1.0,
    coverage95: 0.9067,
    curve: [[0.0033,1],[0.0633,1],[0.12,1],[0.18,1],[0.2367,1],[0.2967,1],[0.3567,1],[0.4133,1],[0.4733,1],[0.53,0.9937],[0.59,0.9944],[0.6467,0.9845],[0.7067,0.9811],[0.7667,0.9739],[0.8233,0.9595],[0.8833,0.9547],[0.94,0.9397],[1,0.91]],
  },
];

export const e5 = {
  single: { n: 100, p50: 285.9, p95: 474.3 },
  multi1: { n: 30, p50: 287.6, p95: 360.0 },
  multi5: { n: 30, p50: 307.5, p95: 457.8 },
  models: { n: 30, p50: 302.6, p95: 402.3 },
  ratio5v1: 1.0694,
};

// Every field below is read straight off results/20260930T185023Z/predictions.jsonl and
// data/frozen/*.jsonl (matched by id) — no hand-waved numbers. pTrue/pPred/top3 are each
// prediction's own `probabilities` dict (how Jev's distribution scored that label). The
// separate `conf` field is Jev's self-reported `confidence` — the signal the gate and ECE
// actually sweep on Choice/Score (see the note above). The two aren't always the same
// number; where there's a `conf` field, compare it to the gate cutoff, not to pPred.
// BoolQ (Noul) has no self-reported confidence field at all, so there's no `conf` there.
const BOOLQ_GATE_NOTE =
  "BoolQ clears 90% accuracy at full coverage, so the gate escalates nothing at this target.";

export const failures = [
  {
    quote: "I don't know where to look to find my PIN.",
    cause: "Text reads like the predicted label",
    dataset: "Banking77 · k=77",
    trueLabel: "get physical card",
    pTrue: 0.0,
    predLabel: "passcode forgotten",
    pPred: 0.63,
    conf: 0.61,
    top3: [["passcode forgotten", 0.63], ["change pin", 0.33], ["pin blocked", 0.02]],
    gate: { pct: 0.85, verdict: "escalated", note: "Confidence 61% is below the 85% cutoff — the gate catches this one." },
  },
  {
    quote: "This place is CLOSED now. Waaaa! So take your stingy butts to Chipotle.",
    cause: "Text reads negative, label says 5 stars",
    dataset: "Yelp",
    trueLabel: "5★",
    pTrue: 0.0,
    predLabel: "2★",
    pPred: 0.6,
    conf: 0.64,
    top3: [["2★", 0.6], ["1★", 0.25], ["3★", 0.12]],
    starDistance: 3,
    gate: { pct: null, verdict: "na", note: "Yelp/E3 has no selective-prediction gate." },
  },
  {
    quote: "How long does a card delivery take?",
    cause: "Near-synonym intents",
    dataset: "Banking77 · k=77",
    trueLabel: "card arrival",
    pTrue: 0.01,
    predLabel: "card delivery estimate",
    pPred: 0.99,
    conf: 0.99,
    top3: [["card delivery estimate", 0.99], ["card arrival", 0.01]],
    gate: { pct: 0.85, verdict: "auto", note: "Confidence 99% clears the 85% cutoff — the gate misses this one." },
  },
  {
    quote: "Is there such a thing as a miniature pig?",
    cause: "Ground truth itself looks debatable — teacup pigs exist",
    dataset: "BoolQ",
    trueLabel: "False",
    pTrue: 0.31,
    predLabel: "True",
    pPred: 0.69,
    gate: { pct: null, verdict: "auto", note: BOOLQ_GATE_NOTE },
  },
  {
    quote: "Is the Big Dipper the same as Ursa Major?",
    cause: "None obvious",
    dataset: "BoolQ",
    trueLabel: "False",
    pTrue: 0.49,
    predLabel: "True",
    pPred: 0.51,
    gate: { pct: null, verdict: "auto", note: BOOLQ_GATE_NOTE },
  },
];
