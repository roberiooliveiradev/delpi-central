import { Search, X, type LucideIcon } from "lucide-react";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { AnchoredPanelPortal } from "../../shape/AnchoredPanelPortal";
import {
  BPMN_NODE_DEFINITIONS,
  type FlowchartNodeType,
} from "../model/bpmnNodeCatalog";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import {
  FLOWCHART_NODE_ICONS,
  type DiagramEditorAction,
} from "./flowchartEditorToolbar";
import {
  searchFlowchartComponents,
  type FlowchartComponentSearchHit,
} from "./searchFlowchartComponents";

type Props = {
  labels: FlowchartEditorLabels;
  onAddNode: (type: FlowchartNodeType) => void;
  onEditorAction: (actionId: DiagramEditorAction["id"]) => void;
  portalScopeClassName?: string;
};

function hitIcon(hit: FlowchartComponentSearchHit): LucideIcon {
  if (hit.kind === "action") return hit.icon;
  return FLOWCHART_NODE_ICONS[hit.type];
}

/**
 * Busca de componentes BPMN na top bar — paleta + ações (Faixa, modelos).
 */
export function FlowchartComponentSearch({
  labels,
  onAddNode,
  onEditorAction,
  portalScopeClassName,
}: Props) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const hits = useMemo(
    () => searchFlowchartComponents(query, labels),
    [labels, query],
  );
  const showPanel = open && query.trim().length > 0;

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const pick = (hit: FlowchartComponentSearchHit) => {
    if (hit.kind === "node") onAddNode(hit.type);
    else onEditorAction(hit.actionId);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!showPanel) {
      if (event.key === "Escape") {
        setQuery("");
        setOpen(false);
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => Math.min(index + 1, Math.max(hits.length - 1, 0)));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const hit = hits[activeIndex];
      if (hit) pick(hit);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setQuery("");
      setOpen(false);
    }
  };

  return (
    <div ref={rootRef} className="delpi-ui-bpmn-editor__component-search" role="search">
      <div className="delpi-ui-bpmn-editor__component-search-field">
        <Search
          size={14}
          className="delpi-ui-bpmn-editor__component-search-icon"
          aria-hidden
        />
        <input
          ref={inputRef}
          type="search"
          className="delpi-ui-bpmn-editor__component-search-input"
          value={query}
          placeholder={labels.componentSearchPlaceholder}
          aria-label={labels.componentSearchAriaLabel}
          aria-autocomplete="list"
          aria-controls={showPanel ? listId : undefined}
          aria-expanded={showPanel}
          aria-activedescendant={
            showPanel && hits[activeIndex]
              ? `${listId}-option-${hits[activeIndex].id}`
              : undefined
          }
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {query ? (
          <button
            type="button"
            className="delpi-ui-bpmn-editor__component-search-clear"
            aria-label={labels.componentSearchClear}
            onClick={() => {
              setQuery("");
              setOpen(false);
              inputRef.current?.focus();
            }}
          >
            <X size={14} aria-hidden />
          </button>
        ) : null}
      </div>

      <AnchoredPanelPortal
        open={showPanel}
        anchorRef={rootRef}
        panelRef={panelRef}
        variant="bare"
        role="listbox"
        aria-label={labels.componentSearchAriaLabel}
        density="compact"
        preferredPlacement="bottom"
        matchAnchorWidth
        portalScopeClassName={portalScopeClassName}
        onDismiss={() => setOpen(false)}
      >
        <div
          ref={panelRef}
          className="delpi-ui-bpmn-editor__component-search-panel delpi-ui-popover-surface"
          data-delpi-ui-density="compact"
        >
          {hits.length === 0 ? (
            <p className="delpi-ui-bpmn-editor__component-search-empty">
              {labels.componentSearchEmpty}
            </p>
          ) : (
            <ul id={listId} className="delpi-ui-bpmn-editor__component-search-list" role="listbox">
              {hits.map((hit, index) => {
                const Icon = hitIcon(hit);
                const active = index === activeIndex;
                const title =
                  hit.kind === "node"
                    ? hit.hint || BPMN_NODE_DEFINITIONS[hit.type].hint
                    : hit.hint;
                return (
                  <li key={hit.id} role="presentation">
                    <button
                      type="button"
                      id={`${listId}-option-${hit.id}`}
                      role="option"
                      aria-selected={active}
                      title={title}
                      className={[
                        "delpi-ui-bpmn-editor__component-search-option",
                        active
                          ? "delpi-ui-bpmn-editor__component-search-option--active"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => pick(hit)}
                    >
                      <span
                        className="delpi-ui-bpmn-editor__component-search-option-icon"
                        aria-hidden
                      >
                        <Icon size={16} strokeWidth={2} />
                      </span>
                      <span className="delpi-ui-bpmn-editor__component-search-option-text">
                        <span className="delpi-ui-bpmn-editor__component-search-option-label">
                          {hit.label}
                        </span>
                        <span className="delpi-ui-bpmn-editor__component-search-option-meta">
                          {hit.categoryLabel}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
