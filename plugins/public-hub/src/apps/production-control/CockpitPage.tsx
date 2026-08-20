import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  fetchPublicDrawingPdf,
  fetchPublicMachineLoad,
  type MachineLoadOperation,
  type MachineLoadWorkCenter,
  type PublicMachineLoadPayload,
} from "./api";
import { usePublicMachineLoadRealtime } from "./usePublicMachineLoadRealtime";
import "./cockpit.css";

const POLLING_FALLBACK_MS = 90_000;
const STORAGE_PREFIX = "delpi.pcp.cockpit.work-center";

type Props = {
  token: string;
  branch: string;
  initial: PublicMachineLoadPayload;
};

function storageKey(branch: string): string {
  return `${STORAGE_PREFIX}.${branch}`;
}

function readStoredWorkCenter(branch: string): string | null {
  try {
    return window.localStorage.getItem(storageKey(branch));
  } catch {
    return null;
  }
}

function storeWorkCenter(branch: string, workCenter: string | null): void {
  try {
    if (workCenter) window.localStorage.setItem(storageKey(branch), workCenter);
    else window.localStorage.removeItem(storageKey(branch));
  } catch {
    /* modo privado sem storage: a escolha vale só para esta sessão */
  }
}

export function OperatorCockpit({ token, branch, initial }: Props) {
  const [payload, setPayload] = useState<PublicMachineLoadPayload>(initial);
  const [workCenter, setWorkCenter] = useState<string | null>(() => {
    const stored = readStoredWorkCenter(branch);
    const exists = initial.work_centers.some((item) => item.work_center === stored);
    return stored && exists ? stored : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date>(() => new Date());
  const [drawingPa, setDrawingPa] = useState<string | null>(null);
  const workCenterRef = useRef(workCenter);
  workCenterRef.current = workCenter;

  const reload = useCallback(
    async (center: string | null) => {
      setLoading(true);
      try {
        const next = await fetchPublicMachineLoad(token, branch, center);
        setPayload(next);
        setUpdatedAt(new Date());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Não foi possível atualizar a fila.");
      } finally {
        setLoading(false);
      }
    },
    [token, branch],
  );

  useEffect(() => {
    if (!workCenter || payload.selected.work_center === workCenter) return;
    void reload(workCenter);
  }, [workCenter, payload.selected.work_center, reload]);

  const connected = usePublicMachineLoadRealtime({
    token,
    branch,
    onChanged: useCallback(() => {
      void reload(workCenterRef.current);
    }, [reload]),
  });

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void reload(workCenterRef.current);
    }, POLLING_FALLBACK_MS);
    return () => window.clearInterval(timer);
  }, [reload]);

  const selectWorkCenter = (center: string) => {
    storeWorkCenter(branch, center);
    setWorkCenter(center);
  };

  const clearWorkCenter = () => {
    storeWorkCenter(branch, null);
    setWorkCenter(null);
  };

  if (!workCenter) {
    return (
      <WorkCenterPicker
        branch={branch}
        workCenters={payload.work_centers}
        onSelect={selectWorkCenter}
      />
    );
  }

  const activeCenter = payload.work_centers.find((item) => item.work_center === workCenter);
  const items = payload.selected.work_center === workCenter ? payload.selected.items : [];

  return (
    <section className="pcp-pub">
      <header className="pcp-pub__header">
        <div className="pcp-pub__identity">
          <p className="pcp-pub__eyebrow">Fila de produção · Filial {branch}</p>
          <h1>{activeCenter?.work_center_name || workCenter}</h1>
          <p className="pcp-pub__meta">
            Posto {workCenter} · {items.length} {items.length === 1 ? "operação" : "operações"}
            {activeCenter?.in_production_count
              ? ` · ${activeCenter.in_production_count} em produção`
              : ""}
          </p>
        </div>
        <div className="pcp-pub__actions">
          <span
            className={`pcp-pub__live ${connected ? "pcp-pub__live--on" : "pcp-pub__live--off"}`}
            title={
              connected
                ? "Conectado: a fila atualiza sozinha quando o PCP altera."
                : "Sem conexão ao vivo: atualizando periodicamente."
            }
          >
            <span className="pcp-pub__live-dot" aria-hidden="true" />
            {connected ? "Ao vivo" : "Reconectando"}
          </span>
          <button type="button" className="pcp-pub__ghost" onClick={clearWorkCenter}>
            Trocar posto
          </button>
        </div>
      </header>

      <p className="pcp-pub__notice">
        Sequência definida pelo PCP — esta tela é somente leitura e atualiza automaticamente.
      </p>

      {error ? <p className="pcp-pub__error">{error}</p> : null}

      {items.length === 0 ? (
        <p className="pcp-pub__empty">
          {loading ? "Carregando fila…" : "Nenhuma operação programada para este posto."}
        </p>
      ) : (
        <ol className="pcp-pub__queue">
          {items.map((item, index) => (
            <OperationCard
              key={`${item.production_order}::${item.operation_code}`}
              position={index + 1}
              operation={item}
              onOpenDrawing={setDrawingPa}
            />
          ))}
        </ol>
      )}

      <footer className="pcp-pub__footer">
        <span>
          Atualizado às{" "}
          {updatedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
        </span>
        {payload.snapshot.refreshed_at ? (
          <span>Fila publicada em {formatDateTime(payload.snapshot.refreshed_at)}</span>
        ) : null}
      </footer>

      {drawingPa ? (
        <DrawingViewer
          token={token}
          branch={branch}
          paCode={drawingPa}
          onClose={() => setDrawingPa(null)}
        />
      ) : null}
    </section>
  );
}

type PickerProps = {
  branch: string;
  workCenters: MachineLoadWorkCenter[];
  onSelect: (workCenter: string) => void;
};

function WorkCenterPicker({ branch, workCenters, onSelect }: PickerProps) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return workCenters;
    return workCenters.filter(
      (item) =>
        item.work_center.toLowerCase().includes(term) ||
        item.work_center_name.toLowerCase().includes(term),
    );
  }, [workCenters, query]);

  return (
    <section className="pcp-pub pcp-pub--picker">
      <header className="pcp-pub__header pcp-pub__header--picker">
        <div className="pcp-pub__identity">
          <p className="pcp-pub__eyebrow">Filial {branch}</p>
          <h1>Escolha o seu posto de trabalho</h1>
          <p className="pcp-pub__meta">
            A escolha fica salva neste aparelho; você pode trocar depois pelo cabeçalho.
          </p>
        </div>
      </header>

      {workCenters.length > 8 ? (
        <input
          className="pcp-pub__search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar posto ou máquina…"
          aria-label="Buscar posto de trabalho"
        />
      ) : null}

      {filtered.length === 0 ? (
        <p className="pcp-pub__empty">Nenhum posto encontrado.</p>
      ) : (
        <div className="pcp-pub__centers">
          {filtered.map((item) => (
            <button
              key={item.work_center}
              type="button"
              className="pcp-pub__center"
              onClick={() => onSelect(item.work_center)}
            >
              <span className="pcp-pub__center-code">{item.work_center}</span>
              <span className="pcp-pub__center-name">{item.work_center_name}</span>
              <span className="pcp-pub__center-meta">
                {item.operation_count} {item.operation_count === 1 ? "operação" : "operações"}
                {item.in_production_count ? ` · ${item.in_production_count} em produção` : ""}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function OperationCard({
  position,
  operation,
  onOpenDrawing,
}: {
  position: number;
  operation: MachineLoadOperation;
  onOpenDrawing: (paCode: string) => void;
}) {
  const status = resolveStatus(operation);
  const paCode = operation.pa_product_code?.trim() || "";
  return (
    <li className={`pcp-pub__card pcp-pub__card--${status.tone}`}>
      <span className="pcp-pub__position" aria-label={`Posição ${position}`}>
        {position}
      </span>
      <div className="pcp-pub__card-body">
        <div className="pcp-pub__card-top">
          <span className="pcp-pub__order">
            <span className="pcp-pub__order-label">OP</span>
            <strong>{operation.production_order}</strong>
            <CopyValueButton value={operation.production_order} label="Copiar OP" />
          </span>
          <span className={`pcp-pub__badge pcp-pub__badge--${status.tone}`}>{status.label}</span>
        </div>

        <p className="pcp-pub__product">
          <strong>{operation.product_code}</strong> {operation.product_description}
        </p>

        <dl className="pcp-pub__facts">
          <Fact label="Operação">
            {operation.operation_code} · {operation.operation_description}
          </Fact>
          <Fact label="PA">{paCode || "—"}</Fact>
          <Fact label="Pendente">
            {formatQty(operation.pending_qty)} {formatUnit(operation.unit)}
          </Fact>
          <Fact label="Ferramenta">{operation.tool || "—"}</Fact>
          <Fact label="Programada">
            {formatDate(operation.scheduled_date)}
            {operation.scheduled_start_time ? ` · ${operation.scheduled_start_time}` : ""}
          </Fact>
          <Fact label="Entrega PA">{formatDate(operation.pa_due_date)}</Fact>
        </dl>

        {status.operatorNote ? (
          <p className="pcp-pub__operator">{status.operatorNote}</p>
        ) : null}

        {paCode ? (
          <button
            type="button"
            className="pcp-pub__drawing"
            onClick={() => onOpenDrawing(paCode)}
          >
            Ver desenho
          </button>
        ) : null}
      </div>
    </li>
  );
}

function DrawingViewer({
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
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
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

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="pcp-pub-viewer" role="dialog" aria-modal="true" aria-labelledby="pcp-pub-viewer-title">
      <div className="pcp-pub-viewer__bar">
        <h2 id="pcp-pub-viewer-title">Desenho {paCode}</h2>
        <button type="button" className="pcp-pub__ghost" onClick={onClose}>
          Fechar
        </button>
      </div>
      {status === "loading" ? <p className="pcp-pub-viewer__state">Carregando desenho…</p> : null}
      {status === "error" ? <p className="pcp-pub-viewer__state pcp-pub-viewer__state--error">{message}</p> : null}
      {status === "ready" && objectUrl ? (
        <iframe className="pcp-pub-viewer__frame" title={`Desenho ${paCode}`} src={objectUrl} />
      ) : null}
    </div>
  );
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="pcp-pub__fact">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function CopyValueButton({ value, label }: { value: string; label: string }) {
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
            <rect x="9" y="9" width="11" height="11" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
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

type StatusView = {
  tone: "running" | "done" | "queued";
  label: string;
  operatorNote: string | null;
};

function resolveStatus(operation: MachineLoadOperation): StatusView {
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

function formatQty(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

/** Unidade de chão de fábrica: TOTVS envia MI (milheiro); o operador lê como peça. */
function formatUnit(unit: string | null): string {
  const cleaned = (unit || "").trim().toUpperCase();
  if (!cleaned || cleaned === "MI") return "PÇ";
  return unit!.trim();
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
