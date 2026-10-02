import { useEffect, useRef, useState } from "react";
import { Clock, Pause, Play, Square } from "lucide-react";
import type { MachineLoadOperation, PendingMesDowntime, RunDowntimeView } from "./api.ts";
import { DowntimeElapsedTimer } from "./DowntimeElapsedTimer";
import { DowntimeReasonModal } from "./DowntimeReasonModal";
import { PendingDowntimesModal } from "./PendingDowntimesModal";
import { ProductionRunTimeline } from "./ProductionRunTimeline";
import { usePendingMesDowntimes } from "./usePendingMesDowntimes.ts";
import { useRunTimeline } from "./useRunTimeline.ts";
import { formatQty } from "./cockpitShared";
import { formatTimeHm } from "./runTimeline";
import {
  piecesToOperatorUnit,
  resolveProductionRunProgress,
} from "./productionRunProgress.ts";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import { useProductionRun } from "./useProductionRun.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

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
  // C4: sessão do operador vem do provider do posto — este componente só
  // consome; identificação/troca acontecem no nível do cockpit.
  const { session, status: sessionStatus, invalidate: invalidateSession, openIdentify } =
    useOperatorSession();
  const {
    run,
    runMatchesOperation,
    busy,
    error,
    play,
    pause,
    resume,
    stop,
    loadDowntimeReasons,
    classifyDowntime,
    classifyDowntimeById,
  } = useProductionRun({
    token,
    branch,
    workCenter,
    operation,
    session,
    onAuthError: invalidateSession,
    runUpdatedSignal,
    runRealtimeEvent,
    realtimeConnected,
  });

  const counted = run?.countedPieces ?? run?.piecesTotal ?? 0;
  const progress = resolveProductionRunProgress(counted, run?.targetPieces);
  const [reasonModalOpen, setReasonModalOpen] = useState(false);
  const [downtimeClockForId, setDowntimeClockForId] = useState<string | null>(null);
  // `downtime` é a parada aberta do run — também com status "running"
  // quando a parada foi detectada automaticamente por ausência de peças.
  const openDowntime = run?.downtime ?? null;
  const openDowntimeId = openDowntime?.id ?? null;
  const downtimeClockOpen = downtimeClockForId === openDowntimeId && openDowntimeId !== null;
  const pendingDowntime = run?.pendingDowntime ?? null;
  const downtimeUnclassified = Boolean(openDowntime && !openDowntime.confirmed);

  const {
    items: pendingItems,
    error: pendingError,
    refresh: refreshPending,
  } = usePendingMesDowntimes({
    token,
    sessionToken: session?.sessionToken ?? null,
    branch,
    workCenter,
    refreshSignal: runUpdatedSignal,
  });
  const [pendingModalOpen, setPendingModalOpen] = useState(false);
  // Alvo manual: parada escolhida na lista de pendências ou na timeline.
  const [manualTarget, setManualTarget] = useState<{
    runId: string;
    downtime: RunDowntimeView;
  } | null>(null);
  // Quando o alvo veio da lista de pendências, ao fechar/confirmar o modal de
  // motivo retorna à lista (em vez de encerrar o fluxo) até o operador sair.
  const [returnToPending, setReturnToPending] = useState(false);
  // Alvo do modal: escolha manual (lista de pendências/timeline) primeiro;
  // senão a parada aberta; senão a pendência encerrada do run ativo.
  const modalDowntime = manualTarget?.downtime ?? openDowntime ?? pendingDowntime;
  const autoStopped =
    run?.status === "running" && Boolean(openDowntime ?? null);

  const { timeline, serverNow } = useRunTimeline({
    token,
    sessionToken: session?.sessionToken ?? null,
    runId: run?.id ?? null,
    branch,
    workCenter,
    runRealtimeEvent,
    realtimeConnected,
  });

  // A classificação abre automaticamente quando há parada aberta sem motivo
  // (Pause manual ou auto-stop) ou uma parada encerrada pendente — inclusive
  // após F5/reconexão, via pendingDowntime do snapshot.
  const autoOpenRef = useRef<string | null>(null);
  const classifyTarget = openDowntime?.confirmed === false ? openDowntime : null;
  const pendingTarget = pendingDowntime?.confirmed === false ? pendingDowntime : null;
  const classifyTargetId = (classifyTarget ?? pendingTarget)?.id ?? null;
  useEffect(() => {
    if (classifyTargetId && autoOpenRef.current !== classifyTargetId) {
      autoOpenRef.current = classifyTargetId;
      setReasonModalOpen(true);
    }
    if (!classifyTargetId) autoOpenRef.current = null;
  }, [classifyTargetId]);

  const openPendingTarget = (item: PendingMesDowntime) => {
    if (!item.runId) return;
    setPendingModalOpen(false);
    setReturnToPending(true);
    setManualTarget({
      runId: item.runId,
      downtime: {
        id: item.id,
        runId: item.runId,
        reasonCode: item.reasonCode,
        reasonLabel: null,
        category: null,
        note: item.note,
        confirmed: item.confirmed,
        source: item.source,
        startedAt: item.startedAt,
        endedAt: item.endedAt,
      },
    });
    setReasonModalOpen(true);
  };
  const piecesFactor = run?.piecesConversionFactor ?? operation.pieces_conversion_factor;
  const toOperatorUnit = (pieces: number) => piecesToOperatorUnit(pieces, piecesFactor);
  const deviceOnline = run?.device?.online;
  const otherRun =
    run && !runMatchesOperation
      ? `Produção ativa em ${run.productionOrder} / ${run.operationCode}`
      : null;

  return (
    <div className="pcp-pub__run" onClick={(event) => event.stopPropagation()}>
      {!session ? (
        <div className="pcp-pub__run-identify">
          <p className="pcp-pub__run-note">
            {sessionStatus === "restoring"
              ? "Restaurando sessão do operador…"
              : "Identifique-se no posto para iniciar a produção."}
          </p>
          {sessionStatus === "anonymous" ? (
            <div className="pcp-pub__run-actions">
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={openIdentify}
              >
                <Play size={16} aria-hidden="true" />
                Identificar operador
              </button>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="pcp-pub__run-session">

          {pendingItems && pendingItems.length > 0 ? (
            <div className="pcp-pub__run-actions">
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--ghost"
                onClick={() => setPendingModalOpen(true)}
                disabled={busy}
              >
                Paradas sem motivo ({pendingItems.length})
              </button>
            </div>
          ) : null}

          {otherRun ? <p className="pcp-pub__run-warn">{otherRun}</p> : null}

          {run && runMatchesOperation && deviceOnline === false ? (
            <p className="pcp-pub__run-warn pcp-pub__run-warn--telemetry" role="status">
              Contador sem comunicação — última contagem conhecida mantida.
              Você ainda pode pausar ou encerrar.
            </p>
          ) : null}

          {run && runMatchesOperation ? (
            <div className="pcp-pub__run-readout" aria-live="polite">
              {openDowntime ? (
                <div
                  className="pcp-pub__downtime pcp-pub__downtime--hero"
                  role="status"
                  aria-label="Produção parada"
                >
                  <div className="pcp-pub__downtime-head">
                    <p className="pcp-pub__downtime-title">
                      <span className="pcp-pub__downtime-dot" aria-hidden="true" />
                      Produção parada
                    </p>
                    <span className="pcp-pub__downtime-badge">
                      <Pause size={14} aria-hidden="true" />
                      <span className="pcp-pub__downtime-badge-label">
                        {openDowntime.reasonLabel?.trim() || "Sem motivo"}
                      </span>
                    </span>
                  </div>
                  <div className="pcp-pub__downtime-body">
                    <div className="pcp-pub__downtime-readout">
                      {openDowntime.startedAt ? (
                        <DowntimeElapsedTimer
                          startedAt={openDowntime.startedAt}
                          serverNow={serverNow}
                        />
                      ) : (
                        <span className="pcp-pub__downtime-timer">--:--:--</span>
                      )}
                      <p className="pcp-pub__downtime-caption">Tempo de parada</p>
                      {downtimeClockOpen && openDowntime.startedAt ? (
                        <p className="pcp-pub__downtime-note">
                          Iniciada às {formatTimeHm(openDowntime.startedAt)}
                        </p>
                      ) : null}
                      {openDowntime.note ? (
                        <p className="pcp-pub__downtime-note">{openDowntime.note}</p>
                      ) : null}
                    </div>
                    {openDowntime.startedAt ? (
                      <button
                        type="button"
                        className="pcp-pub__downtime-clock"
                        aria-expanded={downtimeClockOpen}
                        aria-label={
                          downtimeClockOpen
                            ? "Ocultar horário de início da parada"
                            : `Ver horário de início da parada, ${formatTimeHm(openDowntime.startedAt)}`
                        }
                        onClick={() =>
                          setDowntimeClockForId((current) =>
                            current === openDowntimeId ? null : openDowntimeId,
                          )
                        }
                      >
                        <Clock size={20} strokeWidth={1.75} aria-hidden="true" />
                      </button>
                    ) : null}
                  </div>
                </div>
              ) : null}
              {progress ? (
                <div className="pcp-pub__run-progress">
                  <p className="pcp-pub__run-progress-state">
                    {progress.targetReached ? "Meta atingida" : "Produção em andamento"}
                  </p>
                  <div className="pcp-pub__run-progress-values">
                    <strong>
                      {formatQty(toOperatorUnit(progress.countedPieces))} /{" "}
                      {formatQty(toOperatorUnit(progress.targetPieces))} peças
                    </strong>
                    <span>{Math.round(progress.progressPercent)}%</span>
                  </div>
                  <div
                    className="pcp-pub__run-progress-track"
                    role="progressbar"
                    aria-label="Progresso da meta do run"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={progress.visualPercent}
                    aria-valuetext={`${formatQty(toOperatorUnit(progress.countedPieces))} de ${formatQty(toOperatorUnit(progress.targetPieces))} peças`}
                  >
                    <span
                      className="pcp-pub__run-progress-fill"
                      style={{ width: `${progress.visualPercent}%` }}
                    />
                  </div>
                  <p className="pcp-pub__run-progress-note">
                    {progress.overproductionPieces > 0
                      ? `+${formatQty(toOperatorUnit(progress.overproductionPieces))} peças acima da meta`
                      : progress.targetReached
                        ? "Produção prevista concluída"
                        : `Faltam ${formatQty(toOperatorUnit(progress.remainingPieces))} peças`}
                  </p>
                </div>
              ) : (
                <div className="pcp-pub__run-count">
                  <span>Peças contadas</span>
                  <strong>{formatQty(toOperatorUnit(counted))}</strong>
                </div>
              )}
              <dl className="pcp-pub__run-meta">
                <div>
                  <dt>Status</dt>
                  <dd>
                    {run.status === "running"
                      ? autoStopped
                        ? "Parada detectada"
                        : "Contando"
                      : "Produção pausada"}
                  </dd>
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
                  <>
                    {openDowntime ? (
                      <button
                        type="button"
                        className="pcp-pub__btn pcp-pub__btn--ghost"
                        onClick={() => setReasonModalOpen(true)}
                        disabled={busy}
                      >
                        {openDowntime.confirmed ? "Alterar motivo" : "Informar motivo"}
                      </button>
                    ) : pendingDowntime ? (
                      <button
                        type="button"
                        className="pcp-pub__btn pcp-pub__btn--ghost"
                        onClick={() => setReasonModalOpen(true)}
                        disabled={busy}
                      >
                        Informar motivo
                        {(run.pendingDowntimeCount ?? 0) > 1
                          ? ` (${run.pendingDowntimeCount})`
                          : ""}
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="pcp-pub__btn pcp-pub__btn--ghost"
                      onClick={() => void pause()}
                      disabled={busy}
                    >
                      <Pause size={16} aria-hidden="true" />
                      Pausar
                    </button>
                  </>
                ) : (
                  <>
                    {openDowntime ? (
                      <button
                        type="button"
                        className="pcp-pub__btn pcp-pub__btn--ghost"
                        onClick={() => setReasonModalOpen(true)}
                        disabled={busy}
                      >
                        {openDowntime.confirmed ? "Alterar motivo" : "Informar motivo"}
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="pcp-pub__btn pcp-pub__btn--primary"
                      onClick={() => {
                        if (downtimeUnclassified) setReasonModalOpen(true);
                        else void resume();
                      }}
                      disabled={busy}
                    >
                      <Play size={16} aria-hidden="true" />
                      Retomar
                    </button>
                  </>
                )}
                <button
                  type="button"
                  className="pcp-pub__btn pcp-pub__btn--ghost"
                  onClick={() => {
                    if (downtimeUnclassified) setReasonModalOpen(true);
                    else void stop();
                  }}
                  disabled={busy}
                >
                  <Square size={16} aria-hidden="true" />
                  Encerrar
                </button>
              </div>
              {timeline && timeline.items.length > 0 ? (
                <details className="pcp-pub__timeline">
                  <summary>Linha do tempo</summary>
                  <ProductionRunTimeline
                    timeline={timeline}
                    serverNow={serverNow}
                    onSelectDowntime={(item) => {
                      if (!item.downtime || item.downtime.confirmed || !run) return;
                      setReturnToPending(false);
                      setManualTarget({
                        runId: run.id,
                        downtime: {
                          id: item.downtime.id,
                          runId: run.id,
                          reasonCode: item.downtime.reasonCode,
                          reasonLabel: item.downtime.reasonLabel,
                          category: item.downtime.category,
                          note: item.downtime.note,
                          confirmed: item.downtime.confirmed,
                          source: item.downtime.source,
                          startedAt: item.startedAt,
                          endedAt: item.endedAt,
                        },
                      });
                      setReasonModalOpen(true);
                    }}
                  />
                </details>
              ) : null}
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

      <PendingDowntimesModal
        open={pendingModalOpen}
        items={pendingItems}
        error={pendingError}
        busy={busy}
        onSelect={openPendingTarget}
        onClose={() => setPendingModalOpen(false)}
      />

      <DowntimeReasonModal
        open={reasonModalOpen && Boolean(modalDowntime)}
        downtime={modalDowntime}
        busy={busy}
        serverNow={serverNow}
        loadReasons={loadDowntimeReasons}
        onClassify={async (reasonCode, note) => {
          if (manualTarget) {
            await classifyDowntimeById(
              manualTarget.runId,
              manualTarget.downtime.id,
              reasonCode,
              note,
            );
            setManualTarget(null);
            await refreshPending();
            if (returnToPending) {
              setReturnToPending(false);
              setPendingModalOpen(true);
            }
            return;
          }
          await classifyDowntime(reasonCode, note, modalDowntime?.id ?? null);
        }}
        onClose={() => {
          setManualTarget(null);
          setReasonModalOpen(false);
          if (returnToPending) {
            setReturnToPending(false);
            void refreshPending();
            setPendingModalOpen(true);
          }
        }}
      />
    </div>
  );
}
