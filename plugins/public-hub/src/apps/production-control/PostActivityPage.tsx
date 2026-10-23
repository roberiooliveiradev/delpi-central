import { useCallback, useEffect, useRef, useState } from "react";
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
  stateLabel,
} from "./runTimeline";
import { useCockpitActivity } from "./CockpitActivityContext";
import {
  classifiableDowntime,
  formatTimeHmSp,
  isReasonPending,
  timelineSegments,
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

function itemDescription(item: MesWorkCenterTodayItem): string {
  const range = `${formatTimeHmSp(item.startedAt)}–${item.endedAt ? formatTimeHmSp(item.endedAt) : "agora"}`;
  const base = `${stateLabel(item.state)} ${range}`;
  if (item.state === "stopped") {
    const dt = item.downtime;
    const reason = dt?.reasonLabel ?? (dt ? "Motivo não informado" : "Motivo não disponível");
    return `${base} · ${reason}`;
  }
  return base;
}

function SummaryStrip({ data }: { data: MesWorkCenterTodayMes }) {
  const { producingSeconds, stoppedSeconds, stopCount, pendingReasonCount } =
    data.summary;
  return (
    <dl className="pcp-pub-activity__summary" aria-label="Resumo do dia">
      <div className="pcp-pub-activity__metric pcp-pub-activity__metric--producing">
        <dt>Produzindo</dt>
        <dd>{formatDurationHms(producingSeconds)}</dd>
      </div>
      <div className="pcp-pub-activity__metric pcp-pub-activity__metric--stopped">
        <dt>Parado</dt>
        <dd>{formatDurationHms(stoppedSeconds)}</dd>
      </div>
      <div className="pcp-pub-activity__metric">
        <dt>Paradas</dt>
        <dd>{stopCount}</dd>
      </div>
      <div
        className={`pcp-pub-activity__metric${
          pendingReasonCount > 0 ? " pcp-pub-activity__metric--pending" : ""
        }`}
      >
        <dt>Motivos pendentes</dt>
        <dd>{pendingReasonCount}</dd>
      </div>
    </dl>
  );
}

function DayBand({ data }: { data: MesWorkCenterTodayMes }) {
  const segments = timelineSegments(data.items, data.from, data.to);
  return (
    <figure className="pcp-pub-activity-band">
      <div
        className="pcp-pub-timeline__band pcp-pub-activity-band__track"
        role="img"
        aria-label={
          segments.length > 0
            ? segments.map((seg) => itemDescription(seg.item)).join(" → ")
            : "Sem registros MES no dia"
        }
      >
        {segments.map((seg) => (
          <span
            key={seg.item.stateEventId}
            className={`pcp-pub-timeline__seg pcp-pub-activity-band__seg pcp-pub-timeline__seg--${seg.item.state}`}
            style={{ left: `${seg.leftPct}%`, width: `${seg.widthPct}%` }}
            title={itemDescription(seg.item)}
          />
        ))}
      </div>
      <figcaption className="pcp-pub-activity-band__caption">
        <span>{formatTimeHmSp(data.from)}</span>
        <span>{formatTimeHmSp(data.to)}</span>
      </figcaption>
    </figure>
  );
}

function ActivityList({
  data,
  busy,
  onClassify,
}: {
  data: MesWorkCenterTodayMes;
  busy: boolean;
  onClassify: (target: ClassifyTarget) => void;
}) {
  return (
    <ol className="pcp-pub-activity__list">
      {data.items.map((item) => {
        const target = classifiableDowntime(item);
        const pending = isReasonPending(item);
        const open = item.endedAt == null;
        const dt = item.downtime;
        const classifiable =
          item.state === "stopped" && target !== null;
        return (
          <li
            key={item.stateEventId}
            className={`pcp-pub-activity__entry${
              open ? " pcp-pub-activity__entry--open" : ""
            }`}
          >
            <div className="pcp-pub-activity__entry-time">
              <strong>{formatTimeHmSp(item.startedAt)}</strong>
              <span>{item.endedAt ? formatTimeHmSp(item.endedAt) : "em curso"}</span>
            </div>
            <div className="pcp-pub-activity__entry-body">
              <div className="pcp-pub-activity__entry-head">
                <strong className={`pcp-pub-activity__state pcp-pub-activity__state--${item.state}`}>
                  {item.state === "stopped" ? "Parada" : stateLabel(item.state)}
                </strong>
                <span className="pcp-pub-activity__duration">
                  {formatDurationHms(item.effectiveDurationSeconds)}
                  {open ? " · em curso" : ""}
                </span>
              </div>
              <p className="pcp-pub-activity__meta">
                {item.productionOrder
                  ? `OP ${item.productionOrder}${item.operationCode ? ` · op. ${item.operationCode}` : ""}`
                  : "Sem produção vinculada"}
                {item.source === "system" || item.source === "automatic_detection"
                  ? " · automática"
                  : ""}
              </p>
              {item.state === "stopped" ? (
                <p className="pcp-pub-activity__reason">
                  {dt?.reasonLabel ??
                    (dt ? "Motivo não informado" : "Motivo não disponível")}
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
              ) : null}
              {dt?.note ? (
                <p className="pcp-pub-activity__note">{dt.note}</p>
              ) : null}
            </div>
            {classifiable ? (
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--ghost pcp-pub-activity__classify"
                disabled={busy}
                onClick={() => onClassify({ item, ...target })}
              >
                {pending || !dt?.confirmed ? "Informar motivo" : "Alterar motivo"}
              </button>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

/**
 * Atividade do posto (Etapa 3): resumo oficial, faixa temporal real e
 * histórico diário MES com classificação por identidade — inclusive de
 * runs já encerrados do mesmo posto.
 */
export function PostActivityPage({
  token,
  branch,
  workCenter,
  workCenterName,
  onBack,
}: Props) {
  const { session, status, invalidate, openIdentify } = useOperatorSession();
  // Leitura diária compartilhada (Etapa 4): mesmo GET do cartão e dos
  // indicadores do cabeçalho — classificar aqui já atualiza os tiles.
  const { data, error, loading, refresh } = useCockpitActivity();
  const [classifying, setClassifying] = useState<ClassifyTarget | null>(null);
  const [busy, setBusy] = useState(false);

  // Relógio do servidor: o offset é ANCORADO uma vez por resposta (no
  // recebimento do referenceAt). Recalculá-lo a cada chamada congelaria o
  // "agora" no referenceAt — o timer da parada aberta não avançaria.
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
          // Parada autônoma (sem OP): endpoint por identidade — o backend
          // confere que a sessão pertence ao posto da parada.
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
          const status = (err as { status?: number }).status;
          if (status === 401) invalidate();
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
          Identifique-se para ver a produção e as paradas reais deste posto
          hoje. A identificação vale somente para esta bancada.
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
    body = <p className="pcp-pub__empty">Carregando atividade…</p>;
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
    body = <p className="pcp-pub__empty">Atividade indisponível.</p>;
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
  } else if (data.items.length === 0) {
    body = (
      <>
        <SummaryStrip data={data} />
        <p className="pcp-pub__empty">
          Nenhum registro MES neste posto hoje ({data.date}).
        </p>
      </>
    );
  } else {
    body = (
      <>
        <SummaryStrip data={data} />
        <h2 className="pcp-pub__detail-section">Linha do tempo do dia</h2>
        <DayBand data={data} />
        <h2 className="pcp-pub__detail-section">Eventos e paradas</h2>
        <ActivityList data={data} busy={busy} onClassify={setClassifying} />
        <p className="pcp-pub-activity__meta" role="note">
          Horários em horário de São Paulo. Estas são as paradas reais medidas
          pelo sensor do posto (MES) — diferentes dos apontamentos de parada
          do TOTVS. Espaços sem evento na faixa significam ausência de
          registro, não máquina desligada.
        </p>
      </>
    );
  }

  return (
    <section className="pcp-pub pcp-pub--activity">
      <BrandBar
        eyebrow={`Atividade do posto · Filial ${branch}`}
        title={workCenterName || workCenter}
        code={workCenter}
        stats={
          data?.source === "mes" ? (
            <span className="pcp-pub__chip">{data.date} · horário de São Paulo</span>
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
