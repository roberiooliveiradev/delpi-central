import type { PointerEvent as ReactPointerEvent, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { DeckSectionHeader } from "./DeckSectionHeader";

export type DeckSectionListItem = {
  id: string;
  name: string;
  collapsed?: boolean;
  inactive?: boolean;
  slideCount: number;
  children?: ReactNode;
};

export type DeckSectionListProps = {
  sections: DeckSectionListItem[];
  /** Slides sem seção (bucket implícito). */
  unsectioned?: ReactNode;
  unsectionedLabel?: string;
  unsectionedCount?: number;
  prefix?: string;
  onToggleCollapsed?: (sectionId: string) => void;
  onNameChange?: (sectionId: string, name: string) => void;
  onNameCommit?: (sectionId: string, name: string) => void;
  onSectionMenuPointerDown?: (
    sectionId: string,
    event: ReactPointerEvent<HTMLButtonElement>,
  ) => void;
  /** Slot após o header (ex.: handles de DnD do MFE). */
  renderSectionChrome?: (section: DeckSectionListItem) => ReactNode;
};

export function deckSectionListBemClasses(prefix = "delpi-ui") {
  const local = `${prefix}-deck-section-list`;
  const ui = "delpi-ui-deck-section-list";
  const pair = (a: string, b: string) => delpiUiClass(a, b);
  return {
    root: pair(local, ui),
    section: pair(`${local}__section`, `${ui}__section`),
    body: pair(`${local}__body`, `${ui}__body`),
    unsectioned: pair(`${local}__unsectioned`, `${ui}__unsectioned`),
  };
}

/**
 * Lista seção → filhos (slots). O MFE injeta cards de slide / DnD nos children.
 */
export function DeckSectionList({
  sections,
  unsectioned,
  unsectionedLabel = "Sem seção",
  unsectionedCount = 0,
  prefix = "td",
  onToggleCollapsed,
  onNameChange,
  onNameCommit,
  onSectionMenuPointerDown,
  renderSectionChrome,
}: DeckSectionListProps) {
  const cn = deckSectionListBemClasses(prefix);

  return (
    <div className={cn.root} data-deck-section-list="">
      {unsectioned != null ? (
        <div className={cn.unsectioned} data-deck-unsectioned="">
          <DeckSectionHeader
            prefix={prefix}
            name={unsectionedLabel}
            slideCount={unsectionedCount}
            nameEditable={false}
            collapsed={false}
          />
          <div className={cn.body}>{unsectioned}</div>
        </div>
      ) : null}
      {sections.map((section) => {
        const collapsed = Boolean(section.collapsed);
        return (
          <div
            key={section.id}
            className={cn.section}
            data-section-id={section.id}
            data-collapsed={collapsed ? "true" : "false"}
          >
            <DeckSectionHeader
              prefix={prefix}
              name={section.name}
              slideCount={section.slideCount}
              collapsed={collapsed}
              inactive={section.inactive}
              onToggleCollapsed={() => onToggleCollapsed?.(section.id)}
              onNameChange={(name) => onNameChange?.(section.id, name)}
              onNameCommit={(name) => onNameCommit?.(section.id, name)}
              onMenuPointerDown={
                onSectionMenuPointerDown
                  ? (event) => onSectionMenuPointerDown(section.id, event)
                  : undefined
              }
            />
            {renderSectionChrome?.(section)}
            {!collapsed ? <div className={cn.body}>{section.children}</div> : null}
          </div>
        );
      })}
    </div>
  );
}
