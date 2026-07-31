import { useEffect, useRef, useState } from "react";
import {
  createDataSourceBlock,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
  type DataTransform,
} from "@delpi/tv-dashboard-presentation";

import {
  createDataBuilderSession,
  dataBuilderTurn,
  materializeDataBuilderSession,
  previewDataBuilderSession,
  type DataBuilderDraft,
  type DataBuilderMessage,
  type DataBuilderPreviewTable,
  type DataBuilderSession,
  type DataBuilderSuggestionCard,
} from "../api/tvDashboardApi";
import { DATA_BUILDER_CHAT_CONTENT as C } from "../content/dataBuilderChatContent";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { DataCatalogMode } from "./comunicadoEditorContextCore";

type Props = {
  mode?: DataCatalogMode;
  onInserted?: () => void;
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

export function DataBuilderChatPanel({ mode = "insert", onInserted }: Props) {
  const { addDataSourceBlock, replaceSelectedDataRoute } = useComunicadoEditor();
  const [session, setSession] = useState<DataBuilderSession | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewTable, setPreviewTable] = useState<DataBuilderPreviewTable | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    void createDataBuilderSession()
      .then((created) => {
        if (!cancelled) setSession(created);
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
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [session?.messages?.length, busy]);

  async function runTurn(body: { message?: string; action?: Record<string, unknown> }) {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const next = await dataBuilderTurn(session.id, body);
      setSession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.sessionError);
    } finally {
      setBusy(false);
    }
  }

  function handleSend() {
    const text = input.trim();
    if (!text) return;
    setInput("");
    void runTurn({ message: text });
  }

  function handleAddSuggestion(card: DataBuilderSuggestionCard) {
    if (!card.operationId) return;
    void runTurn({ action: { type: "add_source", operationId: card.operationId } });
  }

  async function handlePreview() {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await previewDataBuilderSession(session.id);
      if (result.session) setSession(result.session);
      setPreviewTable(result.preview ?? null);
      if (!result.ok && result.message) setError(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.previewError);
    } finally {
      setBusy(false);
    }
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

  const draft: DataBuilderDraft = session?.draft ?? { sources: [], status: "draft" };
  const canMaterialize = (draft.sources?.length ?? 0) > 0 && !busy;
  const table = previewTable;

  return (
    <div className="td-data-builder-chat">
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
        {table && table.columns.length ? (
          <div className="td-data-builder-chat__preview" aria-label={C.previewTitle}>
            <h4 className="td-data-builder-chat__draft-title">{C.previewTitle}</h4>
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
          </div>
        ) : null}
      </section>

      <div className="td-data-builder-chat__composer">
        <input
          type="text"
          className="td-data-builder-chat__input"
          placeholder={C.placeholder}
          value={input}
          disabled={!session || busy}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              handleSend();
            }
          }}
          aria-label={C.placeholder}
        />
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--primary"
          disabled={!session || busy || !input.trim()}
          onClick={handleSend}
        >
          {C.send}
        </button>
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
