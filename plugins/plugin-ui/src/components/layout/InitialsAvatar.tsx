import type { CSSProperties, ReactNode } from "react";
import { useState } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { ImageLightboxModal } from "../preview/ImageLightboxModal";

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
  /**
   * Com `src`, clique amplia a foto em modal host-contained.
   * Default: `true` quando há `src`. Desligar em botões de upload/navegação.
   */
  previewable?: boolean;
  /** Título do modal de ampliação. Default: `name`. */
  previewTitle?: string;
  /** `aria-label` do botão de ampliação. */
  previewAriaLabel?: string;
  portalScopeClassName?: string;
  previewHeaderActions?: ReactNode;
  previewFooter?: ReactNode;
  onPreviewOpenChange?: (open: boolean) => void;
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
 * Com foto, o clique abre lightbox transversal (`ImageLightboxModal`).
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
  previewable,
  previewTitle,
  previewAriaLabel,
  portalScopeClassName,
  previewHeaderActions,
  previewFooter,
  onPreviewOpenChange,
}: InitialsAvatarProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const rootClass = [withBemModifier(classNames.root, size), className].filter(Boolean).join(" ");
  const initials = initialsFromName(name);
  const hue = hueFromKey(colorKey ?? name);
  const canPreview = Boolean(src) && previewable !== false;
  const resolvedPreviewTitle = (previewTitle ?? name).trim() || "Foto";
  const resolvedPreviewAria =
    (previewAriaLabel ?? "").trim() || `Ampliar foto de ${name.trim() || "contato"}`;

  const setOpen = (open: boolean) => {
    setPreviewOpen(open);
    onPreviewOpenChange?.(open);
  };

  if (src && canPreview) {
    return (
      <>
        <button
          type="button"
          className={`${rootClass} delpi-ui-avatar--previewable`}
          aria-label={resolvedPreviewAria}
          aria-haspopup="dialog"
          aria-expanded={previewOpen}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            setOpen(true);
          }}
        >
          <img className="delpi-ui-avatar__media" src={src} alt="" />
        </button>
        <ImageLightboxModal
          open={previewOpen}
          src={src}
          title={resolvedPreviewTitle}
          onClose={() => setOpen(false)}
          portalScopeClassName={portalScopeClassName}
          headerActions={previewHeaderActions}
          footer={previewFooter}
        />
      </>
    );
  }

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
