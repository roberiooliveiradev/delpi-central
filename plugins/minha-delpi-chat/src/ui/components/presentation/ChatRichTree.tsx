import { useEffect, useMemo, useRef, useState } from "react";
import { TreeGuideRails } from "@delpi/plugin-ui/index";
import type { ChatPresentation, ChatTreeNode } from "../../../data/api/chatTypes";
import {
  formatRichToolbarTemplate,
  richPresentationToolbar,
} from "../../../content/presentationVocabulary";
import { buildTreePointMenuActions, type TableRowMenuAction } from "./chatDrillDown";
import { ChatTableRowMenu, type TableRowMenuAnchor } from "../shared/menus/ChatTableRowMenu";
import { ExpandButton } from "../canvas/ChatExpandModal";
import { ChatPresentationCopyButton } from "./ChatPresentationCopyButton";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import { ChatRichSearchField } from "./ChatRichSearchField";
import type { RichTreeViewState } from "./richPresentationViewState";
import {
  countTreeNodes,
  filterTreeByQuery,
  formatTreeNodeMeta,
  treePresentationToClipboardText,
} from "./pipeline/treePresentationUtils";
import "./ChatRichTree.css";
import "./ChatRichSearchField.css";

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

const EMPHASIS_ROW_CLASS: Record<string, string> = {
  exclusive_mp: "mdc-rich-tree__row--exclusive-mp",
};

function TreeNodeRow({
  node,
  depth,
  isLastSiblingPath,
  defaultExpanded,
  forceExpanded = false,
  onDrillDown,
}: {
  node: ChatTreeNode;
  depth: number;
  isLastSiblingPath: readonly boolean[];
  defaultExpanded: boolean;
  forceExpanded?: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const hasChildren = Boolean(node.children?.length);
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0 || forceExpanded);
  const badgeClass = BADGE_COLORS[String(node.badge || "").toUpperCase()] ?? "";
  const emphasis = String(node.emphasis || "").trim();
  const emphasisClass = EMPHASIS_ROW_CLASS[emphasis] ?? "";
  const metaText = String(node.metaCaption ?? "").trim() || formatTreeNodeMeta(node.meta);
  const menuActions = onDrillDown ? buildTreePointMenuActions(node) : [];
  const hasMenu = menuActions.length > 0;
  const contentRef = useRef<HTMLDivElement>(null);
  const [rowMenu, setRowMenu] = useState<{
    anchor: TableRowMenuAnchor;
    actions: TableRowMenuAction[];
  } | null>(null);

  useEffect(() => {
    if (forceExpanded) {
      setExpanded(true);
    }
  }, [forceExpanded, node.id]);

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
        className={[
          "mdc-rich-tree__row",
          emphasisClass,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <TreeGuideRails depth={depth} isLastSiblingPath={isLastSiblingPath} />

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
            {node.emphasisLabel ? (
              <span className="mdc-rich-tree__badge mdc-rich-tree__badge--exclusive">
                {node.emphasisLabel}
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
          {node.children!.map((child, index) => (
            <TreeNodeRow
              key={`${child.id}-${depth + 1}`}
              node={child}
              depth={depth + 1}
              isLastSiblingPath={[...isLastSiblingPath, index === node.children!.length - 1]}
              defaultExpanded={depth < 1}
              forceExpanded={forceExpanded}
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
  expanded = false,
  initialViewState,
  onDrillDown,
}: {
  presentation: TreePresentation;
  hideTitle?: boolean;
  hideToolbar?: boolean;
  /** Modal expandido — mantém toolbar de busca. */
  expanded?: boolean;
  initialViewState?: RichTreeViewState;
  onDrillDown?: (query: string) => void;
}) {
  const toolbarCopy = richPresentationToolbar();
  const { title, root } = presentation;
  const [searchQuery, setSearchQuery] = useState(initialViewState?.searchQuery ?? "");
  const skipSearchResetOnMountRef = useRef(Boolean(initialViewState));
  const totalNodeCount = useMemo(() => countTreeNodes(root), [root]);

  useEffect(() => {
    if (skipSearchResetOnMountRef.current) {
      skipSearchResetOnMountRef.current = false;
      return;
    }

    setSearchQuery("");
  }, [root, title]);

  const filteredRoot = useMemo(
    () => filterTreeByQuery(root, searchQuery),
    [root, searchQuery],
  );

  const treeViewState = useMemo(
    (): RichTreeViewState => ({ searchQuery }),
    [searchQuery],
  );

  const filteredPresentation = useMemo((): TreePresentation => {
    if (!filteredRoot || filteredRoot === root) {
      return presentation;
    }

    return {
      ...presentation,
      root: filteredRoot,
    };
  }, [filteredRoot, presentation, root]);

  const visibleNodeCount = filteredRoot ? countTreeNodes(filteredRoot) : 0;
  const searchActive = Boolean(String(searchQuery).trim());
  const footerLabel =
    searchActive && visibleNodeCount !== totalNodeCount
      ? formatRichToolbarTemplate(toolbarCopy.footerTreeFiltered, {
          visible: visibleNodeCount,
          total: totalNodeCount,
        })
      : formatRichToolbarTemplate(toolbarCopy.footerTreeAll, {
          total: searchActive ? visibleNodeCount : totalNodeCount,
        });

  const showToolbar = !hideToolbar || expanded;

  return (
    <div
      className={[
        "mdc-rich-tree",
        hideToolbar && !expanded ? "mdc-rich-tree--embedded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {showToolbar ? (
        <div className="mdc-rich-tree__header">
          <span
            className="mdc-rich-tree__title"
            aria-hidden={hideTitle ? "true" : undefined}
          >
            {hideTitle ? null : title}
          </span>
          <div className="mdc-rich-tree__actions">
            <ChatRichSearchField
              className="mdc-rich-tree__search"
              label={toolbarCopy.searchAriaLabelTree}
              onChange={setSearchQuery}
              placeholder={toolbarCopy.searchPlaceholderTree}
              value={searchQuery}
            />
            <ChatPresentationCopyButton
              getText={() => treePresentationToClipboardText(filteredPresentation)}
              copyAriaLabel="Copiar árvore"
              copiedAriaLabel="Árvore copiada"
            />
            <ChatPresentationExportButtons presentation={filteredPresentation} />
            {!expanded ? (
              <ExpandButton
                presentation={presentation}
                treeViewState={treeViewState}
                onDrillDown={onDrillDown}
              />
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mdc-rich-tree__scroll">
        {filteredRoot ? (
          <ul className="mdc-rich-tree__list">
            <TreeNodeRow
              node={filteredRoot}
              depth={0}
              isLastSiblingPath={[]}
              defaultExpanded
              forceExpanded={searchActive}
              onDrillDown={onDrillDown}
            />
          </ul>
        ) : (
          <div className="mdc-rich-tree__empty" role="status">
            —
          </div>
        )}
      </div>

      <div className="mdc-rich-tree__footer">{footerLabel}</div>
    </div>
  );
}
