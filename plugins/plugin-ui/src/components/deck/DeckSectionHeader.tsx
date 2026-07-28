import type { PointerEvent as ReactPointerEvent, ReactNode } from "react";
import { ChevronDown, ChevronRight, MoreHorizontal } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type DeckSectionHeaderProps = {
  name: string;
  slideCount: number;
  collapsed?: boolean;
  inactive?: boolean;
  /** Prefixo BEM do MFE (ex.: `td-composer`). */
  prefix?: string;
  nameEditable?: boolean;
  onToggleCollapsed?: () => void;
  onNameChange?: (name: string) => void;
  onNameCommit?: (name: string) => void;
  onMenuPointerDown?: (event: ReactPointerEvent<HTMLButtonElement>) => void;
  trailing?: ReactNode;
};

export function deckSectionHeaderBemClasses(prefix = "delpi-ui") {
  const local = `${prefix}-deck-section-header`;
  const ui = "delpi-ui-deck-section-header";
  const pair = (a: string, b: string) => delpiUiClass(a, b);
  return {
    root: pair(local, ui),
    toggle: pair(`${local}__toggle`, `${ui}__toggle`),
    name: pair(`${local}__name`, `${ui}__name`),
    count: pair(`${local}__count`, `${ui}__count`),
    menu: pair(`${local}__menu`, `${ui}__menu`),
    trailing: pair(`${local}__trailing`, `${ui}__trailing`),
  };
}

/**
 * Cabeçalho colapsável de seção de slides (filmstrip) — visual só via `.delpi-ui-deck-section-*`.
 */
export function DeckSectionHeader({
  name,
  slideCount,
  collapsed = false,
  inactive = false,
  prefix = "td",
  nameEditable = true,
  onToggleCollapsed,
  onNameChange,
  onNameCommit,
  onMenuPointerDown,
  trailing,
}: DeckSectionHeaderProps) {
  const cn = deckSectionHeaderBemClasses(prefix);
  const Chevron = collapsed ? ChevronRight : ChevronDown;

  return (
    <div
      className={[cn.root, inactive ? "delpi-ui-deck-section-header--inactive" : ""]
        .filter(Boolean)
        .join(" ")}
      data-deck-section-header=""
      data-collapsed={collapsed ? "true" : "false"}
    >
      <button
        type="button"
        className={cn.toggle}
        aria-expanded={!collapsed}
        aria-label={collapsed ? "Expandir seção" : "Recolher seção"}
        onClick={() => onToggleCollapsed?.()}
      >
        <Chevron size={14} strokeWidth={2} aria-hidden />
      </button>
      {nameEditable ? (
        <input
          className={cn.name}
          value={name}
          aria-label="Nome da seção"
          onChange={(event) => onNameChange?.(event.target.value)}
          onBlur={(event) => onNameCommit?.(event.target.value.trim() || name)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              (event.target as HTMLInputElement).blur();
            }
          }}
        />
      ) : (
        <span className={cn.name}>{name}</span>
      )}
      <span className={cn.count} aria-label={`${slideCount} slides`}>
        {slideCount}
      </span>
      {onMenuPointerDown ? (
        <button
          type="button"
          className={cn.menu}
          aria-label="Menu da seção"
          title="Menu da seção"
          onPointerDown={onMenuPointerDown}
        >
          <MoreHorizontal size={14} strokeWidth={2} aria-hidden />
        </button>
      ) : null}
      {trailing ? <div className={cn.trailing}>{trailing}</div> : null}
    </div>
  );
}
