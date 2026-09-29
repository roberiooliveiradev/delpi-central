import { useEffect, useMemo, useState } from "react";
import { serverOffsetMs } from "../utils/duration";

export function useServerClock(referenceAt?: string) {
  const offset = useMemo(() => referenceAt ? serverOffsetMs(referenceAt) : 0, [referenceAt]);
  const [clientNow, setClientNow] = useState(0);
  useEffect(() => {
    const firstTick = window.setTimeout(() => setClientNow(Date.now()), 0);
    const timer = window.setInterval(() => setClientNow(Date.now()), 1_000);
    return () => { window.clearTimeout(firstTick); window.clearInterval(timer); };
  }, []);
  return clientNow + offset;
}
