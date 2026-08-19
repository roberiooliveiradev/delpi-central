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
  subtitle: string;
  chips: string;
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
    subtitle: pair(`${base}__subtitle`, `${ui}__subtitle`),
    chips: pair(`${base}__chips`, `${ui}__chips`),
    people: pair(`${base}__people`, `${ui}__people`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    avatars: avatarStackBemClasses(prefix),
    avatar: initialsAvatarBemClasses(prefix),
  };
}

/**
 * Room header: title, chip slot, AvatarStack participants, actions slot.
 */
export function RoomHeader({
  title,
  classNames,
  subtitle,
  chips,
  participants = [],
  participantsAriaLabel,
  actions,
  className,
}: RoomHeaderProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <header className={rootClass}>
      <div className={classNames.titles}>
        <h2 className={classNames.title}>{title}</h2>
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
