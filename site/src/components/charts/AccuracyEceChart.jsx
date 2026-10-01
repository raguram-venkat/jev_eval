import { useRef } from "react";
import { e1 } from "../../data/results";
import { scaleLinear, scaleLog } from "./scales";
import Tooltip from "./Tooltip";
import { useTooltip } from "./useTooltip";

const W = 800;
const H_ACC = 230;
const H_ECE = 110;
const M = { t: 16, r: 70, b: 30, l: 40 };

export default function AccuracyEceChart() {
  const ref = useRef(null);
  const [tooltip, show, hide] = useTooltip();

  const x = scaleLog(2, 77, M.l, W - M.r);
  const yAcc = scaleLinear(0, 1, H_ACC - M.b, M.t);
  const maxEce = 0.12;
  const yEce = scaleLinear(0, maxEce, H_ECE - M.b, M.t);

  const last = e1[e1.length - 1];
  const accPath = `M ${e1.map((d) => `${x(d.k)},${yAcc(d.accuracy)}`).join(" L ")}`;
  const chancePath = `M ${e1.map((d) => `${x(d.k)},${yAcc(d.chance)}`).join(" L ")}`;
  const ecePath = `M ${e1.map((d) => `${x(d.k)},${yEce(d.ece)}`).join(" L ")}`;

  return (
    <div className="chart-wrap" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H_ACC}`} role="img" aria-label="Accuracy vs number of options, Jev vs chance">
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <g key={v}>
            <line x1={M.l} x2={W - M.r} y1={yAcc(v)} y2={yAcc(v)} className="grid-line" />
            <text x={M.l - 10} y={yAcc(v) + 4} textAnchor="end" className="axis-label">
              {Math.round(v * 100)}%
            </text>
          </g>
        ))}
        {e1.map((d) => (
          <text key={d.k} x={x(d.k)} y={H_ACC - M.b + 20} textAnchor="middle" className="axis-label">
            k={d.k}
          </text>
        ))}

        <path d={chancePath} className="chart-line-dashed" />
        <text x={x(last.k) + 8} y={yAcc(last.chance) + 4} className="axis-label">
          chance
        </text>

        <path d={accPath} className="chart-line series-1" />
        {e1.map((d) => (
          <g key={d.k}>
            <line
              x1={x(d.k)}
              x2={x(d.k)}
              y1={yAcc(d.accuracyLo)}
              y2={yAcc(d.accuracyHi)}
              className="ci-whisker series-1"
            />
            <circle
              cx={x(d.k)}
              cy={yAcc(d.accuracy)}
              r={5}
              className="chart-dot series-1"
              onMouseMove={(evt) =>
                show(evt, ref, `k=${d.k}  acc=${(d.accuracy * 100).toFixed(1)}%  n=${d.n}`)
              }
              onMouseLeave={hide}
            />
          </g>
        ))}
        <text x={x(last.k) + 8} y={yAcc(last.accuracy) + 4} className="chart-direct-label series-1">
          Jev
        </text>
      </svg>

      <svg viewBox={`0 0 ${W} ${H_ECE}`} role="img" aria-label="Calibration error vs number of options">
        {[0, 0.06, 0.12].map((v) => (
          <g key={v}>
            <line x1={M.l} x2={W - M.r} y1={yEce(v)} y2={yEce(v)} className="grid-line" />
            <text x={M.l - 10} y={yEce(v) + 3} textAnchor="end" className="axis-label">
              {(v * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        <text x={W - M.r + 8} y={M.t + 8} className="axis-label">
          ECE
        </text>
        <path d={ecePath} className="chart-line series-2" />
        {e1.map((d) => (
          <circle
            key={d.k}
            cx={x(d.k)}
            cy={yEce(d.ece)}
            r={4.5}
            className="chart-dot series-2"
            onMouseMove={(evt) => show(evt, ref, `k=${d.k}  ECE=${(d.ece * 100).toFixed(1)}%`)}
            onMouseLeave={hide}
          />
        ))}
      </svg>

      <Tooltip tooltip={tooltip} />
    </div>
  );
}
