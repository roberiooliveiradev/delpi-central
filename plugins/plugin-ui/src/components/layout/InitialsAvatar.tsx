import type { CSSProperties } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type InitialsAvatarSize = "sm" | "md" | "lg";

export type InitialsAvatarClassNames = {
  root: string;
};

export type InitialsAvatarProps = {
  /** Nome usado para iniciais (e hue se `colorKey` omitido). */
  name: string;
  /** Chave estável para cor de fundo (ex.: código|loja). Default: `name`. */
  colorKey?: string;
  /** URL da imagem; sem src, mostra iniciais. */
  src?: string | null;
  alt?: string;
  size?: InitialsAvatarSize;
  classNames: InitialsAvatarClassNames;
  className?: string;
  /** Sobrescreve o estilo de fundo (só no modo iniciais). */
  style?: CSSProperties;
};

export function initialsFromName(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}

export function hueFromKey(key: string): number {
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) {
    hash = (hash * 31 + key.charCodeAt(i)) % 360;
  }
  return hash;
}

export function initialsAvatarBemClasses(prefix: string): InitialsAvatarClassNames {
  return {
    root: delpiUiClass(`${prefix}-avatar`, "delpi-ui-avatar"),
  };
}

/**
 * Avatar chrome: foto ou iniciais com cor determinística.
 * Sem HTTP — o consumidor resolve `src` (blob URL, CDN, etc.).
 */
export function InitialsAvatar({
  name,
  colorKey,
  src,
  alt = "",
  size = "md",
  classNames,
  className,
  style,
}: InitialsAvatarProps) {
  const rootClass = [withBemModifier(classNames.root, size), className].filter(Boolean).join(" ");
  const initials = initialsFromName(name);
  const hue = hueFromKey(colorKey ?? name);

  if (src) {
    return <img className={rootClass} src={src} alt={alt} />;
  }

  return (
    <span
      className={rootClass}
      style={{ background: `hsl(${hue} 48% 42%)`, ...style }}
      aria-hidden={alt ? undefined : true}
      role={alt ? "img" : undefined}
      aria-label={alt || undefined}
    >
      {initials}
    </span>
  );
}

export type DashboardInitialsAvatarProps = Omit<InitialsAvatarProps, "classNames">;

export function createInitialsAvatar(prefix: string) {
  const classNames = initialsAvatarBemClasses(prefix);

  return function DashboardInitialsAvatar(props: DashboardInitialsAvatarProps) {
    return <InitialsAvatar classNames={classNames} {...props} />;
  };
}
