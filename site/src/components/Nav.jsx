import { useEffect, useState } from "react";

const SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "choice", label: "Choice" },
  { id: "calibration", label: "Calibration" },
  { id: "selective", label: "Selective" },
  { id: "latency", label: "Latency" },
  { id: "failures", label: "Sample failures" },
  { id: "takeaways", label: "Takeaways" },
];

export default function Nav() {
  const [active, setActive] = useState("overview");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: 0 },
    );
    const els = SECTIONS.map(({ id }) => document.getElementById(id)).filter(Boolean);
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <nav className="nav">
      <div className="nav-inner">
        <a href="#overview" className="nav-brand">
          Jev<span className="nav-brand-dim">benchmark</span>
        </a>
        <div className="nav-links">
          {SECTIONS.map(({ id, label }) => (
            <a key={id} href={`#${id}`} className={active === id ? "nav-link nav-link-active" : "nav-link"}>
              {label}
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
}
