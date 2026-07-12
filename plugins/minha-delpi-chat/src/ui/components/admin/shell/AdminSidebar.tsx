import { ChatNativeTextInput } from "../../shared/chatNativeFormFields";
import { ChevronRight, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import {
  buildAdminNavTree,
  getExpandedNodeIdsForNav,
  isAdminNavTargetActive,
  type AdminNavNode,
  type AdminNavTreeSection,
} from "../../../../navigation/adminNavTree";
import { searchAdminNavigation } from "../../../../navigation/adminNavSearch";
import type { AdminNavState } from "../../../../navigation/adminNavigation";

import "./AdminSidebar.css";

type AdminSidebarProps = {
  nav: AdminNavState;
  onNavigate: (next: AdminNavState) => void;
  className?: string;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
};

type AdminSidebarNodeProps = {
  node: AdminNavNode;
  depth: number;
  nav: AdminNavState;
  expandedIds: Set<string>;
  onToggle: (nodeId: string) => void;
  onNavigate: (next: AdminNavState) => void;
};

function AdminSidebarNode({
  node,
  depth,
  nav,
  expandedIds,
  onToggle,
  onNavigate,
}: AdminSidebarNodeProps) {
  const hasChildren = Boolean(node.children?.length);
  const isExpanded = expandedIds.has(node.id);
  const isActive = isAdminNavTargetActive(nav, node.target);
  const branchActive =
    hasChildren &&
    node.children!.some(
      (child) =>
        isAdminNavTargetActive(nav, child.target) ||
        child.children?.some((grand) => isAdminNavTargetActive(nav, grand.target)),
    );

  if (!hasChildren) {
    return (
      <button
        type="button"
        className={[
          "mdc-admin-sidebar__node",
          "mdc-admin-sidebar__node--leaf",
          isActive ? "is-active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={{ "--mdc-admin-sidebar-depth": depth } as CSSProperties}
        aria-current={isActive ? "page" : undefined}
        onClick={() => onNavigate(node.target)}
      >
        {node.label}
      </button>
    );
  }

  return (
    <div
      className={[
        "mdc-admin-sidebar__branch",
        isExpanded ? "is-expanded" : "",
        branchActive || isActive ? "is-branch-active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ "--mdc-admin-sidebar-depth": depth } as CSSProperties}
    >
      <button
        type="button"
        className="mdc-admin-sidebar__node mdc-admin-sidebar__node--branch"
        aria-expanded={isExpanded}
        onClick={() => onToggle(node.id)}
      >
        <span className="mdc-admin-sidebar__node-label">{node.label}</span>
        <ChevronRight size={14} aria-hidden="true" className="mdc-admin-sidebar__chevron" />
      </button>

      {isExpanded ? (
        <ul className="mdc-admin-sidebar__nested">
          {node.children!.map((child) => (
            <li key={child.id}>
              <AdminSidebarNode
                node={child}
                depth={depth + 1}
                nav={nav}
                expandedIds={expandedIds}
                onToggle={onToggle}
                onNavigate={onNavigate}
              />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function AdminSidebar({
  nav,
  onNavigate,
  className,
  mobileOpen = false,
  onMobileClose,
}: AdminSidebarProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const tree = useMemo(() => buildAdminNavTree(), []);
  const searchResult = useMemo(
    () => searchAdminNavigation(tree, searchQuery),
    [tree, searchQuery],
  );
  const { tree: filteredTree, contentHits, hasQuery } = searchResult;
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() =>
    getExpandedNodeIdsForNav(nav, filteredTree, searchQuery),
  );

  useEffect(() => {
    setExpandedIds(getExpandedNodeIdsForNav(nav, filteredTree, searchQuery));
  }, [nav, filteredTree, searchQuery]);

  useEffect(() => {
    if (!mobileOpen) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      searchInputRef.current?.focus();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [mobileOpen]);

  function toggleNode(nodeId: string) {
    setExpandedIds((current) => {
      const next = new Set(current);

      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }

      return next;
    });
  }

  function toggleSection(section: AdminNavTreeSection) {
    toggleNode(section.key);
  }

  function handleNavigate(next: AdminNavState) {
    onNavigate(next);
    setSearchQuery("");
    onMobileClose?.();
  }

  const rootClass = ["mdc-admin-sidebar", className].filter(Boolean).join(" ");
  const showEmpty = hasQuery && filteredTree.length === 0 && contentHits.length === 0;

  return (
    <aside className={rootClass} aria-label="Navegação do admin">
      {mobileOpen && onMobileClose ? (
        <div className="mdc-admin-sidebar__mobile-header">
          <button
            type="button"
            className="mdc-chat-ws-outline-btn mdc-admin-sidebar__mobile-close"
            onClick={onMobileClose}
          >
            <X size={16} aria-hidden="true" />
            <span>Fechar menu</span>
          </button>
        </div>
      ) : null}

      <div className="mdc-admin-sidebar__search">
        <Search size={16} aria-hidden="true" />
        <ChatNativeTextInput
          ref={searchInputRef}
          type="search"
          value={searchQuery}
          placeholder="Buscar seção, página ou conteúdo…"
          aria-label="Buscar na navegação e no conteúdo do admin"
          autoComplete="off"
          enterKeyHint="search"
          onChange={(event) => setSearchQuery(event.target.value)}
        />
      </div>

      {hasQuery && contentHits.length > 0 ? (
        <div className="mdc-admin-sidebar__content-hits" role="region" aria-label="Resultados de conteúdo">
          <p className="mdc-admin-sidebar__content-label">Conteúdo</p>
          <ul className="mdc-admin-sidebar__content-list">
            {contentHits.map((hit) => (
              <li key={hit.id}>
                <button
                  type="button"
                  className="mdc-admin-sidebar__content-item"
                  onClick={() => handleNavigate(hit.target)}
                >
                  <span className="mdc-admin-sidebar__content-path">{hit.path}</span>
                  <span className="mdc-admin-sidebar__content-title">{hit.title}</span>
                  <span className="mdc-admin-sidebar__content-snippet">{hit.snippet}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <nav className="mdc-admin-sidebar__tree" aria-label="Árvore de navegação">
        {showEmpty ? (
          <p className="mdc-admin-sidebar__empty">Nenhum item corresponde à busca.</p>
        ) : (
          filteredTree.map((section) => {
            const Icon = section.icon;
            const isOverview = section.key === "overview";
            const isSectionExpanded = expandedIds.has(section.key);
            const sectionActive = section.nodes.some((node) =>
              isAdminNavTargetActive(nav, node.target),
            );

            if (isOverview && section.nodes.length === 1) {
              const node = section.nodes[0]!;
              const isActive = isAdminNavTargetActive(nav, node.target);

              return (
                <button
                  key={section.key}
                  type="button"
                  className={[
                    "mdc-admin-sidebar__section-row",
                    "mdc-admin-sidebar__section-row--solo",
                    isActive ? "is-active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => handleNavigate(node.target)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{section.label}</span>
                </button>
              );
            }

            return (
              <div
                key={section.key}
                className={[
                  "mdc-admin-sidebar__group",
                  isSectionExpanded ? "is-expanded" : "",
                  sectionActive ? "is-section-active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <button
                  type="button"
                  className="mdc-admin-sidebar__section-row"
                  aria-expanded={isSectionExpanded}
                  onClick={() => toggleSection(section)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span className="mdc-admin-sidebar__section-label">{section.label}</span>
                  <ChevronRight
                    size={16}
                    aria-hidden="true"
                    className="mdc-admin-sidebar__chevron"
                  />
                </button>

                {isSectionExpanded ? (
                  <div className="mdc-admin-sidebar__section-children">
                    {section.nodes.map((node) => (
                      <AdminSidebarNode
                        key={node.id}
                        node={node}
                        depth={1}
                        nav={nav}
                        expandedIds={expandedIds}
                        onToggle={toggleNode}
                        onNavigate={handleNavigate}
                      />
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </nav>
    </aside>
  );
}
