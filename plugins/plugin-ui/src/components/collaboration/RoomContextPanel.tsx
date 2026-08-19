import { ExternalLink, Pin } from "lucide-react";
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

export type RoomContextPanelPin = {
  id: string;
  messageId: string;
  title: string;
  dateLabel?: string | null;
};

export type RoomContextPanelClassNames = {
  root: string;
  embedded: string;
  flush: string;
  section: string;
  heading: string;
  body: string;
  aboutRow: string;
  openLink: string;
  empty: string;
  pinList: string;
  pinItem: string;
  pinIcon: string;
  avatars: AvatarStackClassNames;
  avatar: InitialsAvatarClassNames;
};

export type RoomContextPanelLabels = {
  about: string;
  participants: string;
  pins: string;
  pinsEmpty: string;
  membersEmpty: string;
  openEntity: string;
};

export type RoomContextPanelProps = {
  classNames: RoomContextPanelClassNames;
  labels: RoomContextPanelLabels;
  entityTitle?: string | null;
  entityKey?: string | null;
  entityHref?: string | null;
  onOpenEntity?: () => void;
  participants?: AvatarStackItem[];
  participantsAriaLabel?: string;
  pins?: readonly RoomContextPanelPin[];
  onPinSelect?: (messageId: string) => void;
  /** Sem chrome de sidebar/drawer. */
  embedded?: boolean;
  /** Sem divisores de seção; o scroller fica no RoomSidePanel. */
  flush?: boolean;
  className?: string;
  footer?: ReactNode;
};

export function roomContextPanelBemClasses(prefix: string): RoomContextPanelClassNames {
  const base = `${prefix}-room-context-panel`;
  const ui = "delpi-ui-room-context-panel";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    embedded: pair(`${base}--embedded`, `${ui}--embedded`),
    flush: pair(`${base}--flush`, `${ui}--flush`),
    section: pair(`${base}__section`, `${ui}__section`),
    heading: pair(`${base}__heading`, `${ui}__heading`),
    body: pair(`${base}__body`, `${ui}__body`),
    aboutRow: pair(`${base}__about-row`, `${ui}__about-row`),
    openLink: pair(`${base}__open`, `${ui}__open`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
    pinList: pair(`${base}__pins`, `${ui}__pins`),
    pinItem: pair(`${base}__pin`, `${ui}__pin`),
    pinIcon: pair(`${base}__pin-icon`, `${ui}__pin-icon`),
    avatars: avatarStackBemClasses(prefix),
    avatar: initialsAvatarBemClasses(prefix),
  };
}

export function RoomContextPanel({
  classNames,
  labels,
  entityTitle,
  entityKey,
  entityHref,
  onOpenEntity,
  participants = [],
  participantsAriaLabel,
  pins = [],
  onPinSelect,
  embedded = false,
  flush = false,
  className,
  footer,
}: RoomContextPanelProps) {
  const rootClass = [
    classNames.root,
    embedded ? classNames.embedded : null,
    flush ? classNames.flush : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const title = (entityTitle ?? "").trim();
  const key = (entityKey ?? "").trim();

  return (
    <aside className={rootClass}>
      <section className={classNames.section}>
        <h3 className={classNames.heading}>{labels.about}</h3>
        <div className={classNames.aboutRow}>
          <div className={classNames.body}>
            {title ? <div>{title}</div> : null}
            {key ? <div>{key}</div> : null}
          </div>
          {entityHref ? (
            <a
              className={classNames.openLink}
              href={entityHref}
              onClick={(event) => {
                if (!onOpenEntity) return;
                event.preventDefault();
                onOpenEntity();
              }}
            >
              {labels.openEntity} <ExternalLink size={14} aria-hidden />
            </a>
          ) : null}
        </div>
      </section>
      <section className={classNames.section}>
        <h3 className={classNames.heading}>{labels.participants}</h3>
        {participants.length > 0 ? (
          <AvatarStack
            classNames={classNames.avatars}
            avatarClassNames={classNames.avatar}
            items={participants}
            aria-label={participantsAriaLabel}
            max={8}
            size="md"
          />
        ) : (
          <p className={classNames.empty}>{labels.membersEmpty}</p>
        )}
      </section>
      <section className={classNames.section}>
        <h3 className={classNames.heading}>
          {labels.pins}
          {pins.length > 0 ? ` (${pins.length})` : ""}
        </h3>
        {pins.length === 0 ? (
          <p className={classNames.empty}>{labels.pinsEmpty}</p>
        ) : (
          <ul className={classNames.pinList}>
            {pins.map((pin) => (
              <li key={pin.id}>
                <button
                  type="button"
                  className={classNames.pinItem}
                  onClick={() => onPinSelect?.(pin.messageId)}
                >
                  <Pin size={14} className={classNames.pinIcon} aria-hidden />
                  <span>{pin.title}</span>
                  {pin.dateLabel ? <time>{pin.dateLabel}</time> : null}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
      {footer}
    </aside>
  );
}

export type DashboardRoomContextPanelProps = Omit<RoomContextPanelProps, "classNames">;

export function createDashboardRoomContextPanel(prefix: string) {
  const classNames = roomContextPanelBemClasses(prefix);
  return function DashboardRoomContextPanel(props: DashboardRoomContextPanelProps) {
    return <RoomContextPanel classNames={classNames} {...props} />;
  };
}
