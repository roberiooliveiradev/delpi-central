import { useEffect, useMemo, useRef, useState } from "react";
import {
  createDataSourceBlock,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
  type DataTransform,
} from "@delpi/tv-dashboard-presentation";

import {
  createDataBuilderSession,
  dataBuilderTurn,
  listDataRoutes,
  materializeDataBuilderSession,
  previewDataBuilderSession,
  type BranchScope,
  type DataBuilderDraft,
  type DataBuilderMessage,
  type DataBuilderPreviewTable,
  type DataBuilderSession,
  type DataBuilderSuggestionCard,
  type TvDataRouteCatalogItem,
} from "../api/tvDashboardApi";
import { DATA_BUILDER_CHAT_CONTENT as C } from "../content/dataBuilderChatContent";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import { buildRouteDefaultParams } from "../utils/buildRouteDefaultParams";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { DataCatalogMode } from "./comunicadoEditorContextCore";
import { DataParamFields, type DataParamSchema, visibleParamSchema } from "./DataParamFields";
import { DeckField } from "./deck/DeckField";
import { BranchField } from "./BranchField";
import { NativeTextControl } from "@delpi/plugin-ui/index";

type Props = {
  mode?: DataCatalogMode;
  branchScope?: BranchScope | null;
  onInserted?: () => void;
};

type DiscoveryMode = "search" | "ai";

type SessionDefaults = {
  branch: string;
  periodDays: string;
};

function remapTransformSourceIds(
  transform: DataTransform | undefined,
  idMap: Record<string, string>,
): DataTransform | undefined {
  if (!transform || !("steps" in transform) || !Array.isArray(transform.steps)) {
    return transform;
  }
  const steps = transform.steps.map((step) => {
    if (!step || typeof step !== "object") return step;
    const row = { ...(step as Record<string, unknown>) };
    if (row.op === "merge" && typeof row.sourceId === "string" && idMap[row.sourceId]) {
      row.sourceId = idMap[row.sourceId];
    }
    return row;
  });
  return { ...transform, steps } as DataTransform;
}

function normalizePreview(
  preview: unknown,
): DataBuilderPreviewTable | null {
  if (!preview || typeof preview !== "object") return null;
  const row = preview as Record<string, unknown>;
  const columns = Array.isArray(row.columns) ? row.columns.map(String) : [];
  const rows = Array.isArray(row.rows) ? (row.rows as Array<Array<unknown>>) : [];
  const rowCount = typeof row.rowCount === "number" ? row.rowCount : rows.length;
  if (!columns.length && !rows.length) {
    return { columns: [], rows: [], rowCount };
  }
  return { columns, rows, rowCount };
}

function isPreviewIntent(text: string): boolean {
  return /\b(pr[eé]via|preview|mostre(?:\s+uma)?\s+pr[eé]via|mostrar(?:\s+a)?\s+pr[eé]via|gera(?:r)?\s+(?:a\s+)?pr[eé]via)\b/i.test(
    text,
  );
}

export function DataBuilderChatPanel({
  mode = "insert",
  branchScope = null,
  onInserted,
}: Props) {
  const { addDataSourceBlock, replaceSelectedDataRoute } = useComunicadoEditor();
  const [session, setSession] = useState<DataBuilderSession | null>(null);
  const [discoveryMode, setDiscoveryMode] = useState<DiscoveryMode>("ai");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewTable, setPreviewTable] = useState<DataBuilderPreviewTable | null>(null);
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [routesLoading, setRoutesLoading] = useState(false);
  const [sessionDefaults, setSessionDefaults] = useState<SessionDefaults>({
    branch: "01",
    periodDays: "",
  });
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    void createDataBuilderSession()
      .then((created) => {
        if (!cancelled) {
          setSession(created);
          setPreviewTable(normalizePreview(created.preview));
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || C.sessionError);
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setRoutesLoading(true);
    void listDataRoutes()
      .then((items) => {
        if (!cancelled) setRoutes(items || []);
      })
      .catch(() => {
        if (!cancelled) setRoutes([]);
      })
      .finally(() => {
        if (!cancelled) setRoutesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [session?.messages?.length, busy, previewTable]);

  const draft: DataBuilderDraft = session?.draft ?? { sources: [], status: "draft" };
  const primarySource =
    draft.sources?.find((source) => source.localId === draft.primaryLocalId) ||
    draft.sources?.[0] ||
    null;
  const primaryRoute = useMemo(() => {
    if (!primarySource?.operationId) return null;
    return routes.find((route) => route.operationId === primarySource.operationId) || null;
  }, [primarySource?.operationId, routes]);

  const searchHits = useMemo(() => {
    const q = input.trim().toLowerCase();
    if (discoveryMode !== "search" || !q) return [];
    return routes
      .filter((route) => {
        const hay = [
          route.label,
          route.operationId,
          route.path,
          route.description,
          route.whenToUse,
          route.category,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .slice(0, 12);
  }, [discoveryMode, input, routes]);

  function applySession(next: DataBuilderSession) {
    setSession(next);
    const table = normalizePreview(next.preview);
    if (table) setPreviewTable(table);
  }

  async function runTurn(body: { message?: string; action?: Record<string, unknown> }) {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const next = await dataBuilderTurn(session.id, body);
      applySession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.sessionError);
    } finally {
      setBusy(false);
    }
  }

  function sessionParamsPayload(): Record<string, string | number> {
    const params: Record<string, string | number> = {};
    if (sessionDefaults.branch.trim()) params.branch = sessionDefaults.branch.trim();
    const days = Number(sessionDefaults.periodDays);
    if (sessionDefaults.periodDays.trim() && Number.isFinite(days) && days > 0) {
      params.periodDays = days;
    }
    return params;
  }

  function handleSend() {
    const text = input.trim();
    if (!text || !session?.id) return;

    if (discoveryMode === "search") {
      return;
    }

    setInput("");
    if (isPreviewIntent(text)) {
      void handlePreview(text);
      return;
    }
    void runTurn({ message: text });
  }

  function handleAddSuggestion(card: DataBuilderSuggestionCard) {
    if (!card.operationId) return;
    void runTurn({
      action: {
        type: "add_source",
        operationId: card.operationId,
        params: sessionParamsPayload(),
      },
    });
  }

  function handleAddRoute(route: TvDataRouteCatalogItem) {
    if (!route.operationId) return;
    const defaults = buildRouteDefaultParams(route);
    void runTurn({
      action: {
        type: "add_source",
        operationId: route.operationId,
        params: { ...defaults, ...sessionParamsPayload() },
      },
    });
  }

  async function handlePreview(userText?: string) {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (userText) {
        const next = await dataBuilderTurn(session.id, { message: userText });
        applySession(next);
        const table = normalizePreview(next.preview);
        setPreviewTable(table);
        if (table && !table.columns.length && !table.rowCount) {
          setError(C.previewEmpty);
        }
        return;
      }
      const result = await previewDataBuilderSession(session.id);
      if (result.session) applySession(result.session);
      const table = normalizePreview(result.preview);
      setPreviewTable(table);
      if (!result.ok && result.message) setError(result.message);
      else if (table && !table.columns.length && !table.rowCount) setError(C.previewEmpty);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.previewError);
    } finally {
      setBusy(false);
    }
  }

  function handlePrimaryParamsChange(updates: Record<string, string>) {
    if (!primarySource || !primaryRoute) return;
    const schema = visibleParamSchema(
      (primaryRoute.paramSchema || {}) as DataParamSchema,
      primaryRoute.fixedQueryParams,
    );
    const nextParams = applyDataParamRawUpdates(
      primarySource.params as Record<string, string | number | boolean | null | undefined>,
      updates,
      schema,
    );
    void runTurn({
      action: {
        type: "set_params",
        localId: primarySource.localId,
        params: nextParams,
      },
    });
  }

  async function handleUseOnSlide() {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await materializeDataBuilderSession(session.id);
      const blocks = result.blocks || [];
      if (!blocks.length) {
        setError(result.message || C.materializeError);
        return;
      }

      if (mode === "replace") {
        const primary = blocks.find((b) => b.isPrimary) || blocks[0]!;
        const created = createDataSourceBlock(primary.dataBinding.operationId, {
          label: primary.dataBinding.label,
          defaultParams: primary.dataBinding.params ?? {},
        }) as ComunicadoDataSourceBlock;
        if (primary.queryName) created.queryName = primary.queryName;
        if (primary.dataTransform) {
          created.dataTransform = primary.dataTransform as DataTransform;
        }
        replaceSelectedDataRoute(created);
        onInserted?.();
        return;
      }

      const idMap: Record<string, string> = {};
      const createdBlocks: ComunicadoDataSourceBlock[] = [];
      for (const spec of blocks) {
        const created = createDataSourceBlock(spec.dataBinding.operationId, {
          label: spec.dataBinding.label,
          defaultParams: spec.dataBinding.params ?? {},
        }) as ComunicadoDataSourceBlock;
        if (spec.queryName) created.queryName = spec.queryName;
        idMap[spec.localId] = created.id;
        createdBlocks.push(created);
      }

      const primaryLocal = result.primaryLocalId || blocks[0]?.localId;
      let primaryBlock: ComunicadoBlock | null = null;
      for (let index = 0; index < createdBlocks.length; index += 1) {
        const spec = blocks[index]!;
        const block = createdBlocks[index]!;
        if (spec.dataTransform) {
          block.dataTransform = remapTransformSourceIds(
            spec.dataTransform as DataTransform,
            idMap,
          );
        }
        const isPrimary = spec.localId === primaryLocal || spec.isPrimary;
        if (isPrimary && !primaryBlock) {
          primaryBlock = block;
          addDataSourceBlock(block, {
            preferredView:
              (result.preferredView as "table" | "kpi" | "series" | undefined) || "table",
          });
        } else {
          addDataSourceBlock(block);
        }
      }
      onInserted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : C.materializeError);
    } finally {
      setBusy(false);
    }
  }

  const canMaterialize = (draft.sources?.length ?? 0) > 0 && !busy;
  const table = previewTable;
  const primarySchema = primaryRoute
    ? visibleParamSchema(
        (primaryRoute.paramSchema || {}) as DataParamSchema,
        primaryRoute.fixedQueryParams,
      )
    : {};

  return (
    <div className="td-data-builder-chat">
      <div className="td-data-builder-chat__modes" role="tablist" aria-label="Modo de descoberta">
        <button
          type="button"
          role="tab"
          aria-selected={discoveryMode === "search"}
          className={[
            "td-btn td-btn--sm",
            discoveryMode === "search" ? "td-btn--primary" : "td-btn--ghost",
          ].join(" ")}
          onClick={() => setDiscoveryMode("search")}
        >
          {C.modeSearch}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={discoveryMode === "ai"}
          className={[
            "td-btn td-btn--sm",
            discoveryMode === "ai" ? "td-btn--primary" : "td-btn--ghost",
          ].join(" ")}
          onClick={() => setDiscoveryMode("ai")}
        >
          {C.modeAi}
        </button>
        <span className="td-data-builder-chat__mode-hint">
          {discoveryMode === "search" ? C.modeSearchHint : C.modeAiHint}
        </span>
      </div>

      <section className="td-data-builder-chat__config" aria-label={C.configTitle}>
        <h3 className="td-data-builder-chat__draft-title">{C.configTitle}</h3>
        <p className="td-data-builder-chat__draft-meta">{C.configHint}</p>
        <div className="td-data-builder-chat__config-grid">
          <BranchField
            id="td-data-builder-branch"
            label={C.branchLabel}
            scope={branchScope}
            value={sessionDefaults.branch}
            onChange={(value) =>
              setSessionDefaults((prev) => ({ ...prev, branch: value || "01" }))
            }
          />
          <DeckField label={C.periodDaysLabel}>
            <NativeTextControl
              type="number"
              min={1}
              value={sessionDefaults.periodDays}
              onChange={(event) =>
                setSessionDefaults((prev) => ({
                  ...prev,
                  periodDays: event.target.value,
                }))
              }
              placeholder="opcional"
            />
          </DeckField>
        </div>
        {primarySource && primaryRoute ? (
          <div className="td-data-builder-chat__config-source">
            <h4 className="td-data-builder-chat__draft-title">{C.configSourceTitle}</h4>
            <DataParamFields
              schema={primarySchema}
              values={primarySource.params || {}}
              branchScope={branchScope}
              openEndedDateRange={Boolean(primaryRoute.openEndedDateRange)}
              onChange={handlePrimaryParamsChange}
            />
          </div>
        ) : null}
      </section>

      <div ref={listRef} className="td-data-builder-chat__messages" aria-live="polite">
        {(session?.messages || []).map((message: DataBuilderMessage) => (
          <div
            key={message.id}
            className={[
              "td-data-builder-chat__bubble",
              message.role === "user"
                ? "td-data-builder-chat__bubble--user"
                : "td-data-builder-chat__bubble--assistant",
            ].join(" ")}
          >
            <p className="td-data-builder-chat__text">{message.text}</p>
            {message.suggestions?.length ? (
              <ul className="td-data-builder-chat__suggestions">
                {message.suggestions.map((card) => (
                  <li key={`${message.id}-${card.operationId}`}>
                    <div className="td-data-builder-chat__suggestion-card">
                      <div>
                        <strong>{card.label || card.operationId}</strong>
                        {card.reason ? <small>{card.reason}</small> : null}
                      </div>
                      <button
                        type="button"
                        className="td-btn td-btn--sm td-btn--primary"
                        disabled={busy || !card.operationId}
                        onClick={() => handleAddSuggestion(card)}
                      >
                        {C.addSuggestion}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}

        {discoveryMode === "search" && input.trim() ? (
          <div className="td-data-builder-chat__bubble td-data-builder-chat__bubble--assistant">
            {routesLoading ? (
              <p className="td-data-builder-chat__text">{C.catalogLoading}</p>
            ) : searchHits.length === 0 ? (
              <p className="td-data-builder-chat__text">{C.catalogEmpty}</p>
            ) : (
              <ul className="td-data-builder-chat__suggestions">
                {searchHits.map((route) => (
                  <li key={route.operationId}>
                    <div className="td-data-builder-chat__suggestion-card">
                      <div>
                        <strong>{route.label || route.operationId}</strong>
                        {route.path ? <small>{route.path}</small> : null}
                      </div>
                      <button
                        type="button"
                        className="td-btn td-btn--sm td-btn--primary"
                        disabled={busy}
                        onClick={() => handleAddRoute(route)}
                      >
                        {C.addSuggestion}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}

        {busy ? <p className="td-data-builder-chat__status">{C.loading}</p> : null}
        {error ? (
          <p className="td-data-builder-chat__status td-data-builder-chat__status--error" role="alert">
            {error}
          </p>
        ) : null}
      </div>

      <section className="td-data-builder-chat__draft" aria-label={C.draftTitle}>
        <h3 className="td-data-builder-chat__draft-title">{C.draftTitle}</h3>
        {(draft.sources?.length ?? 0) === 0 ? (
          <p className="td-data-builder-chat__draft-empty">{C.draftEmpty}</p>
        ) : (
          <ul className="td-data-builder-chat__draft-list">
            {draft.sources.map((source) => (
              <li key={source.localId}>
                <span>
                  {source.label || source.operationId}
                  {source.localId === draft.primaryLocalId ? ` · ${C.primaryMark}` : ""}
                </span>
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost"
                  disabled={busy}
                  onClick={() =>
                    void runTurn({
                      action: { type: "remove_source", localId: source.localId },
                    })
                  }
                >
                  {C.removeSource}
                </button>
              </li>
            ))}
          </ul>
        )}
        {draft.transform?.steps?.length ? (
          <p className="td-data-builder-chat__draft-meta">
            Transform: {draft.transform.steps.map((step) => String(step.op || "?")).join(" → ")}
          </p>
        ) : null}
        {table ? (
          <div className="td-data-builder-chat__preview" aria-label={C.previewTitle}>
            <h4 className="td-data-builder-chat__draft-title">{C.previewTitle}</h4>
            {table.columns.length ? (
              <div className="td-data-builder-chat__preview-scroll">
                <table>
                  <thead>
                    <tr>
                      {table.columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {table.rows.map((row, rowIndex) => (
                      <tr key={`r-${rowIndex}`}>
                        {row.map((cell, cellIndex) => (
                          <td key={`c-${rowIndex}-${cellIndex}`}>{String(cell ?? "")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="td-data-builder-chat__draft-empty">{C.previewEmpty}</p>
            )}
          </div>
        ) : null}
      </section>

      <div className="td-data-builder-chat__composer">
        <input
          type="text"
          className="td-data-builder-chat__input"
          placeholder={discoveryMode === "search" ? C.placeholderSearch : C.placeholderAi}
          value={input}
          disabled={!session || busy}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && discoveryMode === "ai") {
              event.preventDefault();
              handleSend();
            }
          }}
          aria-label={discoveryMode === "search" ? C.placeholderSearch : C.placeholderAi}
        />
        {discoveryMode === "ai" ? (
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--primary"
            disabled={!session || busy || !input.trim()}
            onClick={handleSend}
          >
            {C.send}
          </button>
        ) : (
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            disabled
            title={C.modeSearchHint}
          >
            {C.search}
          </button>
        )}
      </div>

      <div className="td-data-builder-chat__actions">
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          disabled={!canMaterialize}
          onClick={() => void handlePreview()}
        >
          {C.preview}
        </button>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--primary"
          disabled={!canMaterialize}
          onClick={() => void handleUseOnSlide()}
        >
          {C.useOnSlide}
        </button>
      </div>
    </div>
  );
}
