import { useEffect, useState } from "react";

import { fetchStrategicIndicatorsRefreshStatus } from "../../data/api/strategicIndicatorsCacheApi";
import "./StatusBadge.css";

type LastUpdateBadgeProps = {
  getAccessToken?: () => string | undefined;
  /** Alterar este valor força nova consulta (ex.: após "Atualizar"). */
  refreshKey?: number | string;
};

// Cache em módulo: evita refazer a chamada a cada navegação entre páginas.
const CACHE_TTL_MS = 60_000;
let cachedLabel: string | null = null;
let cachedAt = 0;

function formatUpdatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function LastUpdateBadge({
  getAccessToken,
  refreshKey,
}: LastUpdateBadgeProps) {
  const [label, setLabel] = useState<string | null>(() => {
    if (cachedLabel && Date.now() - cachedAt < CACHE_TTL_MS) {
      return cachedLabel;
    }
    return null;
  });

  useEffect(() => {
    let active = true;

    if (cachedLabel && Date.now() - cachedAt < CACHE_TTL_MS) {
      setLabel(cachedLabel);
      return () => {
        active = false;
      };
    }

    fetchStrategicIndicatorsRefreshStatus(getAccessToken)
      .then((status) => {
        if (!active) return;
        const next = status.last_completed_at
          ? formatUpdatedAt(status.last_completed_at)
          : null;
        cachedLabel = next;
        cachedAt = Date.now();
        setLabel(next);
      })
      .catch(() => {
        if (active) setLabel(null);
      });

    return () => {
      active = false;
    };
  }, [getAccessToken, refreshKey]);

  if (!label) {
    return null;
  }

  return (
    <span
      className="si-status-badge si-status-badge--info"
      title="Data da última atualização dos dados (cache materializado da API)"
    >
      Atualizado em {label}
    </span>
  );
}
