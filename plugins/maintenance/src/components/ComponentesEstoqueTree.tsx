import { ChevronDown, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { TreeGuideRails } from "@delpi/plugin-ui/index";

import type { ComponenteItem } from "../data/api/maintenanceApi";
import {
  buildComponentesForest,
  countComponenteTreeNodes,
  type ComponenteTreeNode,
} from "../utils/componentesTree";

type ComponentesEstoqueTreeProps = {
  items: ComponenteItem[];
  /** Expandir automaticamente até esta profundidade (0 = só raiz). */
  expandDepth?: number;
};

function ComponenteTreeRow({
  node,
  depth,
  isLastSiblingPath,
  expandDepth,
}: {
  node: ComponenteTreeNode;
  depth: number;
  isLastSiblingPath: readonly boolean[];
  expandDepth: number;
}) {
  const hasChildren = node.children.length > 0;
  const [expanded, setExpanded] = useState(depth <= expandDepth);
  const { item } = node;

  return (
    <li className="dm-componentes-tree__item">
      <div className="dm-componentes-tree__row">
        <TreeGuideRails depth={depth} isLastSiblingPath={isLastSiblingPath} />

        {hasChildren ? (
          <button
            type="button"
            className={[
              "dm-componentes-tree__toggle",
              expanded ? "dm-componentes-tree__toggle--expanded" : "dm-componentes-tree__toggle--collapsed",
            ].join(" ")}
            aria-label={expanded ? `Recolher ${item.codigo}` : `Expandir ${item.codigo}`}
            aria-expanded={expanded}
            onClick={() => setExpanded((current) => !current)}
          >
            {expanded ? (
              <ChevronDown size={14} aria-hidden="true" />
            ) : (
              <ChevronRight size={14} aria-hidden="true" />
            )}
          </button>
        ) : (
          <span className="dm-componentes-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="dm-componentes-tree__content">
          <div className="dm-componentes-tree__primary">
            <span className="dm-componentes-tree__code">{item.codigo}</span>
            <span className="dm-componentes-tree__desc">{item.descricao}</span>
            <span className="dm-componentes-tree__stock">
              01: {item.estoque_local_01.toLocaleString("pt-BR")} · 99:{" "}
              {item.estoque_local_99.toLocaleString("pt-BR")}
            </span>
          </div>
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="dm-componentes-tree__children" role="group">
          {node.children.map((child, index) => (
            <ComponenteTreeRow
              key={`${child.item.codigo}-${child.item.nivel}-${index}`}
              node={child}
              depth={depth + 1}
              isLastSiblingPath={[...isLastSiblingPath, index === node.children.length - 1]}
              expandDepth={expandDepth}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function ComponentesEstoqueTree({ items, expandDepth = 1 }: ComponentesEstoqueTreeProps) {
  const forest = useMemo(() => buildComponentesForest(items), [items]);
  const nodeCount = useMemo(() => countComponenteTreeNodes(forest), [forest]);

  if (items.length === 0) {
    return <p className="dm-chart-empty">Nenhum componente amarrado a esta ferramenta.</p>;
  }

  return (
    <div className="dm-componentes-tree">
      <div className="dm-componentes-tree__scroll">
        <ul className="dm-componentes-tree__list" role="tree" aria-label="Componentes e estoque">
          {forest.map((node, index) => (
            <ComponenteTreeRow
              key={`${node.item.codigo}-${node.item.nivel}-${index}`}
              node={node}
              depth={0}
              isLastSiblingPath={[]}
              expandDepth={expandDepth}
            />
          ))}
        </ul>
      </div>
      <p className="dm-componentes-tree__footer">{nodeCount} componente(s)</p>
    </div>
  );
}
