import {
  AnchoredPanelPortal,
  HintAction,
  useRibbonSectionPopoverSurface,
} from "@delpi/plugin-ui/index";
import { ChevronDown, type LucideIcon } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

export type DeckRibbonMenuItem = {
  id: string;
  label: string;
  icon?: LucideIcon;
  disabled?: boolean;
  hint?: string;
  dividerBefore?: boolean;
  onSelect: () => void;
};

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  disabled?: boolean;
  active?: boolean;
  /** Ação principal (clique no corpo). Sem callback, só abre o menu. */
  onPrimaryClick?: () => void;
  items: DeckRibbonMenuItem[];
  /** Conteúdo extra no painel (ex.: toggles). */
  menuFooter?: ReactNode;
  menuAriaLabel?: string;
};

/**
 * Tile da ribbon com menu dropdown (padrão Excel: Avançar▼ / Alinhar▼).
 * Usa AnchoredPanelPortal do kit — sem segundo portal quando já está no popover colapsado.
 */
export function DeckRibbonMenuTile({
  icon: Icon,
  label,
  hint,
  disabled,
  active,
  onPrimaryClick,
  items,
  menuFooter,
  menuAriaLabel,
}: Props) {
  const inSectionPopover = useRibbonSectionPopoverSurface();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const dismiss = () => setOpen(false);
  const enabledItems = items.filter(Boolean);

  const tile = (
    <div
      ref={rootRef}
      className={[
        "td-ribbon-menu-tile",
        active || open ? "td-ribbon-menu-tile--active" : null,
        disabled ? "td-ribbon-menu-tile--disabled" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        type="button"
        className="td-ribbon-menu-tile__primary"
        disabled={disabled}
        aria-label={label}
        onClick={() => {
          if (disabled) return;
          if (onPrimaryClick) {
            onPrimaryClick();
            return;
          }
          setOpen((prev) => !prev);
        }}
      >
        <span className="td-ribbon-menu-tile__icon" aria-hidden="true">
          <Icon size={18} />
        </span>
        <span className="td-ribbon-menu-tile__label">{label}</span>
      </button>
      <button
        type="button"
        className="td-ribbon-menu-tile__chevron"
        disabled={disabled || enabledItems.length === 0}
        aria-label={`${label}: mais opções`}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => {
          if (disabled) return;
          setOpen((prev) => !prev);
        }}
      >
        <ChevronDown size={12} aria-hidden="true" />
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="td-ribbon-menu-tile__panel delpi-ui-shape-menu__panel--narrow"
          role="menu"
          aria-label={menuAriaLabel ?? label}
          exclusive={!inSectionPopover}
          density="compact"
          portalScopeClassName="dashboard-tv-dashboard"
          onDismiss={dismiss}
        >
          <ul className="td-ribbon-menu-tile__list">
            {enabledItems.map((item) => (
              <li key={item.id}>
                {item.dividerBefore ? (
                  <div className="td-ribbon-menu-tile__divider" role="separator" />
                ) : null}
                <button
                  type="button"
                  role="menuitem"
                  className="td-ribbon-menu-tile__item"
                  disabled={item.disabled}
                  title={item.hint}
                  onClick={() => {
                    if (item.disabled) return;
                    item.onSelect();
                    dismiss();
                  }}
                >
                  {item.icon ? (
                    <span className="td-ribbon-menu-tile__item-icon" aria-hidden="true">
                      <item.icon size={16} />
                    </span>
                  ) : null}
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
          {menuFooter ? <div className="td-ribbon-menu-tile__footer">{menuFooter}</div> : null}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );

  if (!hint) return tile;
  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      {tile}
    </HintAction>
  );
}
