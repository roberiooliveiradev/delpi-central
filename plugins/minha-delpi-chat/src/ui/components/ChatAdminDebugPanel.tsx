import { Bug } from "lucide-react";
import { useMemo, useState } from "react";
import "./ChatAdminDebugPanel.css";

type ChatAdminDebugPanelProps = {
  debug?: Record<string, unknown> | null;
};

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? "");
  }
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      className="mdc-chat-admin-debug__copy-btn"
      onClick={handleCopy}
      title="Copiar diagnóstico"
      type="button"
    >
      {copied ? "✓ Copiado" : "Copiar"}
    </button>
  );
}

function formatTimingMs(value: unknown): string | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }

  return `${Math.round(value)} ms`;
}

function AdminTimingsSummary({ intelligence }: { intelligence: Record<string, unknown> }) {
  const timings = intelligence.timings as Record<string, unknown> | undefined;

  if (!timings || typeof timings !== "object") {
    return null;
  }

  const entries = Object.entries(timings)
    .map(([key, value]) => {
      const label = formatTimingMs(value);

      if (!label) {
        return null;
      }

      return { key, label };
    })
    .filter(Boolean) as Array<{ key: string; label: string }>;

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Timings do pipeline">
      {entries.map((entry) => (
        <span key={entry.key} className="mdc-chat-admin-debug__timing-chip">
          <strong>{entry.key.replace(/_ms$/, "")}</strong> {entry.label}
        </span>
      ))}
    </div>
  );
}

function AdminIntentRouteSummary({ intentRoute }: { intentRoute: Record<string, unknown> }) {
  const intent = String(intentRoute.intent ?? "").trim();

  if (!intent) {
    return null;
  }

  const subIntent = String(intentRoute.subIntent ?? "").trim();
  const confidence =
    typeof intentRoute.confidence === "number" ? Math.round(intentRoute.confidence * 100) : null;

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Rota de intenção">
      <span className="mdc-chat-admin-debug__timing-chip">
        <strong>intenção</strong> {intent}
        {subIntent ? ` · ${subIntent}` : ""}
        {confidence !== null ? ` (${confidence}%)` : ""}
      </span>
      {intentRoute.requiresTool === true ? (
        <span className="mdc-chat-admin-debug__timing-chip">tools</span>
      ) : null}
      {intentRoute.requiresRag === true ? (
        <span className="mdc-chat-admin-debug__timing-chip">RAG</span>
      ) : null}
    </div>
  );
}

function AdminTrustSignalsSummary({ signals }: { signals: Array<Record<string, unknown>> }) {
  if (!signals.length) {
    return null;
  }

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Sinais de confiança">
      {signals.map((signal) => (
        <span
          key={String(signal.id ?? signal.label)}
          className="mdc-chat-admin-debug__timing-chip"
          title={String(signal.id ?? "")}
        >
          {String(signal.label ?? signal.id ?? "")}
        </span>
      ))}
    </div>
  );
}

type DrawingPhase = {
  id?: string;
  label?: string;
  status?: string;
  detail?: string;
};

function AdminDocumentVisionTraceSummary({
  trace,
}: {
  trace: Record<string, unknown>;
}) {
  const engine = trace.engine != null ? String(trace.engine) : "";
  const stages = Array.isArray(trace.stages) ? trace.stages.map(String).join(", ") : "";
  const score =
    trace.legibilityScore != null ? String(trace.legibilityScore) : "";
  const duration =
    trace.durationMs != null ? `${String(trace.durationMs)}ms` : "";
  const context = trace.context != null ? String(trace.context) : "";

  if (!engine && !stages) {
    return null;
  }

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Visão de documentos (admin)">
      {context ? (
        <span className="mdc-chat-admin-debug__timing-chip">
          <strong>visão</strong> {context}
        </span>
      ) : null}
      {engine ? (
        <span className="mdc-chat-admin-debug__timing-chip">
          <strong>motor</strong> {engine}
        </span>
      ) : null}
      {stages ? (
        <span className="mdc-chat-admin-debug__timing-chip" title={stages}>
          <strong>estágios</strong> {stages}
        </span>
      ) : null}
      {score ? (
        <span className="mdc-chat-admin-debug__timing-chip">
          <strong>legibilidade</strong> {score}
        </span>
      ) : null}
      {duration ? (
        <span className="mdc-chat-admin-debug__timing-chip">
          <strong>duração</strong> {duration}
        </span>
      ) : null}
    </div>
  );
}

function AdminDrawingAnalysisTraceSummary({
  trace,
}: {
  trace: Record<string, unknown>;
}) {
  const phases = Array.isArray(trace.phases) ? (trace.phases as DrawingPhase[]) : [];

  if (!phases.length) {
    return null;
  }

  const summary = trace.summary as Record<string, unknown> | undefined;
  const productCode = summary?.productCode != null ? String(summary.productCode) : "";

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Análise de desenho (admin)">
      {productCode ? (
        <span className="mdc-chat-admin-debug__timing-chip">
          <strong>desenho</strong> {productCode}
        </span>
      ) : null}
      {phases.map((phase) => {
        const status = String(phase.status ?? "skip");
        const warn = status === "warn" || status === "error" || status === "blocked";

        return (
          <span
            key={String(phase.id ?? phase.label)}
            className={
              warn
                ? "mdc-chat-admin-debug__timing-chip mdc-chat-admin-debug__assertiveness-chip--warn"
                : "mdc-chat-admin-debug__timing-chip"
            }
            title={String(phase.detail ?? "")}
          >
            <strong>{String(phase.label ?? phase.id ?? "fase")}</strong> {status}
          </span>
        );
      })}
    </div>
  );
}

function AdminContextAssertivenessSummary({
  assertiveness,
}: {
  assertiveness: Record<string, unknown>;
}) {
  const score = assertiveness.score;
  const flags = assertiveness.flags;

  if (typeof score !== "number") {
    return null;
  }

  const flagList = Array.isArray(flags) ? flags.filter((item) => typeof item === "string") : [];
  const lowScore = score < 70;

  return (
    <div className="mdc-chat-admin-debug__timings" aria-label="Assertividade contextual">
      <span
        className={
          lowScore
            ? "mdc-chat-admin-debug__timing-chip mdc-chat-admin-debug__assertiveness-chip--warn"
            : "mdc-chat-admin-debug__timing-chip"
        }
        title={lowScore ? "Score abaixo de 70 — revisar flags de contexto" : undefined}
      >
        <strong>assertividade</strong> {Math.round(score)}%
        {lowScore ? " ⚠" : ""}
      </span>
      {flagList.map((flag) => (
        <span key={flag} className="mdc-chat-admin-debug__timing-chip mdc-chat-admin-debug__flag-chip">
          {flag}
        </span>
      ))}
    </div>
  );
}

export function ChatAdminDebugPanel({ debug }: ChatAdminDebugPanelProps) {
  const json = useMemo(() => safeJson(debug ?? {}), [debug]);
  const intelligence = (debug?.intelligence as Record<string, unknown> | undefined) ?? null;
  const memory = (debug?.memory as Record<string, unknown> | undefined) ?? null;
  const contextAssertiveness =
    (debug?.contextAssertiveness as Record<string, unknown> | undefined) ?? null;
  const intentRoute = (debug?.intentRoute as Record<string, unknown> | undefined) ?? null;
  const drawingTrace =
    (debug?.drawingAnalysisTrace as Record<string, unknown> | undefined) ?? null;
  const documentVisionTrace =
    (debug?.documentVisionTrace as Record<string, unknown> | undefined) ?? null;
  const trustSignals = Array.isArray(debug?.trustSignals)
    ? (debug?.trustSignals as Array<Record<string, unknown>>)
    : [];
  const [open, setOpen] = useState(false);

  if (!debug) return null;

  return (
    <section className="mdc-chat-admin-debug" aria-label="Diagnóstico (admin)">
      <details
        className="mdc-chat-admin-debug__details"
        open={open}
        onToggle={(e) => {
          setOpen((e.currentTarget as HTMLDetailsElement).open);
        }}
      >
        <summary className="mdc-chat-admin-debug__open-btn" title="Ver diagnóstico">
          <Bug size={16} aria-hidden="true" />
          <span>Diagnóstico (admin)</span>
          <span className="mdc-chat-admin-debug__summary-hint">
            intenção · tools · RAG · anexo · desenho
          </span>
        </summary>

        <div className="mdc-chat-admin-debug__content">
          {intentRoute ? <AdminIntentRouteSummary intentRoute={intentRoute} /> : null}
          {documentVisionTrace ? (
            <AdminDocumentVisionTraceSummary trace={documentVisionTrace} />
          ) : null}
          {drawingTrace ? <AdminDrawingAnalysisTraceSummary trace={drawingTrace} /> : null}
          {trustSignals.length > 0 ? (
            <AdminTrustSignalsSummary signals={trustSignals} />
          ) : null}
          {intelligence ? <AdminTimingsSummary intelligence={intelligence} /> : null}
          {contextAssertiveness ? (
            <AdminContextAssertivenessSummary assertiveness={contextAssertiveness} />
          ) : null}
          {memory?.loaded ? (
            <div className="mdc-chat-admin-debug__timings" aria-label="Memória ativa">
              {Object.entries((memory.activeEntities as Record<string, unknown>) || {}).map(
                ([key, value]) => (
                  <span key={key} className="mdc-chat-admin-debug__timing-chip">
                    <strong>{key}</strong> {String(value)}
                  </span>
                ),
              )}
            </div>
          ) : null}
          <div className="mdc-chat-admin-debug__toolbar">
            <CopyButton value={json} />
          </div>

          <pre className="mdc-chat-admin-debug__body">{json}</pre>
        </div>
      </details>
    </section>
  );
}

