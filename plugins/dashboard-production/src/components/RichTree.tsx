import { useMemo, useState } from "react";

import type { RichTreeNode } from "../types/richTree";
import { countRichTreeNodes } from "../utils/productStructureTree";

const BADGE_CLASS_BY_TYPE: Record<string, string> = {
  PA: "dp-rich-tree__badge--pa",
  PI: "dp-rich-tree__badge--pi",
  MP: "dp-rich-tree__badge--mp",
};

function TreeChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className="dp-rich-tree__toggle-icon"
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

type RichTreeNodeRowProps = {
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
}: RichTreeNodeRowProps) {
  const hasChildren = Boolean(node.children?.length);
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0);
  const badgeClass =
    BADGE_CLASS_BY_TYPE[String(node.badge ?? "").trim().toUpperCase()] ?? "";

  return (
    <li className="dp-rich-tree__item">
      <div
        className="dp-rich-tree__row"
        style={{ paddingLeft: `${depth * 1.1 + 0.35}rem` }}
      >
        {hasChildren ? (
          <button
            type="button"
            className={`dp-rich-tree__toggle ${
              expanded
                ? "dp-rich-tree__toggle--expanded"
                : "dp-rich-tree__toggle--collapsed"
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
          <span className="dp-rich-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="dp-rich-tree__content">
          <div className="dp-rich-tree__primary">
            <span className="dp-rich-tree__label">{node.label}</span>
            {node.badge ? (
              <span className={`dp-rich-tree__badge ${badgeClass}`.trim()}>
                {node.badge}
              </span>
            ) : null}
            {node.metaCaption ? (
              <span className="dp-rich-tree__meta">{node.metaCaption}</span>
            ) : null}
          </div>
          {node.subtitle ? (
            <div className="dp-rich-tree__subtitle">{node.subtitle}</div>
          ) : null}
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="dp-rich-tree__children">
          {node.children!.map((child) => (
            <RichTreeNodeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              defaultExpanded={depth < expandDepth}
              expandDepth={expandDepth}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

type RichTreeProps = {
  root: RichTreeNode;
  expandDepth?: number;
  maxHeight?: string;
  footerLabel?: (nodeCount: number) => string;
};

export function RichTree({
  root,
  expandDepth = 1,
  maxHeight = "420px",
  footerLabel = (nodeCount) => `${nodeCount} nó(s)`,
}: RichTreeProps) {
  const nodeCount = useMemo(() => countRichTreeNodes(root), [root]);

  return (
    <div className="dp-rich-tree">
      <div className="dp-rich-tree__scroll" style={{ maxHeight }}>
        <ul className="dp-rich-tree__list">
          <RichTreeNodeRow
            node={root}
            depth={0}
            defaultExpanded
            expandDepth={expandDepth}
          />
        </ul>
      </div>
      <div className="dp-rich-tree__footer">{footerLabel(nodeCount)}</div>
    </div>
  );
}
