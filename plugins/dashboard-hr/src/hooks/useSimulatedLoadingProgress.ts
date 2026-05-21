import { useEffect, useState } from "react";

export function useSimulatedLoadingProgress(active: boolean) {
  const [percent, setPercent] = useState(0);

  useEffect(() => {
    if (!active) {
      setPercent(0);
      return;
    }

    setPercent(8);

    const interval = window.setInterval(() => {
      setPercent((current) => {
        if (current >= 92) {
          return current;
        }

        const step = 5 + Math.random() * 9;
        return Math.min(92, current + step);
      });
    }, 420);

    return () => window.clearInterval(interval);
  }, [active]);

  return Math.round(percent);
}
