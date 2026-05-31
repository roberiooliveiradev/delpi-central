import { useMemo, useState } from "react";
import type { ChatPresentation, ChatTreeNode } from "../../data/api/chatTypes";
import { buildTreePointMenuActions, type TableRowMenuAction } from "./chatDrillDown";
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import { ExpandButton } from "./ChatExpandModal";
import {
  exportTreeToCsv,
  treePresentationToClipboardText,
} from "./treePresentationUtils";
import "./ChatRichTree.css";

function TreeChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className="mdc-rich-tree__toggle-icon"
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

type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;

const BADGE_COLORS: Record<string, string> = {
  PA: "mdc-rich-tree__badge--pa",
  PI: "mdc-rich-tree__badge--pi",
  MP: "mdc-rich-tree__badge--mp",
};

function formatMeta(meta?: Record<string, string | number>): string {
  if (!meta) {
    return "";
  }

  const parts: string[] = [];

  if (meta.quantity !== undefined && meta.quantity !== null && meta.quantity !== "") {
    parts.push(`Qtd: ${meta.quantity}`);
  }

  if (meta.unit) {
    parts.push(String(meta.unit));
  }

  return parts.join(" · ");
}

function countNodes(node: ChatTreeNode): number {
  const children = node.children ?? [];

  return 1 + children.reduce((total, child) => total + countNodes(child), 0);
}

function TreeNodeRow({
  node,
  depth,
  defaultExpanded,
  onDrillDown,
}: {
  node: ChatTreeNode;
  depth: number;
  defaultExpanded: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const hasChildren = Boolean(node.children?.length);
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0);
  const badgeClass = BADGE_COLORS[String(node.badge || "").toUpperCase()] ?? "";
  const metaText = formatMeta(node.meta);
  const menuActions = onDrillDown ? buildTreePointMenuActions(node) : [];
  const hasMenu = menuActions.length > 0;
  const [rowMenu, setRowMenu] = useState<{
    anchor: { x: number; y: number };
    actions: TableRowMenuAction[];
  } | null>(null);

  function openRowMenu(event: React.MouseEvent) {
    if (!onDrillDown || !menuActions.length) {
      return;
    }

    event.stopPropagation();
    setRowMenu({
      anchor: { x: event.clientX, y: event.clientY },
      actions: menuActions,
    });
  }

  return (
    <li className="mdc-rich-tree__item">
      <div
        className={`mdc-rich-tree__row ${hasMenu ? "mdc-rich-tree__row--clickable" : ""}`}
        style={{ paddingLeft: `${depth * 1.1 + 0.35}rem` }}
        onContextMenu={hasMenu ? openRowMenu : undefined}
        onClick={hasMenu ? openRowMenu : undefined}
        onKeyDown={
          hasMenu
            ? (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openRowMenu(event as unknown as React.MouseEvent);
                }
              }
            : undefined
        }
        role={hasMenu ? "button" : undefined}
        tabIndex={hasMenu ? 0 : undefined}
        title={hasMenu ? "Clique para ver ações" : undefined}
      >
        {hasChildren ? (
          <button
            type="button"
            className={`mdc-rich-tree__toggle ${
              expanded ? "mdc-rich-tree__toggle--expanded" : "mdc-rich-tree__toggle--collapsed"
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
          <span className="mdc-rich-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="mdc-rich-tree__content">
          <div className="mdc-rich-tree__primary">
            <span className="mdc-rich-tree__label">{node.label}</span>
            {node.badge ? (
              <span className={`mdc-rich-tree__badge ${badgeClass}`.trim()}>
                {node.badge}
              </span>
            ) : null}
            {metaText ? (
              <span className="mdc-rich-tree__meta">{metaText}</span>
            ) : null}
          </div>
          {node.subtitle ? (
            <div className="mdc-rich-tree__subtitle">{node.subtitle}</div>
          ) : null}
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="mdc-rich-tree__children">
          {node.children!.map((child) => (
            <TreeNodeRow
              key={`${child.id}-${depth + 1}`}
              node={child}
              depth={depth + 1}
              defaultExpanded={depth < 1}
              onDrillDown={onDrillDown}
            />
          ))}
        </ul>
      ) : null}

      {rowMenu && onDrillDown ? (
        <ChatTableRowMenu
          actions={rowMenu.actions}
          anchor={rowMenu.anchor}
          onSelect={onDrillDown}
          onClose={() => setRowMenu(null)}
          menuLabel="Ações do nó"
        />
      ) : null}
    </li>
  );
}

export function ChatRichTree({
  presentation,
  hideTitle = false,
  hideToolbar = false,
  onDrillDown,
}: {
  presentation: TreePresentation;
  hideTitle?: boolean;
  hideToolbar?: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const { title, root } = presentation;
  const nodeCount = useMemo(() => countNodes(root), [root]);
  const [copied, setCopied] = useState(false);

  function copyToClipboard() {
    navigator.clipboard?.writeText(treePresentationToClipboardText(presentation)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="mdc-rich-tree">
      {!hideToolbar ? (
        <div className="mdc-rich-tree__header">
          <span
            className="mdc-rich-tree__title"
            aria-hidden={hideTitle ? "true" : undefined}
          >
            {hideTitle ? null : title}
          </span>
          <div className="mdc-rich-tree__actions">
            <button
              type="button"
              className="mdc-rich-table__btn"
              onClick={copyToClipboard}
              title="Copiar árvore"
            >
              {copied ? "✓ Copiado" : "Copiar"}
            </button>
            <button
              type="button"
              className="mdc-rich-table__btn"
              onClick={() => exportTreeToCsv(presentation)}
              title="Baixar CSV"
            >
              ↓ CSV
            </button>
            <ExpandButton presentation={presentation} onDrillDown={onDrillDown} />
          </div>
        </div>
      ) : null}

      <div className="mdc-rich-tree__scroll">
        <ul className="mdc-rich-tree__list">
          <TreeNodeRow
            node={root}
            depth={0}
            defaultExpanded
            onDrillDown={onDrillDown}
          />
        </ul>
      </div>

      <div className="mdc-rich-tree__footer">{nodeCount} nó(s)</div>
    </div>
  );
}
