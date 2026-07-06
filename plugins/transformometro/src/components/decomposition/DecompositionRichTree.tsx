import { useMemo, useState, type ReactNode } from "react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { RichTreeNode } from "../../types/richTree";
import { countRichTreeNodes } from "../../utils/decompositionRichTree";

const BADGE_CLASS_BY_CODE: Record<string, string> = {
  PK: "tm-rich-tree__badge--pk",
  T: "tm-rich-tree__badge--t",
  ST: "tm-rich-tree__badge--st",
};

const BADGE_HINTS: Record<string, string> = {
  PK: "Processo-chave — bloco principal do WBS.",
  T: "Tarefa — etapa dentro do processo-chave.",
  ST: "Sub-tarefa — detalhamento da tarefa ou do processo-chave.",
};

const HIGHLIGHT_CLASS: Record<NonNullable<RichTreeNode["highlight"]>, string> = {
  asis: "tm-rich-tree__row--asis",
  tobe: "tm-rich-tree__row--tobe",
  changed: "tm-rich-tree__row--changed",
  removed: "tm-rich-tree__row--removed",
};

function TreeChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className="tm-rich-tree__toggle-icon"
      width="12"
      height="12"
      viewBox="0 0 12 12"
      aria-hidden="true"
      focusable="false"
    >
      {expanded ? (
        <path
          d="M2.5 4.5 6 8 9.5 4.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          d="M4.5 2.5 8 6 4.5 9.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

type RowSlots = {
  renderLabel?: (node: RichTreeNode) => ReactNode;
  renderActions?: (node: RichTreeNode) => ReactNode;
};

type RichTreeNodeRowProps = RowSlots & {
  node: RichTreeNode;
  depth: number;
  defaultExpanded: boolean;
  expandDepth: number;
};

function RichTreeNodeRow({
  node,
  depth,
  defaultExpanded,
  expandDepth,
  renderLabel,
  renderActions,
}: RichTreeNodeRowProps) {
  const hasChildren = Boolean(node.children?.length);
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0);
  const badgeCode = String(node.badge ?? "").trim().toUpperCase();
  const badgeClass = BADGE_CLASS_BY_CODE[badgeCode] ?? "";
  const badgeHint = BADGE_HINTS[badgeCode] ?? TM_HELP_TOOLTIPS.decomposition.mapeamento;
  const highlightClass = node.highlight ? HIGHLIGHT_CLASS[node.highlight] : "";

  return (
    <li className="tm-rich-tree__item">
      <div
        className={["tm-rich-tree__row", highlightClass].filter(Boolean).join(" ")}
        style={{ paddingLeft: `${depth * 1.1 + 0.35}rem` }}
      >
        {hasChildren ? (
          <button
            type="button"
            className={`tm-rich-tree__toggle ${
              expanded ? "tm-rich-tree__toggle--expanded" : "tm-rich-tree__toggle--collapsed"
            }`}
            aria-label={expanded ? "Recolher ramo" : "Expandir ramo"}
            aria-expanded={expanded}
            onClick={(event) => {
              event.stopPropagation();
              setExpanded((value) => !value);
            }}
          >
            <TreeChevronIcon expanded={expanded} />
          </button>
        ) : (
          <span className="tm-rich-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="tm-rich-tree__content">
          <div className="tm-rich-tree__primary">
            {renderLabel ? (
              renderLabel(node)
            ) : (
              <span className="tm-rich-tree__label" title={node.label}>
                {node.label}
              </span>
            )}
            {node.badge ? (
              <span className={`tm-rich-tree__badge ${badgeClass}`.trim()} title={badgeHint}>
                {node.badge}
              </span>
            ) : null}
            {node.metaCaption ? <span className="tm-rich-tree__meta">{node.metaCaption}</span> : null}
            {renderActions ? (
              <span className="tm-rich-tree__row-actions">{renderActions(node)}</span>
            ) : null}
          </div>
          {node.subtitle ? <div className="tm-rich-tree__subtitle">{node.subtitle}</div> : null}
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="tm-rich-tree__children">
          {node.children!.map((child) => (
            <RichTreeNodeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              defaultExpanded={depth < expandDepth}
              expandDepth={expandDepth}
              renderLabel={renderLabel}
              renderActions={renderActions}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

type DecompositionRichTreeProps = RowSlots & {
  root: RichTreeNode;
  expandDepth?: number;
  maxHeight?: string;
  footerLabel?: (nodeCount: number) => string;
};

export function DecompositionRichTree({
  root,
  expandDepth = 2,
  maxHeight = "420px",
  footerLabel = (nodeCount) => `${nodeCount} nó(s) no mapeamento`,
  renderLabel,
  renderActions,
}: DecompositionRichTreeProps) {
  const nodeCount = useMemo(() => countRichTreeNodes(root), [root]);

  return (
    <div className="tm-rich-tree">
      <div className="tm-rich-tree__scroll" style={{ maxHeight }}>
        <ul className="tm-rich-tree__list">
          <RichTreeNodeRow
            node={root}
            depth={0}
            defaultExpanded
            expandDepth={expandDepth}
            renderLabel={renderLabel}
            renderActions={renderActions}
          />
        </ul>
      </div>
      <div className="tm-rich-tree__footer">{footerLabel(nodeCount)}</div>
    </div>
  );
}
