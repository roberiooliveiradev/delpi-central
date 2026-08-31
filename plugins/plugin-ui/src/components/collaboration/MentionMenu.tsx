import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type RefObject,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { InitialsAvatar, initialsAvatarBemClasses } from "../layout/InitialsAvatar";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

const MENU_AVATAR_CLASSES = initialsAvatarBemClasses("delpi-ui-mention-menu");

export type MentionMenuHit = {
  id: string;
  kind: string;
  label: string;
  subtitle?: string;
  groupLabel?: string;
  /** Optional photo URL — host resolves; kit does not fetch. */
  avatarSrc?: string | null;
  /** Name for initials when photo is missing (user hits). */
  avatarName?: string | null;
};

export type MentionMenuClassNames = {
  panel: string;
  list: string;
  group: string;
  option: string;
  optionActive: string;
  optionAvatar: string;
  optionLabel: string;
  optionSubtitle: string;
  empty: string;
};

export type MentionMenuProps = {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  hits: readonly MentionMenuHit[];
  onSelect: (hit: MentionMenuHit) => void;
  onDismiss: () => void;
  classNames: MentionMenuClassNames;
  /** Accessible name of the listbox (host-provided). */
  listAriaLabel: string;
  /** Shown when `hits` is empty (host-provided). */
  emptyLabel: string;
  portalScopeClassName?: string;
  /** Controlled highlight index (flat order of hits). */
  activeIndex?: number;
  onActiveIndexChange?: (index: number) => void;
};

export function mentionMenuBemClasses(prefix: string): MentionMenuClassNames {
  const base = `${prefix}-mention-menu`;
  const ui = "delpi-ui-mention-menu";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    panel: pair(base, ui),
    list: pair(`${base}__list`, `${ui}__list`),
    group: pair(`${base}__group`, `${ui}__group`),
    option: pair(`${base}__option`, `${ui}__option`),
    optionActive: pair(
      `${base}__option ${base}__option--active`,
      `${ui}__option ${ui}__option--active`,
    ),
    optionAvatar: pair(`${base}__option-avatar`, `${ui}__option-avatar`),
    optionLabel: pair(`${base}__option-label`, `${ui}__option-label`),
    optionSubtitle: pair(`${base}__option-subtitle`, `${ui}__option-subtitle`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
  };
}

type HitGroup = {
  groupLabel: string | null;
  items: MentionMenuHit[];
};

export function groupMentionMenuHits(hits: readonly MentionMenuHit[]): HitGroup[] {
  const groups: HitGroup[] = [];
  const indexByLabel = new Map<string, number>();

  for (const hit of hits) {
    const label = (hit.groupLabel ?? "").trim() || null;
    const key = label ?? "";
    let idx = indexByLabel.get(key);
    if (idx === undefined) {
      idx = groups.length;
      indexByLabel.set(key, idx);
      groups.push({ groupLabel: label, items: [] });
    }
    groups[idx]!.items.push(hit);
  }
  return groups;
}

/**
 * Listbox of @ mention suggestions. Hits/labels come from the host.
 * Uses AnchoredPanelPortal — do not reimplement portal in MFEs.
 */
export function MentionMenu({
  open,
  anchorRef,
  hits,
  onSelect,
  onDismiss,
  classNames,
  listAriaLabel,
  emptyLabel,
  portalScopeClassName,
  activeIndex: activeIndexProp,
  onActiveIndexChange,
}: MentionMenuProps) {
  const listId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const [internalActive, setInternalActive] = useState(0);
  const controlled = typeof activeIndexProp === "number";
  const activeIndex = controlled
    ? Math.min(Math.max(0, activeIndexProp), Math.max(0, hits.length - 1))
    : internalActive;

  const setActive = (index: number) => {
    const next = hits.length === 0 ? 0 : Math.min(Math.max(0, index), hits.length - 1);
    if (!controlled) setInternalActive(next);
    onActiveIndexChange?.(next);
  };

  useEffect(() => {
    if (!open) return;
    if (!controlled) setInternalActive(0);
    onActiveIndexChange?.(0);
  }, [open, hits, controlled, onActiveIndexChange]);

  const groups = useMemo(() => groupMentionMenuHits(hits), [hits]);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        event.stopPropagation();
        if (hits.length === 0) return;
        const next = (activeIndex + 1) % hits.length;
        if (!controlled) setInternalActive(next);
        onActiveIndexChange?.(next);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        event.stopPropagation();
        if (hits.length === 0) return;
        const next = (activeIndex - 1 + hits.length) % hits.length;
        if (!controlled) setInternalActive(next);
        onActiveIndexChange?.(next);
        return;
      }
      if (event.key === "Enter" || event.key === "Tab") {
        if (hits.length === 0) return;
        event.preventDefault();
        event.stopPropagation();
        const hit = hits[activeIndex];
        if (hit) onSelect(hit);
      }
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [open, hits, activeIndex, controlled, onSelect, onActiveIndexChange]);

  let flatIndex = 0;

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      className={classNames.panel}
      variant="bare"
      role="presentation"
      preferredPlacement="top"
      matchAnchorWidth
      portalScopeClassName={portalScopeClassName}
      onDismiss={onDismiss}
      density="compact"
    >
      {hits.length === 0 ? (
        <div className={classNames.empty} role="status">
          {emptyLabel}
        </div>
      ) : (
        <ul
          id={listId}
          className={classNames.list}
          role="listbox"
          aria-label={listAriaLabel}
          aria-activedescendant={`${listId}-opt-${activeIndex}`}
        >
          {groups.map((group) => (
            <li key={group.groupLabel ?? "__default"} role="presentation">
              {group.groupLabel ? (
                <div className={classNames.group}>{group.groupLabel}</div>
              ) : null}
              {group.items.map((hit) => {
                const index = flatIndex;
                flatIndex += 1;
                const active = index === activeIndex;
                return (
                  <div
                    key={hit.id}
                    id={`${listId}-opt-${index}`}
                    role="option"
                    aria-selected={active}
                    className={active ? classNames.optionActive : classNames.option}
                    data-mention-kind={hit.kind}
                    onMouseEnter={() => setActive(index)}
                    onMouseDown={(event) => {
                      event.preventDefault();
                      onSelect(hit);
                    }}
                  >
                    {(hit.avatarSrc || hit.avatarName) ? (
                      <InitialsAvatar
                        name={(hit.avatarName || hit.label).trim() || hit.label}
                        src={(hit.avatarSrc ?? "").trim() || null}
                        size="sm"
                        previewable={false}
                        classNames={MENU_AVATAR_CLASSES}
                        className={classNames.optionAvatar}
                      />
                    ) : null}
                    <span className="delpi-ui-mention-menu__option-text">
                      <span className={classNames.optionLabel}>{hit.label}</span>
                      {hit.subtitle ? (
                        <span className={classNames.optionSubtitle}>{hit.subtitle}</span>
                      ) : null}
                    </span>
                  </div>
                );
              })}
            </li>
          ))}
        </ul>
      )}
    </AnchoredPanelPortal>
  );
}

export type DashboardMentionMenuProps = Omit<MentionMenuProps, "classNames">;

export function createDashboardMentionMenu(prefix: string) {
  const classNames = mentionMenuBemClasses(prefix);
  return function DashboardMentionMenu(props: DashboardMentionMenuProps) {
    return <MentionMenu classNames={classNames} {...props} />;
  };
}
