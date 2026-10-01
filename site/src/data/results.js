// Real numbers from one live run against Jev (TypeSafe AI's System One model),
// 2026-09-30, model jev-1.13.0. 2,040 predictions, 0 failed requests.
// Source: results/20260930T185023Z/ in the jev-eval repo (predictions.jsonl, summary.csv).

export const manifest = {
  model: "jev-1.13.0",
  runDate: "Sep 30, 2026",
  totalPredictions: 2040,
  failedRequests: 0,
  repoUrl: "https://github.com/raguram-venkat/jev_eval",
};

export const e1 = [
  { k: 2, n: 240, accuracy: 0.9875, accuracyLo: 0.9708, accuracyHi: 1.0, ece: 0.006, chance: 0.5 },
  { k: 5, n: 450, accuracy: 0.9778, accuracyLo: 0.9622, accuracyHi: 0.9889, ece: 0.0177, chance: 0.2 },
  { k: 20, n: 450, accuracy: 0.8933, accuracyLo: 0.8644, accuracyHi: 0.92, ece: 0.0617, chance: 0.05 },
  { k: 77, n: 300, accuracy: 0.7933, accuracyLo: 0.7433, accuracyHi: 0.8401, ece: 0.0961, chance: 0.013 },
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

// Real coverage/accuracy curves: sorted by confidence desc, cumulative accuracy per
// coverage level, downsampled to 18 points. [coverage, accuracy] pairs.
export const e4 = [
  {
    source: "E1, k=20",
    n: 450,
    coverage90: 0.98,
    coverage95: 0.8467,
    curve: [[0.0022,1],[0.06,1],[0.12,0.963],[0.1778,0.975],[0.2378,0.9813],[0.2956,0.9774],[0.3533,0.9811],[0.4133,0.9839],[0.4711,0.9858],[0.5311,0.9874],[0.5889,0.9849],[0.6489,0.976],[0.7067,0.978],[0.7644,0.9709],[0.8244,0.9596],[0.8822,0.9345],[0.9422,0.9127],[1,0.8933]],
  },
  {
    source: "E1, k=77",
    n: 300,
    coverage90: 0.7133,
    coverage95: 0.6067,
    curve: [[0.0033,1],[0.0633,1],[0.12,1],[0.18,1],[0.2367,1],[0.2967,0.9888],[0.3567,0.9907],[0.4133,0.9839],[0.4733,0.9718],[0.53,0.9623],[0.59,0.9492],[0.6467,0.9278],[0.7067,0.9104],[0.7667,0.8826],[0.8233,0.8745],[0.8833,0.8491],[0.94,0.8227],[1,0.7933]],
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

export const failures = [
  {
    quote: "How long does a card delivery take?",
    why: "Near-synonym intents",
    detail: "Banking77, k=77",
    true: "card arrival",
    pred: "card delivery estimate",
    conf: "p(true) = 0.01",
  },
  {
    quote: "I don't know where to look to find my PIN.",
    why: "Text reads like the predicted label",
    detail: "Banking77, k=77",
    true: "get physical card",
    pred: "passcode forgotten",
    conf: "p(true) = 0.00",
  },
  {
    quote: "Is the Big Dipper the same as Ursa Major?",
    why: "Landed right at the coin flip",
    detail: "BoolQ",
    true: "False",
    pred: "True",
    conf: "p(yes) = 0.51",
  },
  {
    quote: "Is there such a thing as a miniature pig?",
    why: "Ground truth itself looks debatable — teacup pigs exist",
    detail: "BoolQ",
    true: "False",
    pred: "True",
    conf: "p(yes) = 0.69",
  },
  {
    quote: "This place is CLOSED now. Waaaa! So take your stingy butts to Chipotle.",
    why: "Text reads negative, label says 5 stars",
    detail: "Yelp",
    true: "5★",
    pred: "2★",
    conf: "p(true) = 0.00",
  },
];
