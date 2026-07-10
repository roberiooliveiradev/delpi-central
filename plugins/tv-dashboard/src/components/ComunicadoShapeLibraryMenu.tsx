import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";
import { createPortal } from "react-dom";
import { HintAction } from "@delpi/plugin-ui/index";
import {
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  ComunicadoShapePreview,
  comunicadoShapeLabel,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { readRecentComunicadoShapes } from "../utils/comunicadoRecentShapes";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  anchorRef: RefObject<HTMLDivElement | null>;
  onSelect: (kind: ComunicadoShapeKind) => void;
};

export function ComunicadoShapeLibraryMenu({ anchorRef, onSelect }: Props) {
  const [style, setStyle] = useState<CSSProperties>({ visibility: "hidden" });
  const recent = readRecentComunicadoShapes();

  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    if (!anchor) return;

    const rect = anchor.getBoundingClientRect();
    const panelWidth = 360;
    const left = Math.min(Math.max(8, rect.left), window.innerWidth - panelWidth - 8);

    setStyle({
      position: "fixed",
      top: rect.bottom + 4,
      left,
      width: panelWidth,
      maxHeight: "min(70vh, 520px)",
      zIndex: 5000,
      visibility: "visible",
    });
  }, [anchorRef]);

  return createPortal(
    <div
      className="td-shape-library td-shape-library--portal"
      role="menu"
      aria-label="Biblioteca de formas"
      style={style}
    >
      {recent.length ? (
        <section className="td-shape-library__section">
          <h4 className="td-shape-library__title">Usadas recentemente</h4>
          <div className="td-shape-library__grid">
            {recent.map((kind) => (
              <ShapeLibraryButton key={`recent-${kind}`} kind={kind} onSelect={onSelect} />
            ))}
          </div>
        </section>
      ) : null}

      {COMUNICADO_SHAPE_CATALOG_CATEGORIES.map((category) => (
        <section key={category.id} className="td-shape-library__section">
          <h4 className="td-shape-library__title">{category.label}</h4>
          <div className="td-shape-library__grid">
            {category.shapes.map((kind) => (
              <ShapeLibraryButton key={kind} kind={kind} onSelect={onSelect} />
            ))}
          </div>
        </section>
      ))}
    </div>,
    document.body,
  );
}

function ShapeLibraryButton({
  kind,
  onSelect,
}: {
  kind: ComunicadoShapeKind;
  onSelect: (kind: ComunicadoShapeKind) => void;
}) {
  const label = comunicadoShapeLabel(kind);

  return (
    <HintAction hint={`${H.insertShape} — ${label}`} ariaLabel={`Inserir ${label}`} placement="right">
      <button
        type="button"
        role="menuitem"
        className="td-shape-library__item"
        aria-label={label}
        onClick={() => onSelect(kind)}
      >
        <ComunicadoShapePreview kind={kind} className="td-shape-library__preview" />
        <span className="td-shape-library__label">{label}</span>
      </button>
    </HintAction>
  );
}
