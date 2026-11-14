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
  PRC_FIELD_GROUP_BY_PATH,
  PRC_FIELD_GROUPS,
} from "@delpi/plugin-ui/index";
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
import {
  diffCellState,
  summarizeChangedPaths,
  supplierLinkIdentity,
} from "../prcSnapshot";

function scalarText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return "Não disponível";
  return String(value);
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
  const id = supplierLinkIdentity(c.path);
  const who = id
    ? `Fornecedor ${id.supplierCode} / Loja ${id.store || "?"}`
    : c.path;
  if (c.linkState === "added") {
    return `${PRC_PRODUCTS_COPY.supplierLinkAdded} — ${who}`;
  }
  if (c.linkState === "removed") {
    return `${PRC_PRODUCTS_COPY.supplierLinkRemoved} — ${who}`;
  }
  const attrLabel = PRC_SUPPLIER_LABELS[id?.attribute || ""] ||
    id?.attribute || "";
  return `${who} — ${attrLabel}`;
}

/** Célula Antes/Depois honesta — «não observado» ≠ nulo/vazio
 * registrado (UX-P0-02, presença vem do diff server-side). */
function DiffCell({
  change,
  side,
  rev,
}: {
  change: PrcRevisionChange;
  side: "before" | "after";
  rev: number;
}) {
  const state = diffCellState(change, side);
  if (state.kind === "not_observed") {
    return (
      <span className="engineering-prc__muted" title={
        PRC_PRODUCTS_COPY.compareNotObservedHint
      }>
        {PRC_PRODUCTS_COPY.compareNotObserved} (V{rev})
      </span>
    );
  }
  if (state.kind === "empty") {
    return <span className="engineering-prc__muted">—</span>;
  }
  const head = change.path.split(".")[0];
  return (
    <>{PRC_ENUM_OPTION_LABELS[head]?.[state.text] ?? state.text}</>
  );
}

/** `suppliers[k]` inteiro (link added/removed) → render compacto;
 * attr-level `suppliers[k].attr` → célula presença-ciente. */
function SupplierDiffCell({
  change,
  side,
  rev,
}: {
  change: PrcRevisionChange;
  side: "before" | "after";
  rev: number;
}) {
  if (change.linkState === "added" || change.linkState === "removed") {
    const value = side === "before" ? change.before : change.after;
    const flag =
      side === "before" ? change.beforePresent : change.afterPresent;
    if (flag === false || value == null) {
      return <span className="engineering-prc__muted">—</span>;
    }
    return <>{linkText(value)}</>;
  }
  return <DiffCell change={change} side={side} rev={rev} />;
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
          {ordered.map((rev) => (
            <VersionEntry
              key={rev.revisionNumber}
              rev={rev}
              recordId={recordId}
              basePath={basePath}
              currentRevisionNumber={currentRevisionNumber}
              open={expanded.has(rev.revisionNumber)}
              onToggle={() => toggle(rev.revisionNumber)}
            />
          ))}
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

/** Entrada da timeline — identidade, data e resumo conciso sempre
 * visíveis; detalhe agrupado por seção só no expandir (UX-P1-05). */
function VersionEntry({
  rev,
  recordId,
  basePath,
  currentRevisionNumber,
  open,
  onToggle,
}: {
  rev: PrcRevisionSummary;
  recordId: string;
  basePath: string;
  currentRevisionNumber: number;
  open: boolean;
  onToggle: () => void;
}) {
  const isCurrent = rev.revisionNumber === currentRevisionNumber;
  const isV1 = rev.revisionNumber === 1;
  const { fieldPaths, supplierPaths } = summarizeChangedPaths(
    rev.changedPaths,
  );
  const total = fieldPaths.length + supplierPaths.length;
  const previewNames = [
    ...fieldPaths.map((p) => prcFieldLabel(p)),
    ...supplierPaths.map((p) => {
      const id = supplierLinkIdentity(p);
      return id
        ? `Fornecedor ${id.supplierCode} / Loja ${id.store || "?"}`
        : p;
    }),
  ];
  const preview = previewNames.slice(0, 3);
  const extra = previewNames.length - preview.length;

  /* Campos agrupados na ordem canônica da ficha; sem grupo →
   * «Outros campos». O(≤ ~20 paths), sem memoização. */
  const byTitle = new Map<string, string[]>();
  for (const g of PRC_FIELD_GROUPS) byTitle.set(g.title, []);
  const otherTitle = PRC_PRODUCTS_COPY.compareFieldsGroupFallback;
  for (const p of fieldPaths) {
    const title = PRC_FIELD_GROUP_BY_PATH[p] || otherTitle;
    let bucket = byTitle.get(title);
    if (!bucket) {
      bucket = [];
      byTitle.set(title, bucket);
    }
    bucket.push(p);
  }
  const groupedFields = [...byTitle.entries()]
    .filter(([, paths]) => paths.length)
    .map(([title, paths]) => ({ title, paths }));

  return (
    <li className="engineering-prc__vtimeline-item">
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
          onClick={onToggle}
        >
          <span className="engineering-prc__vtimeline-headline">
            <span className="engineering-prc__vtimeline-title">
              {isCurrent
                ? `V${rev.revisionNumber} · ${PRC_PRODUCTS_COPY.versionCurrent}`
                : isV1
                  ? `V${rev.revisionNumber} · ${PRC_PRODUCTS_COPY.versionFirst}`
                  : `V${rev.revisionNumber}`}
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
          </span>
          <span className="engineering-prc__vtimeline-summary">
            {total
              ? `${total} ${PRC_PRODUCTS_COPY.changesReported}`
              : PRC_PRODUCTS_COPY.changesNone}
          </span>
          {preview.length ? (
            <span className="engineering-prc__vtimeline-preview">
              {preview.join(", ")}
              {extra > 0
                ? ` ${PRC_PRODUCTS_COPY.andMore} ${extra}`
                : ""}
            </span>
          ) : null}
        </button>
        <div
          id={`prc-vdetail-${rev.revisionNumber}`}
          hidden={!open}
          className="engineering-prc__vtimeline-detail"
        >
          {groupedFields.map((group) => (
            <div key={group.title}>
              <p className="engineering-prc__vtimeline-group">
                {group.title}
              </p>
              <ul>
                {group.paths.map((path) => (
                  <li key={path}>{prcFieldLabel(path)}</li>
                ))}
              </ul>
            </div>
          ))}
          {supplierPaths.length ? (
            <div>
              <p className="engineering-prc__vtimeline-group">
                {PRC_PRODUCTS_COPY.compareSuppliersGroup}
              </p>
              <ul>
                {supplierPaths.map((path) => {
                  const id = supplierLinkIdentity(path);
                  return (
                    <li key={path}>
                      {id
                        ? `Fornecedor ${id.supplierCode} / Loja ${id.store || "?"}${id.attribute ? ` — ${PRC_SUPPLIER_LABELS[id.attribute] || id.attribute}` : ""}`
                        : path}
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}
          <p>
            <strong>Solicitação de origem:</strong>{" "}
            {rev.requestId ? (
              <EngineeringActionButton
                variant="ghost"
                title={`${PRC_PRODUCTS_COPY.openOriginRequest} — ${rev.requestId}`}
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
                      rev.revisionNumber === currentRevisionNumber
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
}

function ComparisonResult({ result }: { result: PrcComparisonResult }) {
  const hasField = result.fieldChanges.length > 0;
  const hasLinks = result.supplierLinkChanges.length > 0;

  /* Campos agrupados na ordem canônica da ficha — «Outros campos»
   * para paths fora do catálogo (UX-P1-06). */
  const byTitle = new Map<string, PrcRevisionChange[]>();
  for (const g of PRC_FIELD_GROUPS) byTitle.set(g.title, []);
  const otherTitle = PRC_PRODUCTS_COPY.compareFieldsGroupFallback;
  for (const c of result.fieldChanges) {
    const title = PRC_FIELD_GROUP_BY_PATH[c.path] || otherTitle;
    let bucket = byTitle.get(title);
    if (!bucket) {
      bucket = [];
      byTitle.set(title, bucket);
    }
    bucket.push(c);
  }
  const fieldGroups = [...byTitle.entries()].filter(
    ([, items]) => items.length,
  );

  const hasNotObserved = result.changes.some(
    (c) => c.beforePresent === false || c.afterPresent === false,
  );

  const header = (
    <>
      <th scope="col">Campo</th>
      <th scope="col">
        {PRC_PRODUCTS_COPY.compareBefore} (V{result.from.revisionNumber})
      </th>
      <th scope="col">
        {PRC_PRODUCTS_COPY.compareAfter} (V{result.to.revisionNumber})
      </th>
    </>
  );

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
        <>
          {hasNotObserved ? (
            <p className="engineering-prc__compare-legend">
              {PRC_PRODUCTS_COPY.compareNotObservedHint}
            </p>
          ) : null}
          {fieldGroups.map(([title, items]) => (
            <section
              key={title}
              className="engineering-prc__compare-group"
              aria-label={title}
            >
              <h4>{title}</h4>
              <table className="engineering-prc__compare-table">
                <thead>
                  <tr>{header}</tr>
                </thead>
                <tbody>
                  {items.map((c) => (
                    <tr key={c.path}>
                      <th scope="row">{prcFieldLabel(c.path)}</th>
                      <td>
                        <DiffCell
                          change={c}
                          side="before"
                          rev={result.from.revisionNumber}
                        />
                      </td>
                      <td>
                        <DiffCell
                          change={c}
                          side="after"
                          rev={result.to.revisionNumber}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ))}
          {hasLinks ? (
            <section
              className="engineering-prc__compare-group"
              aria-label={PRC_PRODUCTS_COPY.compareSuppliersGroup}
            >
              <h4>{PRC_PRODUCTS_COPY.compareSuppliersGroup}</h4>
              <table className="engineering-prc__compare-table">
                <thead>
                  <tr>{header}</tr>
                </thead>
                <tbody>
                  {result.supplierLinkChanges.map((c) => (
                    <tr key={c.path}>
                      <th scope="row">{supplierChangeText(c)}</th>
                      <td>
                        <SupplierDiffCell
                          change={c}
                          side="before"
                          rev={result.from.revisionNumber}
                        />
                      </td>
                      <td>
                        <SupplierDiffCell
                          change={c}
                          side="after"
                          rev={result.to.revisionNumber}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}
        </>
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
