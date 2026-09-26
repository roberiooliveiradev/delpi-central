import { Pause, Play, Square } from "lucide-react";
import type { MachineLoadOperation } from "./api";
import { formatQty } from "./cockpitShared";
import { useProductionRun } from "./useProductionRun";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

type Props = {
  token: string;
  branch: string;
  workCenter: string;
  operation: MachineLoadOperation;
  runUpdatedSignal?: number;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
};

export function ProductionRunControls({
  token,
  branch,
  workCenter,
  operation,
  runUpdatedSignal = 0,
  runRealtimeEvent = null,
  realtimeConnected = false,
}: Props) {
  const {
    session,
    run,
    runMatchesOperation,
    busy,
    error,
    operatorCode,
    operatorName,
    setOperatorCode,
    setOperatorName,
    identify,
    clearSession,
    play,
    pause,
    resume,
    stop,
  } = useProductionRun({
    token,
    branch,
    workCenter,
    operation,
    runUpdatedSignal,
    runRealtimeEvent,
    realtimeConnected,
  });

  const counted = run?.countedPieces ?? run?.piecesTotal ?? 0;
  const deviceOnline = run?.device?.online;
  const otherRun =
    run && !runMatchesOperation
      ? `Produção ativa em ${run.productionOrder} / ${run.operationCode}`
      : null;

  return (
    <div className="pcp-pub__run" onClick={(event) => event.stopPropagation()}>
      {!session ? (
        <form
          className="pcp-pub__run-identify"
          onSubmit={(event) => {
            event.preventDefault();
            void identify();
          }}
        >
          <p className="pcp-pub__run-title">Identifique-se para contar peças</p>
          <label className="pcp-pub__run-field">
            <span>Código do operador (Protheus)</span>
            <input
              value={operatorCode}
              onChange={(event) => setOperatorCode(event.target.value)}
              autoComplete="username"
              required
              minLength={1}
              maxLength={40}
            />
          </label>
          <label className="pcp-pub__run-field">
            <span>Nome (opcional)</span>
            <input
              value={operatorName}
              onChange={(event) => setOperatorName(event.target.value)}
              autoComplete="name"
              maxLength={120}
            />
          </label>
          <button type="submit" className="pcp-pub__btn pcp-pub__btn--primary" disabled={busy}>
            Entrar no posto
          </button>
        </form>
      ) : (
        <div className="pcp-pub__run-session">
          <div className="pcp-pub__run-session-head">
            <div>
              <p className="pcp-pub__run-title">
                {session.operatorName || session.operatorCode}
              </p>
              <p className="pcp-pub__run-note">Sessão neste posto · contagem via Pulso</p>
            </div>
            <button
              type="button"
              className="pcp-pub__btn pcp-pub__btn--ghost"
              onClick={() => void clearSession()}
              disabled={busy || Boolean(run && runMatchesOperation)}
            >
              Sair
            </button>
          </div>

          {otherRun ? <p className="pcp-pub__run-warn">{otherRun}</p> : null}

          {run && runMatchesOperation ? (
            <div className="pcp-pub__run-readout" aria-live="polite">
              <div className="pcp-pub__run-count">
                <span>Peças contadas</span>
                <strong>{formatQty(counted)}</strong>
              </div>
              <dl className="pcp-pub__run-meta">
                <div>
                  <dt>Status</dt>
                  <dd>{run.status === "running" ? "Contando" : "Pausada"}</dd>
                </div>
                <div>
                  <dt>Dispositivo</dt>
                  <dd>
                    {deviceOnline === false
                      ? "Offline"
                      : deviceOnline
                        ? "Online"
                        : run.device?.status || "—"}
                  </dd>
                </div>
                {run.totvsProducedQty != null ? (
                  <div>
                    <dt>Apontado TOTVS</dt>
                    <dd>
                      {formatQty(run.totvsProducedQty)}
                      {run.divergencePieces != null
                        ? ` · Δ ${formatQty(run.divergencePieces)}`
                        : null}
                    </dd>
                  </div>
                ) : null}
              </dl>
              <div className="pcp-pub__run-actions">
                {run.status === "running" ? (
                  <button
                    type="button"
                    className="pcp-pub__btn pcp-pub__btn--ghost"
                    onClick={() => void pause()}
                    disabled={busy}
                  >
                    <Pause size={16} aria-hidden="true" />
                    Pausar
                  </button>
                ) : (
                  <button
                    type="button"
                    className="pcp-pub__btn pcp-pub__btn--primary"
                    onClick={() => void resume()}
                    disabled={busy}
                  >
                    <Play size={16} aria-hidden="true" />
                    Retomar
                  </button>
                )}
                <button
                  type="button"
                  className="pcp-pub__btn pcp-pub__btn--ghost"
                  onClick={() => void stop()}
                  disabled={busy}
                >
                  <Square size={16} aria-hidden="true" />
                  Encerrar
                </button>
              </div>
            </div>
          ) : (
            <div className="pcp-pub__run-actions">
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={() => void play()}
                disabled={busy || Boolean(otherRun)}
              >
                <Play size={16} aria-hidden="true" />
                Iniciar contagem
              </button>
            </div>
          )}
        </div>
      )}

      {error ? <p className="pcp-pub__run-error">{error}</p> : null}
    </div>
  );
}
