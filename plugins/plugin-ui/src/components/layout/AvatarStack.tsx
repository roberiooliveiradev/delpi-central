import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
  type InitialsAvatarSize,
} from "./InitialsAvatar";

export type AvatarStackItem = {
  id: string;
  name: string;
  src?: string | null;
};

export type AvatarStackClassNames = {
  root: string;
  item: string;
  more: string;
};

export type AvatarStackProps = {
  items: AvatarStackItem[];
  /** Quantos avatares mostrar antes do +N. Default 5. */
  max?: number;
  size?: InitialsAvatarSize;
  classNames: AvatarStackClassNames;
  /** Classes do InitialsAvatar interno (dual-class do prefixo do plugin). */
  avatarClassNames?: InitialsAvatarClassNames;
  className?: string;
  /** aria-label do grupo. */
  "aria-label"?: string;
};

export function avatarStackBemClasses(prefix: string): AvatarStackClassNames {
  return {
    root: delpiUiClass(`${prefix}-avatar-stack`, "delpi-ui-avatar-stack"),
    item: delpiUiClass(`${prefix}-avatar-stack__item`, "delpi-ui-avatar-stack__item"),
    more: delpiUiClass(`${prefix}-avatar-stack__more`, "delpi-ui-avatar-stack__more"),
  };
}

/**
 * Facepile de avatares (iniciais/foto) com overflow +N.
 * Usa InitialsAvatar sem preview no clique (evita lightbox em stacks densos).
 */
export function AvatarStack({
  items,
  max = 5,
  size = "sm",
  classNames,
  avatarClassNames,
  className,
  "aria-label": ariaLabel,
}: AvatarStackProps) {
  const safeMax = Number.isFinite(max) && max > 0 ? Math.floor(max) : 5;
  const visible = items.slice(0, safeMax);
  const overflow = Math.max(0, items.length - visible.length);
  const resolvedAvatarClasses = avatarClassNames ?? initialsAvatarBemClasses("delpi-ui");
  const rootClass = [withBemModifier(classNames.root, size), className].filter(Boolean).join(" ");

  return (
    <ul className={rootClass} aria-label={ariaLabel || "Membros"}>
      {visible.map((item) => (
        <li key={item.id} className={classNames.item} title={item.name}>
          <InitialsAvatar
            name={item.name}
            src={item.src}
            size={size}
            classNames={resolvedAvatarClasses}
            previewable={false}
            alt={item.name}
          />
        </li>
      ))}
      {overflow > 0 ? (
        <li className={classNames.more} aria-label={`Mais ${overflow}`}>
          +{overflow}
        </li>
      ) : null}
    </ul>
  );
}

export type DashboardAvatarStackProps = Omit<AvatarStackProps, "classNames">;

export function createDashboardAvatarStack(prefix: string) {
  const classNames = avatarStackBemClasses(prefix);
  const avatarClasses = initialsAvatarBemClasses(prefix);

  return function DashboardAvatarStack(props: DashboardAvatarStackProps): ReactNode {
    return <AvatarStack classNames={classNames} avatarClassNames={avatarClasses} {...props} />;
  };
}
