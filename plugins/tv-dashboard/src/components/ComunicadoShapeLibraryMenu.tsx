import { useRef } from "react";
import {
  AnchoredPanelPortal,
  HintAction,
  useRibbonSectionPopoverSurface,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  ComunicadoShapePreview,
  comunicadoShapeLabel,
  isLineShapeKind,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { readRecentComunicadoShapes } from "../utils/comunicadoRecentShapes";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  onSelect: (kind: ComunicadoShapeKind) => void;
  onDismiss: () => void;
};

export function ComunicadoShapeLibraryMenu({ open, anchorRef, onSelect, onDismiss }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();
  const recent = readRecentComunicadoShapes();

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className="delpi-ui-popover-surface td-shape-library td-shape-library--portal"
      role="menu"
      aria-label="Biblioteca de formas"
      density="compact"
      exclusive={!inSectionPopover}
      onDismiss={onDismiss}
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
    </AnchoredPanelPortal>
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
  const hintBase = isLineShapeKind(kind) ? (H.insertLineShape ?? H.insertShape) : H.insertShape;

  return (
    <HintAction hint={`${hintBase} — ${label}`} ariaLabel={`Inserir ${label}`} placement="top">
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
