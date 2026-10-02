import { failures } from "../../data/results";
import Reveal from "../Reveal";

function pctLabel(p) {
  return p < 0.005 ? "under 0.5%" : `${Math.round(p * 100)}%`;
}

function shapeOf(f) {
  if (f.pTrue < 0.05) return { tag: "confident-miss", label: "Confident miss" };
  if (Math.abs(f.pPred - f.pTrue) < 0.1) return { tag: "coin-flip", label: "Coin flip" };
  return { tag: "moderate-miss", label: "Moderate miss" };
}

function gateVerdict(gate) {
  if (gate.verdict === "na") return "Not gated";
  return gate.verdict === "escalated" ? "Escalated" : "Auto-handled";
}

function BarRow({ label, value, pct, kind, row }) {
  return (
    <>
      <span className="bar-label" style={{ gridRow: row }}>{label}</span>
      <div className="bar-track" style={{ gridRow: row }}>
        <div className={`bar-fill ${kind}`} style={{ width: `${Math.max(pct * 100, 1.5)}%` }} />
      </div>
      <span className="bar-val" style={{ gridRow: row }}>{value}</span>
    </>
  );
}

export default function FailuresSection() {
  return (
    <section id="failures" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>Where it fails</h2>
          <span className="tag">real misses, not cherry-picked wins</span>
        </div>
        <p className="sec-note">
          Five real misclassifications, sorted worst to borderline by how much probability the
          correct answer got. The two bars are both read off Jev's own probability distribution
          for that question, on the same 0&ndash;100 scale: what the correct answer got, and what
          Jev's actual pick got. Where a card also lists a <strong>confidence</strong> number,
          that's a different thing &mdash; Jev's own separately self-reported certainty in its
          answer, not the probability above it. The dashed line is the cutoff E4&apos;s gate
          applies to that confidence number to auto-answer vs. escalate to a human, at a 90%
          accuracy target (BoolQ has no self-reported confidence, so its gate falls back to its
          yes/no probability). <strong>Confident miss</strong> = correct answer under 5%.{" "}
          <strong>Coin flip</strong> = the two bars are within 10 points. <strong>Moderate miss</strong> =
          everything else.
        </p>
      </Reveal>
      <Reveal delay={80}>
        <div className="fail-grid">
          {failures.map((f) => {
            const shape = shapeOf(f);
            const verdict = gateVerdict(f.gate);
            return (
              <div key={f.quote} className="fail-card">
                <div className="fail-head">
                  <div className="quote">{f.quote}</div>
                  <div className="why">
                    {f.cause} &middot; {f.dataset}
                    {f.starDistance != null && <> &middot; {f.starDistance}&#9733; off</>}
                  </div>
                </div>

                <div className="fail-bar-group">
                  <BarRow label="Correct" value={pctLabel(f.pTrue)} pct={f.pTrue} kind="true" row={1} />
                  <BarRow label="Jev chose" value={pctLabel(f.pPred)} pct={f.pPred} kind="pred" row={2} />
                  {f.gate.pct != null && (
                    <div className="gate-line" style={{ marginLeft: `${f.gate.pct * 100}%` }} />
                  )}
                </div>

                {f.top3 && (
                  <div className="top3">
                    Top 3:{" "}
                    {f.top3.map(([label, p], i) => (
                      <span key={label}>
                        {i > 0 && " · "}
                        {label} {Math.round(p * 100)}%
                      </span>
                    ))}
                  </div>
                )}

                {f.conf != null && (
                  <div className="top3">Self-reported confidence: {pctLabel(f.conf)}</div>
                )}

                <div className="fail-foot">
                  <span className={`shape-tag ${shape.tag}`}>{shape.label}</span>
                  <span className={`gate-tag ${f.gate.verdict}`}>
                    Gate @90%: {verdict}
                  </span>
                  <span className="gate-note">{f.gate.note}</span>
                </div>
              </div>
            );
          })}
        </div>
      </Reveal>
    </section>
  );
}
