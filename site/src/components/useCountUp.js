import { useEffect, useState } from "react";

const REDUCED_MOTION =
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Animates a number up from 0 on mount. Skips straight to the target under reduced motion. */
export function useCountUp(target, duration = 1000, decimals = 0) {
  const [value, setValue] = useState(REDUCED_MOTION ? target : 0);

  useEffect(() => {
    if (REDUCED_MOTION) {
      setValue(target);
      return undefined;
    }
    let frame;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setValue(target * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value.toFixed(decimals);
}
