import AccuracyEceChart from "../charts/AccuracyEceChart";
import Reveal from "../Reveal";

export default function ChoiceSection() {
  return (
    <section id="choice" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>How far can it count?</h2>
          <span className="tag">Choice &middot; Banking77</span>
        </div>
        <p className="sec-note">
          The same customer-support message, judged against 2, 5, 20 or 77 possible intents
          &mdash; criteria are the option names alone, nothing more. 1,440 messages, 3 random
          label subsets per k.
        </p>
      </Reveal>
      <Reveal delay={80}>
        <div className="panel">
          <p className="finding">
            Accuracy stays within a point of ceiling through <b>k=5</b>, gives up{" "}
            <b>10 points</b> going from 20 to 77 options, and calibration error (ECE) climbs{" "}
            <b>16&times;</b> from k=2 to k=77 &mdash; confidence erodes even faster than
            correctness does.
          </p>
          <AccuracyEceChart />
        </div>
      </Reveal>
    </section>
  );
}
