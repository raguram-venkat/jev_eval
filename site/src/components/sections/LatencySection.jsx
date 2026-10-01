import LatencyChart from "../charts/LatencyChart";
import Reveal from "../Reveal";

export default function LatencySection() {
  return (
    <section id="latency" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>What does it cost to ask more at once?</h2>
          <span className="tag">latency</span>
        </div>
        <p className="sec-note">
          100 sequential single-question calls, 30 network-baseline pings, and a paired 30-vs-30
          single- vs 5-question test against the same state &mdash; concurrency 1, cache off
          throughout.
        </p>
      </Reveal>
      <Reveal delay={80}>
        <div className="panel">
          <LatencyChart />
          <p className="finding finding-top">
            Five questions in one request cost <b>7% more</b> at the median than one question
            (307ms vs 288ms) &mdash; nowhere near a 5&times; penalty. Batching questions against
            shared state is close to free.
          </p>
        </div>
      </Reveal>
    </section>
  );
}
