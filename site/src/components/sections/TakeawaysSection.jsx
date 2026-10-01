import Reveal from "../Reveal";

const TAKEAWAYS = [
  {
    title: "Confidence erodes faster than correctness.",
    body: "Accuracy drops 20 points from k=2 to k=77; calibration error climbs 16× over the same span. The failure mode isn't just “wrong more often” — it's “wrong while sounding just as sure.” Don't trust a raw confidence score at face value on a hard task without checking it's still calibrated there.",
  },
  {
    title: "Simpler decision shapes are well-calibrated out of the box.",
    body: "Yes/no (AUROC 0.974) and 1–5 star scoring (Brier far below baseline) both came in strong, zero-shot. If your use case is binary or ordinal, Jev's confidence is already a reasonable signal to build on.",
  },
  {
    title: "Selective prediction is a free lever, not a tuning project.",
    body: "It's a re-sort of predictions already in hand, no new calls. Auto-handle 98% of easy traffic at 90%+ accuracy; scale the escalation threshold down as the task gets harder (71% at k=77), rather than picking one global confidence cutoff.",
  },
  {
    title: "Batching questions is close to free.",
    body: "5 questions in one request cost ~7% more than 1, not 5×. If your pipeline asks several independent questions about the same context, ask them together.",
  },
  {
    title: "Not every miss is the model's fault.",
    body: "A couple of the “failures” above have debatable ground truth — teacup pigs exist, a 5-star review reads like a complaint. A benchmark number is only as trustworthy as the labels it's measured against.",
  },
];

export default function TakeawaysSection() {
  return (
    <section id="takeaways" className="section">
      <Reveal>
        <div className="sec-head">
          <h2>What this actually means</h2>
          <span className="tag">the full review</span>
        </div>
      </Reveal>
      <div className="takeaways">
        {TAKEAWAYS.map((t, i) => (
          <Reveal key={t.title} delay={i * 70}>
            <div className="takeaway">
              <span className="takeaway-num">{String(i + 1).padStart(2, "0")}</span>
              <div>
                <div className="takeaway-title">{t.title}</div>
                <p className="takeaway-body">{t.body}</p>
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
