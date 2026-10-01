import { failures } from "../../data/results";
import Reveal from "../Reveal";

export default function FailuresSection() {
  return (
    <section id="failures" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>Where it fails</h2>
          <span className="tag">real misses, not cherry-picked wins</span>
        </div>
        <p className="sec-note">
          Five real misclassifications, picked to show the different shapes failure takes here
          &mdash; some are the model being wrong, some are arguably the ground truth being
          debatable.
        </p>
      </Reveal>
      <Reveal delay={80}>
        <div className="fail-grid">
          {failures.map((f) => (
            <div key={f.quote} className="fail-card">
              <div>
                <div className="quote">{f.quote}</div>
                <div className="why">
                  {f.why} &middot; {f.detail}
                </div>
              </div>
              <div className="swap">
                <span className="true">{f.true}</span>
                <span className="arrow">&rarr;</span>
                <span className="pred">{f.pred}</span>
                <span className="conf">{f.conf}</span>
              </div>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
