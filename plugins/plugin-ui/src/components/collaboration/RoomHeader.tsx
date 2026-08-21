import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  AvatarStack,
  avatarStackBemClasses,
  type AvatarStackClassNames,
  type AvatarStackItem,
} from "../layout/AvatarStack";
import {
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "../layout/InitialsAvatar";

export type RoomHeaderClassNames = {
  root: string;
  titles: string;
  title: string;
  titleButton: string;
  subtitle: string;
  chips: string;
  chip: string;
  nav: string;
  people: string;
  actions: string;
  avatars: AvatarStackClassNames;
  avatar: InitialsAvatarClassNames;
};

export type RoomHeaderProps = {
  title: string;
  classNames: RoomHeaderClassNames;
  subtitle?: ReactNode;
  chips?: ReactNode;
  /** Inline view switcher (e.g. Chat | Shared) after avatars, before actions. */
  nav?: ReactNode;
  /** Makes the title a control that opens the linked entity (order, etc.). */
  onTitleClick?: () => void;
  /** Accessible name when title is clickable (e.g. «Abrir pedido»). */
  titleActionLabel?: string;
  participants?: AvatarStackItem[];
  participantsAriaLabel?: string;
  actions?: ReactNode;
  className?: string;
};

export function roomHeaderBemClasses(prefix: string): RoomHeaderClassNames {
  const base = `${prefix}-room-header`;
  const ui = "delpi-ui-room-header";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    titles: pair(`${base}__titles`, `${ui}__titles`),
    title: pair(`${base}__title`, `${ui}__title`),
    titleButton: pair(`${base}__title-button`, `${ui}__title-button`),
    subtitle: pair(`${base}__subtitle`, `${ui}__subtitle`),
    chips: pair(`${base}__chips`, `${ui}__chips`),
    chip: pair(`${base}__chip`, `${ui}__chip`),
    nav: pair(`${base}__nav`, `${ui}__nav`),
    people: pair(`${base}__people`, `${ui}__people`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    avatars: avatarStackBemClasses(prefix),
    avatar: initialsAvatarBemClasses(prefix),
  };
}

/**
 * Room header: title (optional entity link), chips, then people cluster
 * (AvatarStack → optional nav → actions).
 */
export function RoomHeader({
  title,
  classNames,
  subtitle,
  chips,
  nav,
  onTitleClick,
  titleActionLabel,
  participants = [],
  participantsAriaLabel,
  actions,
  className,
}: RoomHeaderProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <header className={rootClass}>
      <div className={classNames.titles}>
        <h2 className={classNames.title}>
          {onTitleClick ? (
            <button
              type="button"
              className={classNames.titleButton}
              onClick={onTitleClick}
              aria-label={titleActionLabel || title}
              title={titleActionLabel || title}
            >
              {title}
            </button>
          ) : (
            title
          )}
        </h2>
        {subtitle ? <span className={classNames.subtitle}>{subtitle}</span> : null}
        {chips ? <div className={classNames.chips}>{chips}</div> : null}
      </div>
      <div className={classNames.people}>
        {participants.length > 0 ? (
          <AvatarStack
            classNames={classNames.avatars}
            avatarClassNames={classNames.avatar}
            items={participants}
            aria-label={participantsAriaLabel}
            max={5}
            size="sm"
          />
        ) : null}
        {nav ? <div className={classNames.nav}>{nav}</div> : null}
        {actions ? <div className={classNames.actions}>{actions}</div> : null}
      </div>
    </header>
  );
}

export type DashboardRoomHeaderProps = Omit<RoomHeaderProps, "classNames">;

export function createDashboardRoomHeader(prefix: string) {
  const classNames = roomHeaderBemClasses(prefix);
  return function DashboardRoomHeader(props: DashboardRoomHeaderProps) {
    return <RoomHeader classNames={classNames} {...props} />;
  };
}
