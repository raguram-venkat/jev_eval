import { useRef } from "react";
import { e4 } from "../../data/results";
import { scaleLinear } from "./scales";
import Tooltip from "./Tooltip";
import { useTooltip } from "./useTooltip";

const W = 800;
const H = 260;
const M = { t: 16, r: 20, b: 30, l: 44 };
const SERIES_CLASS = ["series-1", "series-2", "series-3"];

export default function SelectiveChart() {
  const ref = useRef(null);
  const [tooltip, show, hide] = useTooltip();

  const x = scaleLinear(0, 1, M.l, W - M.r);
  const y = scaleLinear(0.5, 1.0, H - M.b, M.t);

  // De-collide end-of-line labels: sort by y, enforce a minimum gap.
  const labels = e4
    .map((series, i) => {
      const last = series.curve[series.curve.length - 1];
      return { name: series.source, x: x(last[0]), y: y(last[1]), cls: SERIES_CLASS[i] };
    })
    .sort((a, b) => a.y - b.y);
  const MIN_GAP = 13;
  for (let i = 1; i < labels.length; i++) {
    if (labels[i].y - labels[i - 1].y < MIN_GAP) labels[i].y = labels[i - 1].y + MIN_GAP;
  }

  return (
    <div className="chart-wrap" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Accuracy vs coverage for selective prediction">
        {[0.5, 0.6, 0.7, 0.8, 0.9, 1.0].map((v) => (
          <g key={v}>
            <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="grid-line" />
            <text x={M.l - 8} y={y(v) + 3} textAnchor="end" className="axis-label">
              {(v * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        {[0, 0.25, 0.5, 0.75, 1.0].map((v) => (
          <text key={v} x={x(v)} y={H - M.b + 18} textAnchor="middle" className="axis-label">
            {(v * 100).toFixed(0)}%
          </text>
        ))}
        <text x={M.l} y={H - 4} className="axis-label">
          coverage (% of traffic kept)
        </text>

        {[0.9, 0.95].map((v) => (
          <line key={v} x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="chart-line-dashed-thin" />
        ))}

        {e4.map((series, i) => (
          <g key={series.source}>
            <path
              d={`M ${series.curve.map((p) => `${x(p[0])},${y(p[1])}`).join(" L ")}`}
              className={`chart-line ${SERIES_CLASS[i]}`}
            />
            {series.curve.map((p, pi) => (
              <circle
                key={pi}
                cx={x(p[0])}
                cy={y(p[1])}
                r={3}
                className={`chart-dot-small ${SERIES_CLASS[i]}`}
                onMouseMove={(evt) =>
                  show(evt, ref, `${series.source}: coverage ${(p[0] * 100).toFixed(0)}%, accuracy ${(p[1] * 100).toFixed(1)}%`)
                }
                onMouseLeave={hide}
              />
            ))}
          </g>
        ))}

        {labels.map((l) => (
          <text key={l.name} x={l.x - 8} y={l.y + 3} textAnchor="end" className={`chart-direct-label ${l.cls}`}>
            {l.name}
          </text>
        ))}
      </svg>
      <Tooltip tooltip={tooltip} />
    </div>
  );
}
