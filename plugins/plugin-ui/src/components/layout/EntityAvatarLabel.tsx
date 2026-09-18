import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
  type InitialsAvatarSize,
} from "./InitialsAvatar";

export type EntityAvatarLabelClassNames = {
  root: string;
  text: string;
  name: string;
  secondary: string;
};

export type EntityAvatarLabelProps = {
  name: string;
  colorKey?: string;
  secondary?: string | null;
  src?: string | null;
  size?: InitialsAvatarSize;
  emptyLabel?: string;
  classNames: EntityAvatarLabelClassNames;
  avatarClassNames?: InitialsAvatarClassNames;
  className?: string;
};

export function entityAvatarLabelBemClasses(prefix: string): EntityAvatarLabelClassNames {
  return {
    root: delpiUiClass(`${prefix}-entity-avatar-label`, "delpi-ui-entity-avatar-label"),
    text: delpiUiClass(
      `${prefix}-entity-avatar-label__text`,
      "delpi-ui-entity-avatar-label__text",
    ),
    name: delpiUiClass(
      `${prefix}-entity-avatar-label__name`,
      "delpi-ui-entity-avatar-label__name",
    ),
    secondary: delpiUiClass(
      `${prefix}-entity-avatar-label__secondary`,
      "delpi-ui-entity-avatar-label__secondary",
    ),
  };
}

/**
 * Avatar + nome (kit). Foto/href ficam no consumidor; sem src mostra iniciais.
 * Páginas de objeto (fornecedor, pessoa) entram depois — não inventar destino aqui.
 */
export function EntityAvatarLabel({
  name,
  colorKey,
  secondary,
  src,
  size = "sm",
  emptyLabel = "—",
  classNames,
  avatarClassNames,
  className,
}: EntityAvatarLabelProps) {
  const label = name.trim();
  const code = (secondary || "").trim();
  if (!label && !code) {
    return <>{emptyLabel}</>;
  }
  const shown = label || code;
  const resolvedAvatarClasses = avatarClassNames ?? initialsAvatarBemClasses("delpi-ui");
  const rootClass = className ? `${classNames.root} ${className}` : classNames.root;
  return (
    <span className={rootClass}>
      <InitialsAvatar
        name={shown}
        colorKey={colorKey || shown}
        src={src}
        size={size}
        classNames={resolvedAvatarClasses}
        previewable={false}
      />
      <span className={classNames.text}>
        <strong className={classNames.name}>{shown}</strong>
        {code && code !== shown ? <span className={classNames.secondary}>{code}</span> : null}
      </span>
    </span>
  );
}

export type DashboardEntityAvatarLabelProps = Omit<
  EntityAvatarLabelProps,
  "classNames" | "avatarClassNames"
>;

export function createDashboardEntityAvatarLabel(prefix: string) {
  const classNames = entityAvatarLabelBemClasses(prefix);
  const avatarClasses = initialsAvatarBemClasses(prefix);

  return function DashboardEntityAvatarLabel(
    props: DashboardEntityAvatarLabelProps,
  ): ReactNode {
    return (
      <EntityAvatarLabel
        classNames={classNames}
        avatarClassNames={avatarClasses}
        {...props}
      />
    );
  };
}
