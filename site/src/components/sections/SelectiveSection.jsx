import SelectiveChart from "../charts/SelectiveChart";
import Reveal from "../Reveal";

export default function SelectiveSection() {
  return (
    <section id="selective" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>What if it could say "I don't know"?</h2>
          <span className="tag">selective prediction</span>
        </div>
        <p className="sec-note">
          Reusing Choice and Noul's own predictions &mdash; no new calls. Sort every answer by
          Jev's own confidence, then ask: how much traffic can be auto-handled at a target
          accuracy if the rest escalates to a human?
        </p>
      </Reveal>
      <Reveal delay={80}>
        <div className="panel">
          <SelectiveChart />
          <div className="legend">
            <span className="item">
              <span className="sw series-1" /> k=20
            </span>
            <span className="item">
              <span className="sw series-2" /> k=77
            </span>
            <span className="item">
              <span className="sw series-3" /> BoolQ
            </span>
            <span className="item">
              <span className="sw sw-dash" /> 90% / 95% accuracy target
            </span>
          </div>
          <p className="finding finding-top">
            At k=20, <b>98% of traffic</b> can be auto-handled at 90% accuracy &mdash; only 2%
            needs a human. At k=77 that drops to <b>71%</b>: harder questions escalate more,
            which is exactly what a selective-prediction gate is for.
          </p>
        </div>
      </Reveal>
    </section>
  );
}
