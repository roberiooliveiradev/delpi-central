import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, PanelLeftClose, PanelLeftOpen, Search } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { ProcessoWorkspaceTreeIcon } from "../processos/ProcessoWorkspaceTreeIcon";
import {
  collectConfiguracoesExpandedNodeIds,
  filterConfiguracoesTree,
  type ConfiguracoesNavNode,
} from "./configuracoesWorkspaceNav";
import { handleSpaLinkClick } from "../../utils/spaLink";

type Props = {
  nodes: ConfiguracoesNavNode[];
  activeNodeId: string;
  onNavigate: (href: string) => void;
  backActions?: ReactNode;
  footerActions?: ReactNode;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
};

function TreeNode({
  node,
  activeNodeId,
  expandedIds,
  onToggle,
  onNavigate,
}: {
  node: ConfiguracoesNavNode;
  activeNodeId: string;
  expandedIds: Set<string>;
  onToggle: (nodeId: string) => void;
  onNavigate: (href: string) => void;
}) {
  const hasChildren = Boolean(node.children?.length);
  const isExpanded = expandedIds.has(node.id);
  const isActive = node.id === activeNodeId;
  const folderVariant = hasChildren ? "filled" : "empty";

  return (
    <li className="tm-processo-workspace-tree__item">
      <div
        className={`tm-processo-workspace-tree__row${isActive ? " tm-processo-workspace-tree__row--active" : ""}`}
        style={{ paddingLeft: `${0.35 + node.depth * 0.65}rem` }}
      >
        {hasChildren ? (
          <button
            type="button"
            className="tm-processo-workspace-tree__toggle"
            aria-expanded={isExpanded}
            aria-label={isExpanded ? "Recolher" : "Expandir"}
            onClick={() => onToggle(node.id)}
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        ) : (
          <span className="tm-processo-workspace-tree__toggle-spacer" aria-hidden="true" />
        )}
        <a
          href={node.href}
          className="tm-processo-workspace-tree__link"
          aria-current={isActive ? "page" : undefined}
          onClick={(event) => handleSpaLinkClick(event, node.href, onNavigate)}
        >
          <span className="tm-processo-workspace-tree__link-main">
            <ProcessoWorkspaceTreeIcon variant={folderVariant} />
            <span className="tm-processo-workspace-tree__label" title={node.label}>
              {node.label}
            </span>
          </span>
          {node.badge ? <span className="tm-processo-workspace-tree__badge">{node.badge}</span> : null}
        </a>
      </div>
      {hasChildren ? (
        <div
          className={`tm-processo-workspace-tree__children-wrap${isExpanded ? " tm-processo-workspace-tree__children-wrap--expanded" : ""}`}
        >
          <ul className="tm-processo-workspace-tree__children" role="group">
            {node.children!.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                activeNodeId={activeNodeId}
                expandedIds={expandedIds}
                onToggle={onToggle}
                onNavigate={onNavigate}
              />
            ))}
          </ul>
        </div>
      ) : null}
    </li>
  );
}

export function ConfiguracoesWorkspaceSidebar({
  nodes,
  activeNodeId,
  onNavigate,
  backActions,
  footerActions,
  collapsed = false,
  onToggleCollapsed,
}: Props) {
  const [query, setQuery] = useState("");
  const filteredNodes = useMemo(() => filterConfiguracoesTree(nodes, query), [nodes, query]);

  const autoExpanded = useMemo(
    () => collectConfiguracoesExpandedNodeIds(nodes, activeNodeId),
    [activeNodeId, nodes]
  );

  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => autoExpanded);

  useEffect(() => {
    setExpandedIds((current) => {
      const next = new Set(current);
      autoExpanded.forEach((id) => next.add(id));
      return next;
    });
  }, [autoExpanded]);

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  }, []);

  const rootHasChildren = nodes.length > 0;

  if (collapsed) {
    return (
      <aside
        className="tm-processo-workspace-sidebar tm-processo-workspace-sidebar--collapsed"
        aria-label="Navegação de configurações"
      >
        <button
          type="button"
          className="tm-processo-workspace-sidebar__rail-btn"
          onClick={onToggleCollapsed}
          aria-label="Expandir barra lateral"
          title="Expandir"
        >
          <PanelLeftOpen size={18} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="tm-processo-workspace-sidebar__rail-btn"
          onClick={onToggleCollapsed}
          aria-label="Pesquisar nas configurações"
          title="Pesquisar"
        >
          <Search size={18} aria-hidden="true" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="tm-processo-workspace-sidebar" aria-label="Navegação de configurações">
      <div className="tm-processo-workspace-sidebar__header">
        {backActions ? (
          <div className="tm-processo-workspace-sidebar__back">{backActions}</div>
        ) : null}
        <button
          type="button"
          className="tm-processo-workspace-sidebar__collapse-btn"
          onClick={onToggleCollapsed}
          aria-label="Recolher barra lateral"
          title="Recolher"
        >
          <PanelLeftClose size={16} aria-hidden="true" />
        </button>
      </div>

      <div className="tm-processo-workspace-sidebar__search">
        <Search size={15} aria-hidden="true" />
        <NativeTextControl
          type="search"
          value={query}
          onChange={setQuery}
          placeholder="Pesquisar unidades, deptos., recursos…"
          aria-label="Pesquisar na árvore de configurações"
        />
      </div>

      <div className="tm-processo-workspace-sidebar__root">
        <ProcessoWorkspaceTreeIcon variant={rootHasChildren ? "filled" : "empty"} />
        <div className="tm-processo-workspace-sidebar__root-text">
          <span className="tm-processo-workspace-sidebar__root-code">CFG</span>
          <span className="tm-processo-workspace-sidebar__root-title">Configurações</span>
        </div>
      </div>

      <nav className="tm-processo-workspace-tree" aria-label="Árvore de configurações">
        <ul className="tm-processo-workspace-tree__list" role="tree">
          {filteredNodes.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              activeNodeId={activeNodeId}
              expandedIds={expandedIds}
              onToggle={toggleNode}
              onNavigate={onNavigate}
            />
          ))}
        </ul>
        {filteredNodes.length === 0 ? (
          <p className="ds-hint tm-processo-workspace-sidebar__empty">Nenhum item encontrado.</p>
        ) : null}
      </nav>

      {footerActions ? (
        <div className="tm-processo-workspace-sidebar__footer">
          <div className="tm-processo-workspace-sidebar__actions tm-processo-workspace-sidebar__actions--process">
            {footerActions}
          </div>
        </div>
      ) : null}
    </aside>
  );
}
