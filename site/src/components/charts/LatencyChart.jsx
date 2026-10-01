import { useRef } from "react";
import { e5 } from "../../data/results";
import { scaleLinear } from "./scales";
import Tooltip from "./Tooltip";
import { useTooltip } from "./useTooltip";

const W = 800;
const H = 170;
const M = { t: 16, r: 60, b: 26, l: 130 };
const MAX_V = 520;

const ROWS = [
  { label: "1 question", key: "multi1", cls: "series-1" },
  { label: "5 questions", key: "multi5", cls: "series-2" },
  { label: "network baseline", key: "models", cls: "series-3" },
];

export default function LatencyChart() {
  const ref = useRef(null);
  const [tooltip, show, hide] = useTooltip();
  const x = scaleLinear(0, MAX_V, M.l, W - M.r);
  const rowH = (H - M.t - M.b) / ROWS.length;

  return (
    <div className="chart-wrap" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Latency p50/p95 by request shape">
        {[0, 100, 200, 300, 400, 500].map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={M.t} y2={H - M.b} className="grid-line-v" />
            <text x={x(v)} y={H - M.b + 16} textAnchor="middle" className="axis-label">
              {v}
            </text>
          </g>
        ))}
        <text x={x(MAX_V)} y={H - 2} textAnchor="end" className="axis-label">
          ms (p50 marker, line to p95)
        </text>

        {ROWS.map((row, i) => {
          const d = e5[row.key];
          const cy = M.t + i * rowH + rowH / 2;
          return (
            <g key={row.key}>
              <text x={M.l - 12} y={cy + 4} textAnchor="end" className="row-label">
                {row.label}
              </text>
              <line x1={x(d.p50)} x2={x(d.p95)} y1={cy} y2={cy} className={`latency-range ${row.cls}`} />
              <circle
                cx={x(d.p50)}
                cy={cy}
                r={6}
                className={`chart-dot ${row.cls}`}
                onMouseMove={(evt) => show(evt, ref, `${row.label}: p50 ${d.p50.toFixed(0)}ms, p95 ${d.p95.toFixed(0)}ms`)}
                onMouseLeave={hide}
              />
              <text x={x(d.p50)} y={cy - 12} textAnchor="middle" className={`chart-direct-label ${row.cls}`}>
                {d.p50.toFixed(0)}ms
              </text>
            </g>
          );
        })}
      </svg>
      <Tooltip tooltip={tooltip} />
    </div>
  );
}
