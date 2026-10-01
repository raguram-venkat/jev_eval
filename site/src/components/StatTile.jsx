export default function StatTile({ label, value, sub, gauge }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {gauge !== undefined && (
        <div className="gauge">
          <span style={{ width: `${gauge}%` }} />
        </div>
      )}
    </div>
  );
}
