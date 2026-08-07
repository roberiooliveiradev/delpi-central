import { useMemo, useState } from "react";
import { StatusBadge, TreeGuideRails } from "@delpi/plugin-ui/index";

import { cmStatusBadgeClassNames } from "../app/commercialUi";
import type { ProductStructureNode } from "../types/productionExtras";
import { formatQuantity } from "../utils/format";
import {
  countStructureNodes,
  structureNodeChildren,
  structureNodeCode,
  structureNodeTypeBadgeVariant,
  structureNodeTypeLabel,
} from "../utils/productStructurePresentation";

type ProductStructureTreeProps = {
  nodes: ProductStructureNode[];
  /** Expandir automaticamente até esta profundidade (0 = só raiz). */
  expandDepth?: number;
  caption?: string | null;
};

function TreeChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className="cm-product-structure-tree__toggle-icon"
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

function StructureNodeRow({
  node,
  depth,
  isLastSiblingPath,
  expandDepth,
}: {
  node: ProductStructureNode;
  depth: number;
  isLastSiblingPath: readonly boolean[];
  expandDepth: number;
}) {
  const children = structureNodeChildren(node);
  const hasChildren = children.length > 0;
  const [expanded, setExpanded] = useState(depth <= expandDepth);
  const code = structureNodeCode(node);
  const typeLabel = structureNodeTypeLabel(node);
  const description = String(node.description ?? "").trim();
  const qty =
    node.quantity != null && !Number.isNaN(Number(node.quantity))
      ? `${formatQuantity(Number(node.quantity))}${node.unit ? ` ${node.unit}` : ""}`
      : null;

  return (
    <li className="cm-product-structure-tree__item">
      <div className="cm-product-structure-tree__row">
        <TreeGuideRails depth={depth} isLastSiblingPath={isLastSiblingPath} />

        {hasChildren ? (
          <button
            type="button"
            className={[
              "cm-product-structure-tree__toggle",
              expanded
                ? "cm-product-structure-tree__toggle--expanded"
                : "cm-product-structure-tree__toggle--collapsed",
            ].join(" ")}
            aria-label={expanded ? `Recolher ${code}` : `Expandir ${code}`}
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
          >
            <TreeChevronIcon expanded={expanded} />
          </button>
        ) : (
          <span className="cm-product-structure-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="cm-product-structure-tree__content">
          <div className="cm-product-structure-tree__primary">
            <span className="cm-product-structure-tree__code">{code}</span>
            {typeLabel ? (
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                className="cm-product-structure-tree__type"
                label={typeLabel}
                variant={structureNodeTypeBadgeVariant(typeLabel)}
              />
            ) : null}
            {description ? (
              <span className="cm-product-structure-tree__description">{description}</span>
            ) : null}
            {qty ? <span className="cm-product-structure-tree__qty">× {qty}</span> : null}
          </div>
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="cm-product-structure-tree__children">
          {children.map((child, index) => (
            <StructureNodeRow
              key={`${structureNodeCode(child)}-${depth + 1}-${index}`}
              node={child}
              depth={depth + 1}
              isLastSiblingPath={[...isLastSiblingPath, index === children.length - 1]}
              expandDepth={expandDepth}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

/**
 * Árvore de BOM com trilhos e badges do kit (`TreeGuideRails` + `StatusBadge`).
 */
export function ProductStructureTree({
  nodes,
  expandDepth = 1,
  caption,
}: ProductStructureTreeProps) {
  const nodeCount = useMemo(() => countStructureNodes(nodes), [nodes]);

  if (nodes.length === 0) return null;

  return (
    <div className="cm-product-structure-tree">
      {caption ? <p className="cm-product-structure-tree__caption">{caption}</p> : null}
      <div className="cm-product-structure-tree__scroll">
        <ul className="cm-product-structure-tree__list">
          {nodes.map((node, index) => (
            <StructureNodeRow
              key={`${structureNodeCode(node)}-0-${index}`}
              node={node}
              depth={0}
              isLastSiblingPath={[]}
              expandDepth={expandDepth}
            />
          ))}
        </ul>
      </div>
      <p className="cm-product-structure-tree__footer">{nodeCount} nó(s)</p>
    </div>
  );
}
