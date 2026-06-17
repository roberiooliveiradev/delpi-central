import { useMemo, useRef, useState } from "react";
import type { ChatPresentation, ChatTreeNode } from "../../../data/api/chatTypes";
import { buildTreePointMenuActions, type TableRowMenuAction } from "./chatDrillDown";
import { ChatTableRowMenu, type TableRowMenuAnchor } from "../ChatTableRowMenu";
import { ExpandButton } from "../ChatExpandModal";
import { ChatPresentationCopyButton } from "./ChatPresentationCopyButton";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import {
  formatTreeNodeMeta,
  treePresentationToClipboardText,
} from "./pipeline/treePresentationUtils";
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

function TreeMoreIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <circle cx="8" cy="3.25" r="1.25" fill="currentColor" />
      <circle cx="8" cy="8" r="1.25" fill="currentColor" />
      <circle cx="8" cy="12.75" r="1.25" fill="currentColor" />
    </svg>
  );
}

type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;

const BADGE_COLORS: Record<string, string> = {
  PA: "mdc-rich-tree__badge--pa",
  PI: "mdc-rich-tree__badge--pi",
  MP: "mdc-rich-tree__badge--mp",
};

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
  const metaText = String(node.metaCaption ?? "").trim() || formatTreeNodeMeta(node.meta);
  const menuActions = onDrillDown ? buildTreePointMenuActions(node) : [];
  const hasMenu = menuActions.length > 0;
  const contentRef = useRef<HTMLDivElement>(null);
  const [rowMenu, setRowMenu] = useState<{
    anchor: TableRowMenuAnchor;
    actions: TableRowMenuAction[];
  } | null>(null);

  function openRowMenu(event: React.MouseEvent) {
    if (!onDrillDown || !menuActions.length) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const rect = contentRef.current?.getBoundingClientRect();

    if (!rect) {
      return;
    }

    setRowMenu({
      anchor: { rect },
      actions: menuActions,
    });
  }

  return (
    <li className="mdc-rich-tree__item">
      <div
        className="mdc-rich-tree__row"
        style={{ paddingLeft: `${depth * 1.1 + 0.35}rem` }}
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

        <div
          ref={contentRef}
          className={`mdc-rich-tree__content ${hasMenu ? "mdc-rich-tree__content--interactive" : ""}`}
          onClick={hasMenu ? openRowMenu : undefined}
          onContextMenu={hasMenu ? openRowMenu : undefined}
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
          title={hasMenu ? "Clique para ver ações deste item" : undefined}
        >
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

        {hasMenu ? (
          <button
            type="button"
            className="mdc-rich-tree__more"
            aria-label={`Ações do item ${node.label}`}
            aria-haspopup="menu"
            onClick={openRowMenu}
          >
            <TreeMoreIcon />
          </button>
        ) : null}
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
  return (
    <div
      className={[
        "mdc-rich-tree",
        hideToolbar ? "mdc-rich-tree--embedded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!hideToolbar ? (
        <div className="mdc-rich-tree__header">
          <span
            className="mdc-rich-tree__title"
            aria-hidden={hideTitle ? "true" : undefined}
          >
            {hideTitle ? null : title}
          </span>
          <div className="mdc-rich-tree__actions">
            <ChatPresentationCopyButton
              getText={() => treePresentationToClipboardText(presentation)}
              copyAriaLabel="Copiar árvore"
              copiedAriaLabel="Árvore copiada"
            />
            <ChatPresentationExportButtons presentation={presentation} />
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
