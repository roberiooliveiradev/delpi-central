import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";

import {
  collectExpandedNodeIds,
  filterWorkspaceTree,
  type ProcessoWorkspaceNavNode,
} from "./processoWorkspaceNav";

type Props = {
  processoLabel: string;
  processoCode: string;
  nodes: ProcessoWorkspaceNavNode[];
  activeNodeId: string;
  onNavigate: (href: string) => void;
};

function TreeNode({
  node,
  activeNodeId,
  expandedIds,
  onToggle,
  onNavigate,
}: {
  node: ProcessoWorkspaceNavNode;
  activeNodeId: string;
  expandedIds: Set<string>;
  onToggle: (nodeId: string) => void;
  onNavigate: (href: string) => void;
}) {
  const hasChildren = Boolean(node.children?.length);
  const isExpanded = expandedIds.has(node.id);
  const isActive = node.id === activeNodeId;

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
        <button
          type="button"
          className="tm-processo-workspace-tree__link"
          onClick={() => onNavigate(node.href)}
        >
          <span className="tm-processo-workspace-tree__label">{node.label}</span>
          {node.badge ? <span className="tm-processo-workspace-tree__badge">{node.badge}</span> : null}
        </button>
      </div>
      {hasChildren && isExpanded ? (
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
      ) : null}
    </li>
  );
}

export function ProcessoWorkspaceSidebar({
  processoLabel,
  processoCode,
  nodes,
  activeNodeId,
  onNavigate,
}: Props) {
  const [query, setQuery] = useState("");
  const filteredNodes = useMemo(() => filterWorkspaceTree(nodes, query), [nodes, query]);

  const autoExpanded = useMemo(
    () => collectExpandedNodeIds(nodes, activeNodeId),
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

  return (
    <aside className="tm-processo-workspace-sidebar" aria-label="Navegação do processo">
      <div className="tm-processo-workspace-sidebar__search">
        <Search size={15} aria-hidden="true" />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Pesquisar tópicos, melhorias, revisões…"
          aria-label="Pesquisar na árvore do processo"
        />
      </div>

      <div className="tm-processo-workspace-sidebar__root">
        <span className="tm-processo-workspace-sidebar__root-code">{processoCode}</span>
        <span className="tm-processo-workspace-sidebar__root-title">{processoLabel}</span>
      </div>

      <nav className="tm-processo-workspace-tree" aria-label="Árvore do processo">
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
    </aside>
  );
}
