import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import {
  AnchoredPanelPortal,
  HintAction,
  useRibbonSectionPopoverSurface,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES,
  ComunicadoShapePreview,
  comunicadoShapeLabel,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { readRecentComunicadoShapes } from "../utils/comunicadoRecentShapes";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const RECENT_CATEGORY_ID = "__recent__";

type Props = {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  onSelect: (kind: ComunicadoShapeKind) => void;
  onDismiss: () => void;
};

/**
 * Flyout Inserir → Formas:
 * lista lateral Formas / Setas / Descrições / Equação + grade à direita.
 */
export function ComunicadoShapeLibraryMenu({ open, anchorRef, onSelect, onDismiss }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();
  const recent = useMemo(() => readRecentComunicadoShapes(), [open]);
  const flyoutCategories = COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES;
  const defaultCategoryId =
    recent.length > 0 ? RECENT_CATEGORY_ID : (flyoutCategories[0]?.id ?? "formas");
  const [activeCategoryId, setActiveCategoryId] = useState(defaultCategoryId);

  useEffect(() => {
    if (!open) return;
    setActiveCategoryId(recent.length > 0 ? RECENT_CATEGORY_ID : (flyoutCategories[0]?.id ?? "formas"));
  }, [open, recent.length, flyoutCategories]);

  const activeShapes: ComunicadoShapeKind[] = useMemo(() => {
    if (activeCategoryId === RECENT_CATEGORY_ID) return recent;
    return flyoutCategories.find((category) => category.id === activeCategoryId)?.shapes ?? [];
  }, [activeCategoryId, flyoutCategories, recent]);

  const activeTitle =
    activeCategoryId === RECENT_CATEGORY_ID
      ? "Usadas recentemente"
      : (flyoutCategories.find((category) => category.id === activeCategoryId)?.label ?? "Formas");

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className="delpi-ui-popover-surface td-shape-library td-shape-library--portal td-shape-library--flyout"
      role="menu"
      aria-label="Biblioteca de formas"
      density="compact"
      exclusive={!inSectionPopover}
      onDismiss={onDismiss}
    >
      <div className="td-shape-library__flyout">
        <nav className="td-shape-library__nav" aria-label="Categorias de formas">
          {recent.length ? (
            <button
              type="button"
              role="menuitem"
              className={[
                "td-shape-library__nav-item",
                activeCategoryId === RECENT_CATEGORY_ID ? "td-shape-library__nav-item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-current={activeCategoryId === RECENT_CATEGORY_ID ? "true" : undefined}
              onMouseEnter={() => setActiveCategoryId(RECENT_CATEGORY_ID)}
              onFocus={() => setActiveCategoryId(RECENT_CATEGORY_ID)}
              onClick={() => setActiveCategoryId(RECENT_CATEGORY_ID)}
            >
              <span className="td-shape-library__nav-label">Usadas recentemente</span>
              <ChevronRight size={14} strokeWidth={2} aria-hidden="true" />
            </button>
          ) : null}
          {flyoutCategories.map((category) => {
            const active = activeCategoryId === category.id;
            return (
              <button
                key={category.id}
                type="button"
                role="menuitem"
                className={[
                  "td-shape-library__nav-item",
                  active ? "td-shape-library__nav-item--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-current={active ? "true" : undefined}
                onMouseEnter={() => setActiveCategoryId(category.id)}
                onFocus={() => setActiveCategoryId(category.id)}
                onClick={() => setActiveCategoryId(category.id)}
              >
                <span className="td-shape-library__nav-label">{category.label}</span>
                <ChevronRight size={14} strokeWidth={2} aria-hidden="true" />
              </button>
            );
          })}
        </nav>
        <section className="td-shape-library__panel" aria-label={activeTitle}>
          <h4 className="td-shape-library__title">{activeTitle}</h4>
          <div className="td-shape-library__grid">
            {activeShapes.map((kind) => (
              <ShapeLibraryButton
                key={`${activeCategoryId}-${kind}`}
                kind={kind}
                onSelect={onSelect}
              />
            ))}
          </div>
        </section>
      </div>
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

  return (
    <HintAction hint={`${H.insertShape} — ${label}`} ariaLabel={`Inserir ${label}`} placement="top">
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
