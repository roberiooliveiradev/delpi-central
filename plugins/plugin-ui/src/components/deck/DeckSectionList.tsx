import type {
  DragEvent as ReactDragEvent,
  PointerEvent as ReactPointerEvent,
  ReactNode,
} from "react";

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
  emptyDropHint?: string;
  prefix?: string;
  onToggleCollapsed?: (sectionId: string) => void;
  onNameChange?: (sectionId: string, name: string) => void;
  onNameCommit?: (sectionId: string, name: string) => void;
  onSectionMenuPointerDown?: (
    sectionId: string,
    event: ReactPointerEvent<HTMLButtonElement>,
  ) => void;
  /** Soltar slide nesta seção (incluindo vazia). */
  onDropOnSection?: (sectionId: string) => void;
  /** Soltar slide no bucket «Sem seção». */
  onDropOnUnsectioned?: () => void;
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
    dropHint: pair(`${local}__drop-hint`, `${ui}__drop-hint`),
  };
}

function allowDrop(event: ReactDragEvent) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
}

/**
 * Lista seção → filhos (slots). O MFE injeta cards de slide / DnD nos children.
 */
export function DeckSectionList({
  sections,
  unsectioned,
  unsectionedLabel = "Sem seção",
  unsectionedCount = 0,
  emptyDropHint = "Solte telas aqui",
  prefix = "td",
  onToggleCollapsed,
  onNameChange,
  onNameCommit,
  onSectionMenuPointerDown,
  onDropOnSection,
  onDropOnUnsectioned,
  renderSectionChrome,
}: DeckSectionListProps) {
  const cn = deckSectionListBemClasses(prefix);

  return (
    <div className={cn.root} data-deck-section-list="">
      {unsectioned != null ? (
        <div
          className={cn.unsectioned}
          data-deck-unsectioned=""
          onDragOver={onDropOnUnsectioned ? allowDrop : undefined}
          onDrop={
            onDropOnUnsectioned
              ? (event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  onDropOnUnsectioned();
                }
              : undefined
          }
        >
          <DeckSectionHeader
            prefix={prefix}
            name={unsectionedLabel}
            slideCount={unsectionedCount}
            nameEditable={false}
            collapsed={false}
          />
          <div className={cn.body}>
            {unsectionedCount === 0 && onDropOnUnsectioned ? (
              <div className={cn.dropHint} aria-hidden="true">
                {emptyDropHint}
              </div>
            ) : null}
            {unsectioned}
          </div>
        </div>
      ) : null}
      {sections.map((section) => {
        const collapsed = Boolean(section.collapsed);
        const empty = section.slideCount === 0;
        return (
          <div
            key={section.id}
            className={cn.section}
            data-section-id={section.id}
            data-collapsed={collapsed ? "true" : "false"}
            onDragOver={onDropOnSection ? allowDrop : undefined}
            onDrop={
              onDropOnSection
                ? (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    onDropOnSection(section.id);
                  }
                : undefined
            }
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
            {!collapsed ? (
              <div className={cn.body}>
                {empty && onDropOnSection ? (
                  <div className={cn.dropHint} aria-hidden="true">
                    {emptyDropHint}
                  </div>
                ) : null}
                {section.children}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
