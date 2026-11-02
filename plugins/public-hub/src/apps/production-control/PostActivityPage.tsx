import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";
import {
  classifyRunDowntime,
  classifyWorkCenterDowntime,
  fetchMesDowntimeReasons,
  type MesWorkCenterTodayItem,
  type MesWorkCenterTodayMes,
  type RunDowntimeView,
} from "./api";
import { BrandBar } from "./cockpitShared";
import { DowntimeReasonModal } from "./DowntimeReasonModal";
import { useOperatorSession } from "./OperatorSessionContext";
import {
  formatDurationHms,
  serverClockOffsetMs,
  serverNowMs,
} from "./runTimeline";
import { useCockpitActivity } from "./CockpitActivityContext";
import {
  classifiableDowntime,
  formatTimeHmSp,
  isReasonPending,
  projectPostDowntimes,
  type DowntimeListFilter,
} from "./workCenterActivity";

type Props = {
  token: string;
  branch: string;
  workCenter: string;
  workCenterName: string;
  onBack: () => void;
};

type ClassifyTarget = {
  item: MesWorkCenterTodayItem;
  /** NULL em parada autônoma — classificação por identidade do downtime. */
  runId: string | null;
  downtimeId: string;
};

const INITIAL_VISIBLE = 8;

/** Adapta o downtime diário ao DTO de entrada do modal de classificação. */
function toRunDowntimeView(target: ClassifyTarget): RunDowntimeView {
  const dt = target.item.downtime;
  return {
    id: target.downtimeId,
    runId: target.runId,
    reasonCode: dt?.reasonCode ?? null,
    reasonLabel: dt?.reasonLabel ?? null,
    category: dt?.category ?? null,
    note: dt?.note ?? null,
    confirmed: Boolean(dt?.confirmed),
    source: dt?.source ?? null,
    startedAt: dt ? target.item.startedAt : null,
    endedAt: dt ? target.item.endedAt : null,
  };
}

function SummaryStrip({ data }: { data: MesWorkCenterTodayMes }) {
  const { stopCount, pendingReasonCount } = data.summary;
  return (
    <dl className="pcp-pub-activity__summary" aria-label="Resumo das paradas">
      <div className="pcp-pub-activity__metric">
        <dt>Paradas</dt>
        <dd>{stopCount}</dd>
      </div>
      <div
        className={`pcp-pub-activity__metric${
          pendingReasonCount > 0 ? " pcp-pub-activity__metric--pending" : ""
        }`}
      >
        <dt>Sem motivo</dt>
        <dd>{pendingReasonCount}</dd>
      </div>
    </dl>
  );
}

function DowntimeFilterBar({
  filter,
  pendingCount,
  onChange,
}: {
  filter: DowntimeListFilter;
  pendingCount: number;
  onChange: (next: DowntimeListFilter) => void;
}) {
  return (
    <div
      className="pcp-pub-activity__filters"
      role="group"
      aria-label="Filtrar paradas"
    >
      <button
        type="button"
        className={`pcp-pub-activity__filter${
          filter === "all" ? " pcp-pub-activity__filter--active" : ""
        }`}
        aria-pressed={filter === "all"}
        onClick={() => onChange("all")}
      >
        Todas
      </button>
      <button
        type="button"
        className={`pcp-pub-activity__filter${
          filter === "pending" ? " pcp-pub-activity__filter--active" : ""
        }${pendingCount > 0 ? " pcp-pub-activity__filter--warn" : ""}`}
        aria-pressed={filter === "pending"}
        onClick={() => onChange("pending")}
      >
        Sem motivo
        {pendingCount > 0 ? (
          <span className="pcp-pub-activity__filter-count">{pendingCount}</span>
        ) : null}
      </button>
    </div>
  );
}

function DowntimeList({
  items,
  busy,
  visibleCount,
  onShowMore,
  onClassify,
}: {
  items: MesWorkCenterTodayItem[];
  busy: boolean;
  visibleCount: number;
  onShowMore: () => void;
  onClassify: (target: ClassifyTarget) => void;
}) {
  const visible = items.slice(0, visibleCount);
  const remaining = items.length - visible.length;

  return (
    <>
      <ol className="pcp-pub-activity__list">
        {visible.map((item) => {
          const target = classifiableDowntime(item);
          const pending = isReasonPending(item);
          const open = item.endedAt == null;
          const dt = item.downtime;
          const classifiable = target !== null;
          const reasonLabel =
            dt?.reasonLabel ??
            (dt ? "Motivo não informado" : "Motivo não disponível");
          return (
            <li
              key={item.stateEventId}
              className={`pcp-pub-activity__entry${
                open ? " pcp-pub-activity__entry--open" : ""
              }${pending ? " pcp-pub-activity__entry--pending" : ""}`}
            >
              <div className="pcp-pub-activity__entry-time">
                <strong>{formatTimeHmSp(item.startedAt)}</strong>
                <span>
                  {item.endedAt ? formatTimeHmSp(item.endedAt) : "Em andamento"}
                </span>
              </div>
              <div className="pcp-pub-activity__entry-body">
                <div className="pcp-pub-activity__entry-head">
                  <strong className="pcp-pub-activity__state pcp-pub-activity__state--stopped">
                    Parada
                  </strong>
                  <span className="pcp-pub-activity__duration">
                    {formatDurationHms(item.effectiveDurationSeconds)}
                    {open ? " · em andamento" : ""}
                  </span>
                </div>
                <p className="pcp-pub-activity__meta">
                  {item.productionOrder
                    ? `OP ${item.productionOrder}${
                        item.operationCode
                          ? ` · op. ${item.operationCode}`
                          : ""
                      }`
                    : "Sem OP vinculada"}
                  {item.source === "system" ||
                  item.source === "automatic_detection"
                    ? " · automática"
                    : ""}
                </p>
                <p className="pcp-pub-activity__reason">
                  {reasonLabel}
                  {pending ? (
                    <span className="pcp-pub-activity__pending">
                      {" "}
                      ·{" "}
                      {dt?.reasonCode
                        ? "aguardando confirmação"
                        : "sem motivo"}
                    </span>
                  ) : null}
                </p>
                {dt?.note ? (
                  <p className="pcp-pub-activity__note">{dt.note}</p>
                ) : null}
              </div>
              {classifiable ? (
                <button
                  type="button"
                  className={`pcp-pub__btn pcp-pub-activity__classify${
                    pending
                      ? " pcp-pub__btn--primary"
                      : " pcp-pub__btn--ghost"
                  }`}
                  disabled={busy}
                  onClick={() => onClassify({ item, ...target })}
                >
                  {pending || !dt?.confirmed
                    ? "Informar motivo"
                    : "Alterar motivo"}
                </button>
              ) : null}
            </li>
          );
        })}
      </ol>
      {remaining > 0 ? (
        <button
          type="button"
          className="pcp-pub__btn pcp-pub__btn--ghost pcp-pub-activity__more"
          onClick={onShowMore}
        >
          Ver mais ({remaining})
        </button>
      ) : null}
    </>
  );
}

/**
 * Paradas do posto: consulta e classificação das paradas MES do centro de
 * trabalho no dia civil de São Paulo. Filtra `stopped` só nesta projeção —
 * o histórico compartilhado do cockpit permanece intacto.
 */
export function PostActivityPage({
  token,
  branch,
  workCenter,
  workCenterName,
  onBack,
}: Props) {
  const { session, status, invalidate, openIdentify } = useOperatorSession();
  const { data, error, loading, refresh } = useCockpitActivity();
  const [classifying, setClassifying] = useState<ClassifyTarget | null>(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState<DowntimeListFilter>("all");
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE);
  const filterScopeRef = useRef<string | null>(null);

  const clockOffsetRef = useRef(0);
  useEffect(() => {
    clockOffsetRef.current = data
      ? serverClockOffsetMs(data.referenceAt, Date.now())
      : 0;
  }, [data]);
  const serverNow = useCallback(
    () => serverNowMs(Date.now(), clockOffsetRef.current),
    [],
  );
  const loadReasons = useCallback(() => fetchMesDowntimeReasons(token), [token]);

  const downtimes = useMemo(() => {
    if (!data || data.source !== "mes") return [];
    return projectPostDowntimes(data.items, filter);
  }, [data, filter]);

  useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE);
  }, [filter, data?.date, data?.workCenter]);

  // Prioriza pendências só na primeira carga do posto/dia — não sobrescreve
  // a escolha do operador após classificar ou mudar o filtro.
  useEffect(() => {
    if (!data || data.source !== "mes") return;
    const scope = `${data.workCenter}|${data.date}`;
    if (filterScopeRef.current === scope) return;
    filterScopeRef.current = scope;
    setFilter(data.summary.pendingReasonCount > 0 ? "pending" : "all");
  }, [data]);

  const handleClassify = useCallback(
    async (reasonCode: string, note: string | null) => {
      if (!classifying || !session) return;
      setBusy(true);
      try {
        if (classifying.runId) {
          await classifyRunDowntime(token, session.sessionToken, classifying.runId, {
            reasonCode,
            note,
            downtimeId: classifying.downtimeId,
          });
        } else {
          await classifyWorkCenterDowntime(
            token,
            session.sessionToken,
            classifying.downtimeId,
            { reasonCode, note },
          );
        }
        await refresh();
      } catch (err) {
        if (err instanceof Error && "status" in err) {
          const statusCode = (err as { status?: number }).status;
          if (statusCode === 401) invalidate();
        }
        throw err;
      } finally {
        setBusy(false);
      }
    },
    [classifying, session, token, refresh, invalidate],
  );

  let body: React.ReactNode;
  if (status === "restoring") {
    body = <p className="pcp-pub__empty">Restaurando sessão…</p>;
  } else if (!session) {
    body = (
      <div className="pcp-pub-activity__notice" role="status">
        <p>
          Identifique-se para ver as paradas reais deste posto hoje. A
          identificação vale somente para esta bancada.
        </p>
        <button
          type="button"
          className="pcp-pub__btn pcp-pub__btn--primary"
          onClick={openIdentify}
        >
          Identificar operador
        </button>
      </div>
    );
  } else if (loading && !data) {
    body = <p className="pcp-pub__empty">Carregando paradas…</p>;
  } else if (error) {
    body = (
      <div className="pcp-pub-activity__notice" role="alert">
        <p>{error.message}</p>
        {error.retryable ? (
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={() => void refresh()}
          >
            <RefreshCw size={16} aria-hidden="true" /> Tentar novamente
          </button>
        ) : null}
      </div>
    );
  } else if (!data) {
    body = <p className="pcp-pub__empty">Paradas indisponíveis.</p>;
  } else if (data.source === "totvs") {
    body = (
      <div className="pcp-pub-activity__notice" role="status">
        <p>
          Este posto não possui sensoriamento MES — o histórico diário de
          paradas reais não se aplica aqui. Os apontamentos seguem pelo
          fluxo habitual do posto.
        </p>
      </div>
    );
  } else {
    const pendingCount = data.summary.pendingReasonCount;
    const stopCount = data.summary.stopCount;
    const emptyMessage =
      stopCount === 0
        ? `Nenhuma parada registrada neste posto hoje (${data.date}).`
        : filter === "pending"
          ? "Nenhuma parada sem motivo neste período."
          : "Nenhuma parada para exibir com o filtro atual.";

    body = (
      <>
        <SummaryStrip data={data} />
        <DowntimeFilterBar
          filter={filter}
          pendingCount={pendingCount}
          onChange={setFilter}
        />
        {downtimes.length === 0 ? (
          <p className="pcp-pub__empty pcp-pub-activity__empty" role="status">
            {emptyMessage}
          </p>
        ) : (
          <DowntimeList
            items={downtimes}
            busy={busy}
            visibleCount={visibleCount}
            onShowMore={() =>
              setVisibleCount((n) => n + INITIAL_VISIBLE)
            }
            onClassify={setClassifying}
          />
        )}
        <p className="pcp-pub-activity__meta" role="note">
          Horários em horário de São Paulo. Estas são as paradas reais medidas
          pelo sensor do posto (MES) — diferentes dos apontamentos de parada
          do TOTVS.
        </p>
      </>
    );
  }

  return (
    <section className="pcp-pub pcp-pub--activity">
      <BrandBar
        eyebrow={`Paradas do posto · Filial ${branch}`}
        title={workCenterName || workCenter}
        code={workCenter}
        stats={
          data?.source === "mes" ? (
            <span className="pcp-pub__chip">
              {data.date} · horário de São Paulo
            </span>
          ) : null
        }
        lead={
          <button
            type="button"
            className="pcp-pub__back pcp-pub__back--icon"
            onClick={onBack}
            aria-label="Voltar para a fila"
            title="Voltar para a fila"
          >
            <ArrowLeft size={22} strokeWidth={2.4} aria-hidden="true" />
          </button>
        }
      />

      <div className="pcp-pub__wrap">{body}</div>

      <DowntimeReasonModal
        open={Boolean(classifying)}
        downtime={classifying ? toRunDowntimeView(classifying) : null}
        busy={busy}
        serverNow={serverNow}
        loadReasons={loadReasons}
        onClassify={handleClassify}
        onClose={() => setClassifying(null)}
      />
    </section>
  );
}
