import { useCallback, useRef, useState } from "react";
import {
  refreshStrategicIndicatorsSnapshots,
  waitForStrategicIndicatorsRefresh,
} from "../../data/api/strategicIndicatorsCacheApi";
import { clearAllStrategicIndicatorsCache } from "../../data/cache/strategicIndicatorsReadCache";
import "./RefreshSnapshotButton.css";

type RefreshSnapshotButtonProps = {
  onRefreshed: () => void;
  getAccessToken?: () => string | undefined;
  disabled?: boolean;
  /** Competência YYYY-MM dos filtros da página (opcional). */
  competence?: string;
};

export function RefreshSnapshotButton({
  onRefreshed,
  getAccessToken,
  disabled = false,
  competence,
}: RefreshSnapshotButtonProps) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<"success" | "error" | "background" | null>(
    null,
  );
  const feedbackTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const handleClick = useCallback(async () => {
    if (busy) return;

    setBusy(true);
    setFeedback(null);
    clearTimeout(feedbackTimer.current);

    try {
      const started = await refreshStrategicIndicatorsSnapshots({
        getAccessToken,
        competence,
      });

      clearAllStrategicIndicatorsCache();
      onRefreshed();

      if (started.status === "already_running") {
        setFeedback("background");
      }

      const finalStatus = await waitForStrategicIndicatorsRefresh(getAccessToken);

      if (finalStatus.last_error) {
        throw new Error(finalStatus.last_error);
      }

      clearAllStrategicIndicatorsCache();
      onRefreshed();
      setFeedback("success");
    } catch {
      setFeedback("error");
    } finally {
      setBusy(false);
      feedbackTimer.current = setTimeout(() => setFeedback(null), 5000);
    }
  }, [busy, competence, getAccessToken, onRefreshed]);

  return (
    <span className="si-refresh-snapshot">
      <button
        type="button"
        className="si-refresh-snapshot__button"
        onClick={() => void handleClick()}
        disabled={disabled || busy}
        title="Buscar nova versão dos dados. A versão atual permanece até a nova estar pronta."
        aria-label="Atualizar snapshot"
      >
        <svg
          className={`si-refresh-snapshot__icon ${busy ? "is-spinning" : ""}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21.5 2v6h-6" />
          <path d="M2.5 22v-6h6" />
          <path d="M3.2 15.4A9 9 0 0 0 20.8 8.6" />
          <path d="M20.8 8.6A9 9 0 0 0 3.2 15.4" />
        </svg>
        {busy ? "Atualizando…" : "Atualizar"}
      </button>

      {feedback === "success" ? (
        <span className="si-refresh-snapshot__feedback is-success">
          Dados atualizados
        </span>
      ) : null}

      {feedback === "background" ? (
        <span className="si-refresh-snapshot__feedback is-success">
          Atualização em andamento…
        </span>
      ) : null}

      {feedback === "error" ? (
        <span className="si-refresh-snapshot__feedback is-error">
          Falha ao atualizar
        </span>
      ) : null}
    </span>
  );
}
