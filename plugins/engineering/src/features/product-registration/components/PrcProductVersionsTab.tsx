/** U3 — aba Versões do produto acompanhado: timeline Vn→V1 (entradas
 * expansíveis, aria-expanded, teclado/touch) + comparação técnica
 * Vx×Vy calculada pela Engineering API (nunca diff local de JSON). */

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ExternalLink, FileText } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringLoadingActivityCard,
  EngineeringSelectField,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  fetchPrcComparison,
  fetchPrcRevisions,
  type PrcComparisonResult,
  type PrcRecordFlagEvent,
  type PrcRevisionChange,
  type PrcRevisionSummary,
} from "../api/productRegistrationApi";
import {
  navigatePrc,
  prcProductHref,
  navigatePrcHref,
  PRC_PATHS,
} from "../prcNavigate";
import {
  PRC_ENUM_OPTION_LABELS,
  PRC_PRODUCTS_COPY,
  PRC_SUPPLIER_LABELS,
  prcFieldLabel,
  prcShortId,
} from "../prcCopy";

function scalarText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return "Não disponível";
  return String(value);
}

function changeValueText(path: string, value: unknown): string {
  const raw = scalarText(value);
  if (raw === "—") return raw;
  const head = path.split(".")[0];
  return PRC_ENUM_OPTION_LABELS[head]?.[raw] ?? raw;
}

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

const FLAG_EVENT_LABELS: Record<string, string> = {
  "flag.created": "Bandeira criada",
  "flag.updated": "Bandeira editada",
  "flag.resolved": "Bandeira resolvida",
  "flag.removed": "Bandeira removida",
};

/** Vínculo adicionado/removido traz o link inteiro em before/after —
 * render compacto (PN · Catálogo) em vez de «Não disponível». */
function linkText(value: unknown): string {
  if (!value || typeof value !== "object") return scalarText(value);
  const link = value as Record<string, unknown>;
  const pn = scalarText(link.partNumber);
  const cat = scalarText(link.catalogNumber);
  return `PN ${pn} · Cat ${cat}`;
}

function supplierChangeText(c: PrcRevisionChange): string {
  const key = c.path.replace(/^suppliers\[|\].*$/g, "");
  const [code, store] = key.split("|");
  const who = code ? `${code} / ${store || "?"}` : key;
  if (c.linkState === "added") {
    return `${PRC_PRODUCTS_COPY.supplierLinkAdded} — ${who}`;
  }
  if (c.linkState === "removed") {
    return `${PRC_PRODUCTS_COPY.supplierLinkRemoved} — ${who}`;
  }
  const attr = c.path.split(".").slice(1).join(".");
  const attrLabel = PRC_SUPPLIER_LABELS[attr] || attr;
  return `${who} — ${attrLabel}: ${scalarText(c.before)} → ${scalarText(c.after)}`;
}

export function PrcProductVersionsTab({
  recordId,
  basePath,
  currentRevisionNumber,
}: {
  recordId: string;
  basePath: string;
  currentRevisionNumber: number;
}) {
  const [revisions, setRevisions] = useState<PrcRevisionSummary[] | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [fromRev, setFromRev] = useState<number | "">("");
  const [toRev, setToRev] = useState<number | "">("");
  const [comparison, setComparison] =
    useState<PrcComparisonResult | null>(null);
  const [compareBusy, setCompareBusy] = useState(false);
  const [compareError, setCompareError] = useState("");

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError("");
    try {
      const env = await fetchPrcRevisions(recordId, signal);
      setRevisions(env.data.items || []);
    } catch (e) {
      setError(
        e instanceof HomeApiError
          ? e.message
          : "Não foi possível carregar as versões.",
      );
      setRevisions(null);
    } finally {
      setLoading(false);
    }
  }, [recordId]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const ordered = useMemo(
    () =>
      (revisions || [])
        .slice()
        .sort((a, b) => b.revisionNumber - a.revisionNumber),
    [revisions],
  );

  const revOptions = useMemo(
    () =>
      ordered.map((r) => ({
        value: String(r.revisionNumber),
        label: `V${r.revisionNumber}`,
      })),
    [ordered],
  );

  const toggle = useCallback((n: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });
  }, []);

  const runCompare = useCallback(async () => {
    if (!fromRev || !toRev || fromRev === toRev) return;
    setCompareBusy(true);
    setCompareError("");
    try {
      const env = await fetchPrcComparison(
        recordId,
        Number(fromRev),
        Number(toRev),
      );
      setComparison(env.data);
    } catch (e) {
      setComparison(null);
      setCompareError(
        e instanceof HomeApiError
          ? e.message
          : "Não foi possível comparar as versões.",
      );
    } finally {
      setCompareBusy(false);
    }
  }, [recordId, fromRev, toRev]);

  if (loading && !revisions) {
    return (
      <EngineeringLoadingActivityCard
        title="Carregando versões"
        description="Consultando o histórico técnico do produto."
      />
    );
  }
  if (error) {
    return (
      <>
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
        <EngineeringActionButton variant="primary" onClick={() => void load()}>
          Tentar novamente
        </EngineeringActionButton>
      </>
    );
  }
  if (!ordered.length) return null;

  return (
    <div className="engineering-prc__versions">
      {/* 1 — Histórico de versões (timeline vertical Vn→V1) */}
      <EngineeringDetailCard
        title={PRC_PRODUCTS_COPY.versionsTimelineTitle}
        hint="Versões técnicas confirmadas pela Engineering API — a mais recente é a acompanhada, não o estado ao vivo do TOTVS."
      >
        <ol
          className="engineering-prc__vtimeline"
          aria-label="Histórico de versões do produto"
        >
          {ordered.map((rev) => {
            const isCurrent =
              rev.revisionNumber === currentRevisionNumber;
            const isV1 = rev.revisionNumber === 1;
            const open = expanded.has(rev.revisionNumber);
            const changed = rev.changedPaths || [];
            return (
              <li
                key={rev.revisionNumber}
                className="engineering-prc__vtimeline-item"
              >
                <div className="engineering-prc__vtimeline-marker">
                  <span className="engineering-prc__vtimeline-badge">
                    V{rev.revisionNumber}
                  </span>
                </div>
                <div className="engineering-prc__vtimeline-body">
                  <button
                    type="button"
                    className="engineering-prc__vtimeline-toggle"
                    aria-expanded={open}
                    aria-controls={`prc-vdetail-${rev.revisionNumber}`}
                    onClick={() => toggle(rev.revisionNumber)}
                  >
                    <span className="engineering-prc__vtimeline-title">
                      {isCurrent
                        ? PRC_PRODUCTS_COPY.versionCurrent
                        : isV1
                          ? PRC_PRODUCTS_COPY.versionFirst
                          : `Versão ${rev.revisionNumber}`}
                    </span>
                    <span className="engineering-prc__muted">
                      {formatWhen(rev.approvedAt)}
                    </span>
                    <ChevronDown
                      size={14}
                      aria-hidden
                      className={
                        open
                          ? "engineering-prc__vtimeline-chevron engineering-prc__vtimeline-chevron--open"
                          : "engineering-prc__vtimeline-chevron"
                      }
                    />
                  </button>
                  <div
                    id={`prc-vdetail-${rev.revisionNumber}`}
                    hidden={!open}
                    className="engineering-prc__vtimeline-detail"
                  >
                    <p>
                      <strong>Resumo:</strong>{" "}
                      {changed.length
                        ? `${changed.length} campo(s)/vínculo(s) alterado(s)`
                        : "Sem resumo de alterações"}
                    </p>
                    {changed.length ? (
                      <ul>
                        {changed.map((path) => (
                          <li key={path}>{prcFieldLabel(path)}</li>
                        ))}
                      </ul>
                    ) : null}
                    <p>
                      <strong>Solicitação de origem:</strong>{" "}
                      {rev.requestId ? (
                        <EngineeringActionButton
                          variant="ghost"
                          title={PRC_PRODUCTS_COPY.openOriginRequest}
                          onClick={() =>
                            navigatePrc(
                              PRC_PATHS.detail(rev.requestId),
                              basePath,
                            )
                          }
                        >
                          <ExternalLink size={13} aria-hidden />{" "}
                          {prcShortId(rev.requestId)}
                        </EngineeringActionButton>
                      ) : (
                        "—"
                      )}
                    </p>
                    <p>
                      <EngineeringActionButton
                        variant="ghost"
                        onClick={() =>
                          navigatePrcHref(
                            prcProductHref(basePath, recordId, {
                              rev:
                                rev.revisionNumber ===
                                currentRevisionNumber
                                  ? null
                                  : rev.revisionNumber,
                            }),
                            { replace: false },
                          )
                        }
                      >
                        <FileText size={13} aria-hidden />{" "}
                        {PRC_PRODUCTS_COPY.viewSheetOfVersion}
                      </EngineeringActionButton>
                    </p>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </EngineeringDetailCard>

      {/* 2 — Comparar versões (diff calculado pela Engineering API) */}
      <EngineeringDetailCard
        title={PRC_PRODUCTS_COPY.versionsCompareTitle}
        hint="Diferenças técnicas reais entre duas versões — cálculo autoritativo da Engineering API."
      >
        {ordered.length < 2 ? (
          <p className="engineering-prc__muted">
            {PRC_PRODUCTS_COPY.compareEmpty}
          </p>
        ) : (
          <>
            <div className="engineering-prc__compare-controls">
              <EngineeringSelectField
                id="prc-compare-from"
                label={PRC_PRODUCTS_COPY.compareFrom}
                value={String(fromRev)}
                onChange={(v) => setFromRev(v ? Number(v) : "")}
                options={[
                  { value: "", label: "Selecione" },
                  ...revOptions,
                ]}
              />
              <EngineeringSelectField
                id="prc-compare-to"
                label={PRC_PRODUCTS_COPY.compareTo}
                value={String(toRev)}
                onChange={(v) => setToRev(v ? Number(v) : "")}
                options={[
                  { value: "", label: "Selecione" },
                  ...revOptions,
                ]}
              />
              <EngineeringActionButton
                variant="primary"
                softDisabled={
                  compareBusy || !fromRev || !toRev || fromRev === toRev
                }
                title={
                  fromRev && toRev && fromRev === toRev
                    ? PRC_PRODUCTS_COPY.compareSameError
                    : undefined
                }
                onClick={() => void runCompare()}
              >
                {PRC_PRODUCTS_COPY.compareCta}
              </EngineeringActionButton>
            </div>
            {fromRev && toRev && fromRev === toRev ? (
              <p className="engineering-prc__muted" role="status">
                {PRC_PRODUCTS_COPY.compareSameError}
              </p>
            ) : null}
            {compareError ? (
              <EngineeringStateBanner variant="error">
                {compareError}
              </EngineeringStateBanner>
            ) : null}
            {comparison ? (
              <ComparisonResult result={comparison} />
            ) : null}
          </>
        )}
      </EngineeringDetailCard>
    </div>
  );
}

function ComparisonResult({ result }: { result: PrcComparisonResult }) {
  const hasField = result.fieldChanges.length > 0;
  const hasLinks = result.supplierLinkChanges.length > 0;
  return (
    <div
      className="engineering-prc__compare-result"
      aria-live="polite"
      aria-label={`Comparação V${result.from.revisionNumber} por V${result.to.revisionNumber}`}
    >
      <p className="engineering-prc__muted">
        V{result.from.revisionNumber} ({formatWhen(result.from.approvedAt)}
        ) × V{result.to.revisionNumber} (
        {formatWhen(result.to.approvedAt)})
      </p>

      {!result.comparable ? (
        <EngineeringStateBanner variant="default">
          {PRC_PRODUCTS_COPY.compareIncomparable}
        </EngineeringStateBanner>
      ) : !hasField && !hasLinks ? (
        <p className="engineering-prc__muted">
          {PRC_PRODUCTS_COPY.compareNoDiff}
        </p>
      ) : (
        <table className="engineering-prc__compare-table">
          <thead>
            <tr>
              <th scope="col">Campo</th>
              <th scope="col">
                {PRC_PRODUCTS_COPY.compareBefore} (V
                {result.from.revisionNumber})
              </th>
              <th scope="col">
                {PRC_PRODUCTS_COPY.compareAfter} (V
                {result.to.revisionNumber})
              </th>
            </tr>
          </thead>
          <tbody>
            {result.fieldChanges.map((c) => (
              <tr key={c.path}>
                <th scope="row">{prcFieldLabel(c.path)}</th>
                <td>{changeValueText(c.path, c.before)}</td>
                <td>{changeValueText(c.path, c.after)}</td>
              </tr>
            ))}
            {result.supplierLinkChanges.map((c) => (
              <tr key={c.path}>
                <th scope="row">{supplierChangeText(c)}</th>
                <td>{linkText(c.before)}</td>
                <td>{linkText(c.after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {result.flagEvents.length ? (
        <section
          className="engineering-prc__compare-flags"
          aria-label={PRC_PRODUCTS_COPY.compareFlagEventsTitle}
        >
          <h4>{PRC_PRODUCTS_COPY.compareFlagEventsTitle}</h4>
          <ul>
            {result.flagEvents.map((e: PrcRecordFlagEvent) => (
              <li key={e.id}>
                <strong>
                  {FLAG_EVENT_LABELS[e.eventType] || e.eventType}
                </strong>{" "}
                · V{e.revisionNumber} · {formatWhen(e.occurredAt)}
                {e.note ? ` — ${e.note}` : ""}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
