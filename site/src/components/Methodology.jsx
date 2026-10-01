import Reveal from "./Reveal";

const PRIMITIVES = [
  {
    name: "Choice",
    dataset: "Banking77",
    desc: "Pick one of k customer-support intents from a message, k swept from 2 to 77.",
  },
  {
    name: "Noul",
    dataset: "BoolQ",
    desc: "Yes or no, given a passage and a question — returned as p(yes).",
  },
  {
    name: "Score",
    dataset: "Yelp",
    desc: "Rate a review 1–5 stars, returned as a full probability distribution over levels.",
  },
];

export default function Methodology() {
  return (
    <Reveal className="methodology">
      <p className="methodology-text">
        Zero-shot throughout &mdash; no fine-tuning, no prompt tuning based on results. Every
        accuracy number is scored against a naive baseline and carries a 95% bootstrap
        confidence interval, so "91% accurate" means something more than a number in isolation.
      </p>
      <div className="primitive-cards">
        {PRIMITIVES.map((p) => (
          <div key={p.name} className="primitive-card">
            <div className="primitive-name">{p.name}</div>
            <div className="primitive-dataset">{p.dataset}</div>
            <p className="primitive-desc">{p.desc}</p>
          </div>
        ))}
      </div>
    </Reveal>
  );
}
