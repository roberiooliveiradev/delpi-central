import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import {
  RibbonGroup,
  ribbonGroupBemClasses,
  type RibbonGroupProps,
} from "./RibbonGroup";
import {
  RibbonGroupsRow,
  ribbonGroupsRowBemClasses,
  type RibbonGroupsRowProps,
} from "./RibbonGroupsRow";

const SECTION_CN = ribbonGroupBemClasses("delpi-ui");
const SECTIONS_CN = ribbonGroupsRowBemClasses("delpi-ui");

export type EditorRibbonSectionProps = {
  /** Id estável obrigatório para overflow responsivo. */
  groupId: string;
  label: string;
  hint?: string;
  wide?: boolean;
  captionPlacement?: RibbonGroupProps["captionPlacement"];
  order?: number;
  collapseIcon?: LucideIcon;
  className?: string;
  children: ReactNode;
};

/**
 * Seção de ribbon de editor (caption abaixo, tiles dentro).
 * Colapsa em popover via {@link RibbonGroup} + {@link RibbonGroupsRow}.
 */
export function EditorRibbonSection({
  groupId,
  label,
  hint,
  wide,
  captionPlacement = "below",
  order,
  collapseIcon,
  className,
  children,
}: EditorRibbonSectionProps) {
  return (
    <RibbonGroup
      groupId={groupId}
      label={label}
      hint={hint}
      wide={wide}
      captionPlacement={captionPlacement}
      order={order}
      collapseIcon={collapseIcon}
      className={className}
      classNames={SECTION_CN}
    >
      {children}
    </RibbonGroup>
  );
}

export type EditorRibbonSectionsProps = {
  children: ReactNode;
  gap?: number;
  className?: string;
  portalScopeClassName?: string;
  overflowEnabled?: boolean;
};

/** Faixa de seções com colapso direita→esquerda (kit). */
export function EditorRibbonSections({
  children,
  gap = 8,
  className,
  portalScopeClassName,
  overflowEnabled = true,
}: EditorRibbonSectionsProps) {
  const rowProps: RibbonGroupsRowProps = {
    children,
    gap,
    className,
    classNames: SECTIONS_CN,
    portalScopeClassName,
    overflowEnabled,
  };
  return <RibbonGroupsRow {...rowProps} />;
}
