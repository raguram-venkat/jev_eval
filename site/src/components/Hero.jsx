import { e1, manifest } from "../data/results";
import StatTile from "./StatTile";
import { useCountUp } from "./useCountUp";

export default function Hero() {
  const k2 = e1[0];
  const k77 = e1[e1.length - 1];
  const calls = useCountUp(manifest.totalPredictions, 1000, 0);
  const accK2 = useCountUp(k2.accuracy * 100, 1000, 1);
  const accK77 = useCountUp(k77.accuracy * 100, 1000, 1);
  const ratio = useCountUp(k77.accuracy / k77.chance, 1000, 0);

  return (
    <section id="overview" className="hero">
      <div className="eyebrow">
        <span className="dot" /> LIVE RUN <span className="sep">&middot;</span> model {manifest.model}{" "}
        <span className="sep">&middot;</span> {manifest.totalPredictions.toLocaleString()} predictions,{" "}
        {manifest.failedRequests} failed
      </div>

      <h1>
        Jev holds its answer through 20 choices.
        <br />
        At 77, it starts guessing.
      </h1>

      <p className="lede">
        I benchmarked <strong>Jev</strong>, TypeSafe AI's hosted typed-decision model, on three
        question shapes it exposes &mdash; pick one of k, yes/no, 1&ndash;5 stars &mdash; against
        three public datasets, zero-shot. The point wasn't just "is it right," it's whether its
        confidence means anything. Every number below came from a real API call.
      </p>

      <div className="stats">
        <StatTile label="Live calls" value={Number(calls).toLocaleString()} sub={`${manifest.failedRequests} failed`} />
        <StatTile label="Accuracy at k=2" value={`${accK2}%`} gauge={Number(accK2)} />
        <StatTile label="Accuracy at k=77" value={`${accK77}%`} gauge={Number(accK77)} />
        <StatTile label="vs. chance at k=77" value={`${ratio}×`} sub="79.3% right vs. a 1.3% baseline" />
      </div>
    </section>
  );
}
