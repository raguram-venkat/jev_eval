export default function Tooltip({ tooltip }) {
  if (!tooltip) return null;
  return (
    <div className="chart-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
      {tooltip.content}
    </div>
  );
}
