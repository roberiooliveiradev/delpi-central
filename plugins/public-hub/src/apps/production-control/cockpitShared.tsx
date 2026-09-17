import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  buildPublicProductModelGlbUrl,
  fetchPublicDrawingPdf,
} from "./api";
import {
  formatQty,
  formatUnit,
  hasExhaustedOperationBalance,
  isFinishedOperation,
  operationKey,
  operationPendingQty,
  resolveStatus,
  type StatusView,
} from "./cockpitStatus";
import { ProductModelViewer } from "./ProductModelViewer";

export {
  formatQty,
  formatUnit,
  hasExhaustedOperationBalance,
  isFinishedOperation,
  operationKey,
  operationPendingQty,
  resolveStatus,
};
export type { StatusView };

/** Faixa de marca fixa no topo — identidade DELPI e posto em destaque para leitura à distância. */
export function BrandBar({
  eyebrow,
  title,
  code,
  stats,
  actions,
  lead,
  titleExtra,
  metrics,
}: {
  eyebrow?: string;
  title: string;
  code?: string | null;
  stats?: ReactNode;
  actions?: ReactNode;
  lead?: ReactNode;
  titleExtra?: ReactNode;
  metrics?: ReactNode;
}) {
  return (
    <header className="pcp-pub__brandbar">
      <div className="pcp-pub__brandbar-inner">
        <div className="pcp-pub__identity">
          {lead ?? (
            <span className="pcp-pub__logo">
              <img src="/p/logoMinhaDelpi.svg" alt="Minha DELPI" draggable={false} />
            </span>
          )}
          <div className="pcp-pub__identity-text">
            {eyebrow ? <p className="pcp-pub__eyebrow">{eyebrow}</p> : null}
            <div className="pcp-pub__title-row">
              {code ? <span className="pcp-pub__code">{code}</span> : null}
              <h1>{title}</h1>
              {titleExtra}
            </div>
            {stats ? <div className="pcp-pub__stats">{stats}</div> : null}
          </div>
        </div>
        {metrics ? <div className="pcp-pub__brandbar-metrics">{metrics}</div> : null}
        {actions ? <div className="pcp-pub__actions">{actions}</div> : null}
      </div>
    </header>
  );
}

/** Cards de eficiência / produzido / paradas do posto no turno — fila e detalhe. */
export function WorkCenterShiftMetrics({
  shiftLabel,
  shiftPct,
  shiftProducedQty,
  downtimeHours,
  downtimeAvailable,
  onOpenPerformance,
  onOpenDowntime,
}: {
  shiftLabel: string;
  shiftPct: number | null;
  shiftProducedQty: number | null;
  downtimeHours: number | null;
  downtimeAvailable: boolean;
  onOpenPerformance: () => void;
  onOpenDowntime: () => void;
}) {
  const effTone = efficiencyTone(shiftPct);
  const shiftLabelLower = shiftLabel.toLowerCase();

  return (
    <div className="pcp-pub__hero-metrics" role="group" aria-label="Desempenho do posto">
      <button
        type="button"
        className={`pcp-pub__hero-metric pcp-pub__hero-metric--eff-${effTone}`}
        onClick={onOpenPerformance}
        title={`Eficiência do posto no ${shiftLabelLower}`}
      >
        <span className="pcp-pub__hero-metric-label">{shiftLabel}</span>
        <strong className="pcp-pub__hero-metric-value">{formatPercent(shiftPct)}</strong>
      </button>
      <button
        type="button"
        className="pcp-pub__hero-metric"
        onClick={onOpenPerformance}
        title={`Peças produzidas no ${shiftLabelLower}`}
      >
        <span className="pcp-pub__hero-metric-label">Produzido · turno</span>
        <strong className="pcp-pub__hero-metric-value">
          {shiftProducedQty == null
            ? "—"
            : `${formatQty(shiftProducedQty)} ${formatUnit(null, shiftProducedQty)}`}
        </strong>
      </button>
      <button
        type="button"
        className="pcp-pub__hero-metric"
        onClick={onOpenDowntime}
        title={`Paradas apontadas no ${shiftLabelLower} neste posto — clique para ver motivos`}
      >
        <span className="pcp-pub__hero-metric-label">Paradas · turno</span>
        <strong className="pcp-pub__hero-metric-value">
          {downtimeAvailable ? formatHours(downtimeHours) : "—"}
        </strong>
      </button>
    </div>
  );
}

/** Object URL do PDF do desenho — compartilhado pelo preview lado a lado e pela tela cheia. */
export function useDrawingObjectUrl(token: string, branch: string, paCode: string | null) {
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!paCode) {
      setStatus("idle");
      setMessage(null);
      setObjectUrl(null);
      return;
    }

    let active = true;
    let createdUrl: string | null = null;
    setStatus("loading");
    setMessage(null);
    setObjectUrl(null);

    void fetchPublicDrawingPdf(token, branch, paCode)
      .then((blob) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (!active) return;
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Desenho não encontrado para este produto.");
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [token, branch, paCode]);

  return { status, message, objectUrl };
}

export type VisualMode = "drawing" | "model";

export function VisualModeTabs({
  mode,
  onChange,
  show,
}: {
  mode: VisualMode;
  onChange: (mode: VisualMode) => void;
  show: boolean;
}) {
  if (!show) return null;
  return (
    <div className="pcp-pub-visual-tabs" role="tablist" aria-label="Tipo de visualização">
      <button
        type="button"
        role="tab"
        aria-selected={mode === "drawing"}
        className={mode === "drawing" ? "is-active" : undefined}
        onClick={() => onChange("drawing")}
      >
        Desenho
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "model"}
        className={mode === "model" ? "is-active" : undefined}
        onClick={() => onChange("model")}
      >
        Modelo 3D
      </button>
    </div>
  );
}

export function DrawingViewer({
  token,
  branch,
  paCode,
  productCode,
  has3dModel,
  onClose,
}: {
  token: string;
  branch: string;
  paCode: string | null;
  productCode?: string | null;
  has3dModel?: boolean;
  onClose: () => void;
}) {
  const canDraw = Boolean(paCode);
  const canModel = Boolean(has3dModel && productCode);
  const [mode, setMode] = useState<VisualMode>(canDraw ? "drawing" : "model");
  const { status, message, objectUrl } = useDrawingObjectUrl(token, branch, paCode);
  const glbUrl =
    canModel && productCode ? buildPublicProductModelGlbUrl(token, branch, productCode) : null;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const title =
    mode === "model" && productCode
      ? `Modelo 3D ${productCode}`
      : paCode
        ? `Desenho ${paCode}`
        : "Visualização";

  return (
    <div
      className="pcp-pub-viewer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-viewer-title"
    >
      <div className="pcp-pub-viewer__bar">
        <h2 id="pcp-pub-viewer-title">{title}</h2>
        <VisualModeTabs
          show={canDraw && canModel}
          mode={mode}
          onChange={setMode}
        />
        <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
          Fechar
        </button>
      </div>
      {mode === "drawing" ? (
        <>
          {status === "loading" ? <p className="pcp-pub-viewer__state">Carregando desenho…</p> : null}
          {status === "error" ? (
            <p className="pcp-pub-viewer__state pcp-pub-viewer__state--error">{message}</p>
          ) : null}
          {status === "ready" && objectUrl && paCode ? (
            <iframe className="pcp-pub-viewer__frame" title={`Desenho ${paCode}`} src={objectUrl} />
          ) : null}
        </>
      ) : glbUrl && productCode ? (
        <ProductModelViewer
          className="pcp-pub-viewer__model"
          src={glbUrl}
          alt={`Modelo 3D do produto ${productCode}`}
        />
      ) : (
        <p className="pcp-pub-viewer__state">Modelo 3D não disponível para este produto.</p>
      )}
    </div>
  );
}

export function CopyValueButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 1600);
    return () => window.clearTimeout(timer);
  }, [copied]);

  const copy = async () => {
    const ok = await copyToClipboard(value);
    if (ok) setCopied(true);
  };

  return (
    <button
      type="button"
      className={`pcp-pub__copy ${copied ? "pcp-pub__copy--done" : ""}`}
      onClick={copy}
      title={copied ? "Copiado!" : label}
      aria-label={`${label} ${value}`}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        {copied ? (
          <path
            d="m5 13 4 4 10-10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : (
          <>
            <rect
              x="9"
              y="9"
              width="11"
              height="11"
              rx="2.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            />
            <path
              d="M15 5.5A2.5 2.5 0 0 0 12.5 3h-7A2.5 2.5 0 0 0 3 5.5v7A2.5 2.5 0 0 0 5.5 15"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </>
        )}
      </svg>
      <span className="pcp-pub__copy-feedback" aria-live="polite">
        {copied ? "Copiado" : ""}
      </span>
    </button>
  );
}

async function copyToClipboard(value: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    // Tablet de chão de fábrica em HTTP não tem Clipboard API (contexto inseguro).
    return legacyCopy(value);
  }
}

function legacyCopy(value: string): boolean {
  const field = document.createElement("textarea");
  field.value = value;
  field.setAttribute("readonly", "");
  field.style.position = "fixed";
  field.style.opacity = "0";
  document.body.appendChild(field);
  field.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(field);
  return ok;
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

/** Data curta para eixo de gráficos (ex.: 04/09). */
export function formatDateShort(value: string | null): string {
  if (!value) return "—";
  const [, month, day] = value.slice(0, 10).split("-");
  if (!month || !day) return value;
  return `${day}/${month}`;
}

export function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

export function formatHours(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} h`;
}

/** Meta de eficiência do posto (chão de fábrica). */
export const EFFICIENCY_GOAL_PCT = 92;

/** Verde ≥ meta; âmbar até ~5% abaixo; vermelho mais abaixo. */
export function efficiencyTone(value: number | null | undefined): "good" | "warn" | "bad" | "none" {
  if (value === null || value === undefined || !Number.isFinite(value)) return "none";
  if (value >= EFFICIENCY_GOAL_PCT) return "good";
  if (value >= EFFICIENCY_GOAL_PCT * 0.95) return "warn";
  return "bad";
}
