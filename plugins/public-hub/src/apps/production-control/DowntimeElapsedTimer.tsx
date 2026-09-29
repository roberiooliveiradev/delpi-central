import { useEffect, useState } from "react";
import { elapsedSeconds, formatDurationHms } from "./runTimeline";

type Props = {
  /** `started_at` persistido no backend — fonte oficial do início da parada. */
  startedAt: string;
  /** Função que devolve o "agora" estimado no servidor (relógio local + offset). */
  serverNow: () => number;
};

/**
 * Timer da parada MES. O valor é sempre derivado de `startedAt` — nunca um
 * contador incremental — então sobrevive a aba em background, suspensão de
 * timers, reload e navegação card↔detalhe.
 */
export function DowntimeElapsedTimer({ startedAt, serverNow }: Props) {
  const [now, setNow] = useState(() => serverNow());

  useEffect(() => {
    setNow(serverNow());
    const timer = window.setInterval(() => setNow(serverNow()), 1000);
    return () => window.clearInterval(timer);
  }, [serverNow, startedAt]);

  const seconds = elapsedSeconds(startedAt, now);
  return (
    <span
      className="pcp-pub__downtime-timer"
      role="timer"
      aria-label={`Parada há ${formatDurationHms(seconds)}`}
    >
      {formatDurationHms(seconds)}
    </span>
  );
}
