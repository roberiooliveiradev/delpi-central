import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { fetchPublicDrawingPdf, type MachineLoadOperation } from "./api";

/** Faixa de marca fixa no topo — identidade DELPI e posto em destaque para leitura à distância. */
export function BrandBar({
  eyebrow,
  title,
  code,
  stats,
  actions,
  lead,
}: {
  eyebrow: string;
  title: string;
  code?: string | null;
  stats?: ReactNode;
  actions?: ReactNode;
  lead?: ReactNode;
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
            <p className="pcp-pub__eyebrow">{eyebrow}</p>
            <div className="pcp-pub__title-row">
              {code ? <span className="pcp-pub__code">{code}</span> : null}
              <h1>{title}</h1>
            </div>
            {stats ? <div className="pcp-pub__stats">{stats}</div> : null}
          </div>
        </div>
        {actions ? <div className="pcp-pub__actions">{actions}</div> : null}
      </div>
    </header>
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
        setMessage(err instanceof Error ? err.message : "Desenho não encontrado para este PA.");
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [token, branch, paCode]);

  return { status, message, objectUrl };
}

export function DrawingViewer({
  token,
  branch,
  paCode,
  onClose,
}: {
  token: string;
  branch: string;
  paCode: string;
  onClose: () => void;
}) {
  const { status, message, objectUrl } = useDrawingObjectUrl(token, branch, paCode);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="pcp-pub-viewer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-viewer-title"
    >
      <div className="pcp-pub-viewer__bar">
        <h2 id="pcp-pub-viewer-title">Desenho {paCode}</h2>
        <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
          Fechar
        </button>
      </div>
      {status === "loading" ? <p className="pcp-pub-viewer__state">Carregando desenho…</p> : null}
      {status === "error" ? (
        <p className="pcp-pub-viewer__state pcp-pub-viewer__state--error">{message}</p>
      ) : null}
      {status === "ready" && objectUrl ? (
        <iframe className="pcp-pub-viewer__frame" title={`Desenho ${paCode}`} src={objectUrl} />
      ) : null}
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

export type StatusView = {
  tone: "running" | "done" | "queued";
  label: string;
  operatorNote: string | null;
};

export function resolveStatus(operation: MachineLoadOperation): StatusView {
  const operator = operation.active_operator_name?.trim() || null;
  if (operation.is_in_production || operation.production_status === "in_progress") {
    return {
      tone: "running",
      label: "Em produção",
      operatorNote: operator
        ? `Operador ${operator}${
            operation.production_started_time ? ` · desde ${operation.production_started_time}` : ""
          }`
        : null,
    };
  }
  if (operation.production_status === "started") {
    return {
      tone: "done",
      label: "Já apontada",
      operatorNote: operator ? `Último apontamento: ${operator}` : null,
    };
  }
  return { tone: "queued", label: "Na fila", operatorNote: null };
}

/** Chave estável de uma operação na fila — usada como id de navegação e como key do React. */
export function operationKey(operation: MachineLoadOperation): string {
  return `${operation.production_order}::${operation.operation_code}`;
}

export function formatQty(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

/** Unidade de chão de fábrica: TOTVS envia MI (milheiro); o operador lê como peça. */
export function formatUnit(unit: string | null): string {
  const cleaned = (unit ?? "").trim();
  if (!cleaned || cleaned.toUpperCase() === "MI") return "PÇ";
  return cleaned;
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
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

/** Mesma leitura de faixa do MFE de eficiência fabril: verde ≥95, âmbar ≥80, vermelho abaixo. */
export function efficiencyTone(value: number | null | undefined): "good" | "warn" | "bad" | "none" {
  if (value === null || value === undefined || !Number.isFinite(value)) return "none";
  if (value >= 95) return "good";
  if (value >= 80) return "warn";
  return "bad";
}
