import { RibbonGroup, delpiUiClass } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import { useRef, type ReactNode } from "react";

import { resolveDeckRibbonCollapseIcon } from "./deckRibbonCollapseIcons";

/** Dual-class: BEM legado da TV + canônico do kit (overflow / popover). */
export function deckRibbonGroupClassNames() {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair("td-deck-ribbon__group", "delpi-ui-ribbon-group"),
    rootWide: pair("td-deck-ribbon__group--wide", "delpi-ui-ribbon-group--wide"),
    rootCollapsed: pair("td-deck-ribbon__group--collapsed", "delpi-ui-ribbon-group--collapsed"),
    rootNoCaption: pair("td-deck-ribbon__group--no-caption", "delpi-ui-ribbon-group--no-caption"),
    rootCaptionAbove: pair(
      "td-deck-ribbon__group--caption-above",
      "delpi-ui-ribbon-group--caption-above",
    ),
    body: pair("td-deck-ribbon__body", "delpi-ui-ribbon-group__body"),
    caption: pair("td-deck-ribbon__caption", "delpi-ui-ribbon-group__caption"),
    captionAbove: pair("td-deck-ribbon__caption--above", "delpi-ui-ribbon-group__caption--above"),
    captionText: pair("td-deck-ribbon__caption-text", "delpi-ui-ribbon-group__caption-text"),
    collapseTrigger: pair(
      "td-deck-ribbon__collapse-trigger",
      "delpi-ui-ribbon-group__collapse-trigger",
    ),
    collapseIcon: pair("td-deck-ribbon__collapse-icon", "delpi-ui-ribbon-group__collapse-icon"),
    collapseLabel: pair("td-deck-ribbon__collapse-label", "delpi-ui-ribbon-group__collapse-label"),
    collapseChevron: pair(
      "td-deck-ribbon__collapse-chevron",
      "delpi-ui-ribbon-group__collapse-chevron",
    ),
    popover: pair("td-deck-ribbon__group-popover", "delpi-ui-ribbon-group__popover"),
    popoverBody: pair("td-deck-ribbon__group-popover-body", "delpi-ui-ribbon-group__popover-body"),
    popoverCaption: pair(
      "td-deck-ribbon__group-popover-caption",
      "delpi-ui-ribbon-group__popover-caption",
    ),
    measure: pair("td-deck-ribbon__collapse-measure", "delpi-ui-ribbon-group__measure"),
  };
}

const DECK_GROUP_CN = deckRibbonGroupClassNames();

let autoGroupSeq = 0;

function useResolvedGroupId(explicit?: string): string {
  const ref = useRef<string | null>(null);
  if (explicit) {
    ref.current = explicit;
    return explicit;
  }
  if (ref.current == null) {
    autoGroupSeq += 1;
    ref.current = `deck-group-${autoGroupSeq}`;
  }
  return ref.current;
}

type Props = {
  label: string;
  hint?: string;
  wide?: boolean;
  /**
   * `below` — legenda abaixo dos controles (padrão da faixa).
   * `above` — subtítulo no painel embutido.
   * `none` — sem caption (accordion já titulou a seção).
   */
  captionPlacement?: "below" | "above" | "none";
  /** Id estável para overflow responsivo (senão gera id único na montagem). */
  groupId?: string;
  order?: number;
  collapseIcon?: LucideIcon;
  children: ReactNode;
};

/** Grupo da faixa: controles em cima, legenda embaixo — colapsa em popover via kit. */
export function DeckRibbonGroup({
  label,
  hint,
  wide,
  captionPlacement = "below",
  groupId,
  order,
  collapseIcon,
  children,
}: Props) {
  const resolvedId = useResolvedGroupId(groupId);
  const resolvedIcon = resolveDeckRibbonCollapseIcon(
    groupId ? resolvedId : undefined,
    collapseIcon,
  );
  return (
    <RibbonGroup
      groupId={resolvedId}
      label={label}
      hint={hint}
      wide={wide}
      captionPlacement={captionPlacement}
      order={order}
      collapseIcon={resolvedIcon}
      classNames={DECK_GROUP_CN}
    >
      {children}
    </RibbonGroup>
  );
}
