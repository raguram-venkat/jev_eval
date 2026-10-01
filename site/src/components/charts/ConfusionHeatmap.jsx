import { useEffect, useRef, useState } from "react";
import { e3 } from "../../data/results";
import Tooltip from "./Tooltip";
import { useTooltip } from "./useTooltip";

const CELL = 52;
const GAP = 3;
const M = { t: 10, l: 30, b: 28, r: 10 };
const N = 5;
const W = M.l + N * (CELL + GAP) - GAP + M.r;
const H = M.t + N * (CELL + GAP) - GAP + M.b;

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function toHex([r, g, b]) {
  return `#${[r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
}
function lerpColor(c0, c1, t) {
  return toHex(c0.map((v, i) => v + (c1[i] - v) * t));
}

function readTokens() {
  const style = getComputedStyle(document.documentElement);
  return {
    low: hexToRgb(style.getPropertyValue("--seq-100").trim()),
    high: hexToRgb(style.getPropertyValue("--seq-700").trim()),
  };
}

export default function ConfusionHeatmap() {
  const ref = useRef(null);
  const [tooltip, show, hide] = useTooltip();
  const [tokens, setTokens] = useState(null);

  useEffect(() => {
    setTokens(readTokens());
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setTokens(readTokens());
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const maxV = Math.max(...e3.confusion.flat());

  return (
    <div className="chart-wrap" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Yelp true vs predicted star confusion matrix">
        {e3.confusion.map((row, r) => (
          <g key={r}>
            <text x={M.l - 8} y={M.t + r * (CELL + GAP) + CELL / 2 + 4} textAnchor="end" className="axis-label">
              {r + 1}&#9733;
            </text>
            {row.map((v, c) => {
              const t = maxV ? v / maxV : 0;
              const fill = tokens && v > 0 ? lerpColor(tokens.low, tokens.high, t) : null;
              const textLight = t > 0.55;
              return (
                <g
                  key={c}
                  onMouseMove={(evt) => show(evt, ref, `true ${r + 1}★ → pred ${c + 1}★: ${v}`)}
                  onMouseLeave={hide}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    x={M.l + c * (CELL + GAP)}
                    y={M.t + r * (CELL + GAP)}
                    width={CELL}
                    height={CELL}
                    rx={4}
                    className={v === 0 ? "heat-cell-empty" : undefined}
                    fill={fill ?? undefined}
                  />
                  <text
                    x={M.l + c * (CELL + GAP) + CELL / 2}
                    y={M.t + r * (CELL + GAP) + CELL / 2 + 5}
                    textAnchor="middle"
                    className={v === 0 ? "heat-text-empty" : textLight ? "heat-text-light" : "heat-text-dark"}
                  >
                    {v}
                  </text>
                </g>
              );
            })}
          </g>
        ))}
        {e3.confusion[0].map((_, c) => (
          <text
            key={c}
            x={M.l + c * (CELL + GAP) + CELL / 2}
            y={M.t + N * (CELL + GAP) - GAP + 16}
            textAnchor="middle"
            className="axis-label"
          >
            {c + 1}&#9733;
          </text>
        ))}
      </svg>
      <Tooltip tooltip={tooltip} />
    </div>
  );
}
