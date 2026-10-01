import ConfusionHeatmap from "../charts/ConfusionHeatmap";
import { e2, e3 } from "../../data/results";
import Reveal from "../Reveal";

export default function CalibrationSection() {
  return (
    <section id="calibration" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>Is it calibrated?</h2>
          <span className="tag">Noul &middot; BoolQ &middot; Score &middot; Yelp</span>
        </div>
        <p className="sec-note">
          Yes/no reading comprehension and 1&ndash;5 star sentiment &mdash; two different shapes
          of "typed decision," each scored against a naive baseline instead of each other.
        </p>
      </Reveal>

      <div className="twoup">
        <Reveal delay={80}>
          <div className="miniblock">
            <h3>BoolQ &middot; yes/no</h3>
            <div className="big">{(e2.accuracy * 100).toFixed(1)}%</div>
            <div className="vs">accuracy, vs. a 50% baseline &middot; n={e2.n}</div>
            <div className="kv">
              <span>AUROC</span>
              <span>{e2.auroc.toFixed(3)}</span>
            </div>
            <div className="kv">
              <span>Brier score</span>
              <span>
                {e2.brier.toFixed(3)} <span className="muted">(baseline {e2.baselineBrier.toFixed(3)})</span>
              </span>
            </div>
            <div className="kv">
              <span>95% CI</span>
              <span>
                {(e2.accuracyLo * 100).toFixed(1)}&ndash;{(e2.accuracyHi * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </Reveal>

        <Reveal delay={160}>
          <div className="miniblock">
            <h3>Yelp &middot; 1&ndash;5 stars</h3>
            <div className="big">{e3.mae.toFixed(2)}</div>
            <div className="vs">
              mean absolute error, vs. {e3.baselineMae.toFixed(2)} for always guessing 3 &middot; n={e3.n}
            </div>
            <div className="kv">
              <span>Exact-star accuracy</span>
              <span>
                {(e3.exactAccuracy * 100).toFixed(1)}%{" "}
                <span className="muted">(baseline {(e3.baselineExactAccuracy * 100).toFixed(0)}%)</span>
              </span>
            </div>
            <div className="kv">
              <span>Spearman &rho;</span>
              <span>{e3.spearman.toFixed(3)}</span>
            </div>
            <div className="kv">
              <span>95% CI (MAE)</span>
              <span>
                {e3.maeLo.toFixed(3)}&ndash;{e3.maeHi.toFixed(3)}
              </span>
            </div>
          </div>
        </Reveal>
      </div>

      <Reveal delay={200}>
        <div className="panel">
          <p className="finding">
            The Yelp confusion matrix is almost entirely on or one step off the diagonal &mdash;
            Jev rarely mistakes a 1-star review for a 5-star one. Misses cluster at the
            boundaries (2&harr;3, 3&harr;4), where star ratings are genuinely fuzzy to begin with.
          </p>
          <ConfusionHeatmap />
        </div>
      </Reveal>
    </section>
  );
}
