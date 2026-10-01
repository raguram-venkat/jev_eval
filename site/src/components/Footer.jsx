import Reveal from "./Reveal";
import { manifest } from "../data/results";

export default function Footer() {
  return (
    <footer className="footer">
      <Reveal>
        <ul className="caveats">
          <li>
            Banking77 criteria are label-name-only &mdash; the model sees option names, never
            descriptions of what each intent means.
          </li>
          <li>Latency includes real network round-trip time from this machine, not a server-side-only measurement.</li>
          <li>A single run, one point in time, one model version &mdash; Jev may have changed since.</li>
          <li>Zero-shot throughout: no fine-tuning, no prompt or criteria tuning based on these results.</li>
        </ul>
      </Reveal>
      <div className="footer-bar">
        <span>
          Run on {manifest.runDate} &middot; model {manifest.model} &middot; built with{" "}
          <a href={manifest.repoUrl} target="_blank" rel="noreferrer">
            jev-eval
          </a>
        </span>
      </div>
    </footer>
  );
}
