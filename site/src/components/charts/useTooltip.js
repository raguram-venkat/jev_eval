import { useCallback, useState } from "react";

/** Positions a tooltip relative to a container ref, from a mouse event. */
export function useTooltip() {
  const [tooltip, setTooltip] = useState(null);

  const show = useCallback((evt, containerRef, content) => {
    const rect = containerRef.current.getBoundingClientRect();
    setTooltip({ x: evt.clientX - rect.left, y: evt.clientY - rect.top, content });
  }, []);

  const hide = useCallback(() => setTooltip(null), []);

  return [tooltip, show, hide];
}
