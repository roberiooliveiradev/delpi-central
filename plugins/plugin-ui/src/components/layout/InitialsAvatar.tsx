import type { CSSProperties, MouseEventHandler, ReactNode } from "react";
import { useState } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { shouldHandleInlineNavClick } from "../navigation/InlineNavLink";
import { isSafeNavigationHref } from "./PagePath";
import { ImageLightboxModal } from "../preview/ImageLightboxModal";

export type InitialsAvatarSize = "sm" | "md" | "lg";

export type InitialsAvatarClassNames = {
  root: string;
};

type InitialsAvatarChromeProps = {
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
   * Ignorado quando `href` está definido.
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

export type InitialsAvatarProps = InitialsAvatarChromeProps &
  (
    | {
        href: string;
        /** Indicação do destino (tooltip nativo). Obrigatório com `href`. */
        title: string;
        onNavigate?: MouseEventHandler<HTMLAnchorElement>;
        linkAriaLabel?: string;
      }
    | {
        href?: undefined;
        title?: undefined;
        onNavigate?: undefined;
        linkAriaLabel?: undefined;
      }
  );

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

function requireSafeHref(href: string): string {
  if (!isSafeNavigationHref(href)) {
    throw new Error("InitialsAvatar recebeu um href que não é interno ao host.");
  }
  return href.trim();
}

/**
 * Avatar chrome: foto ou iniciais com cor determinística.
 * Sem HTTP — o consumidor resolve `src` (blob URL, CDN, etc.).
 * Com `href`, vira `<a>` (sem lightbox). Com foto e sem href, clique abre lightbox.
 */
export function InitialsAvatar(props: InitialsAvatarProps) {
  const {
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
  } = props;
  const [previewOpen, setPreviewOpen] = useState(false);
  const rootClass = [withBemModifier(classNames.root, size), className].filter(Boolean).join(" ");
  const initials = initialsFromName(name);
  const hue = hueFromKey(colorKey ?? name);
  /** Iniciais sempre claras — fundo HSL escuro; evita herdar texto do tema claro. */
  const initialStyle = {
    background: `hsl(${hue} 48% 42%)`,
    color: "#fff",
    ...style,
  };

  if (props.href) {
    const safeHref = requireSafeHref(props.href);
    const linkTitle = props.title.trim();
    if (!linkTitle) {
      throw new Error("InitialsAvatar com href exige title não vazio.");
    }
    const aria = (props.linkAriaLabel ?? linkTitle).trim();
    const linkClass = `${rootClass} delpi-ui-avatar--link`;
    return (
      <a
        className={linkClass}
        href={safeHref}
        title={linkTitle}
        aria-label={aria || undefined}
        style={src ? undefined : initialStyle}
        onClick={(event) => {
          event.stopPropagation();
          if (!shouldHandleInlineNavClick(event)) {
            return;
          }
          if (!props.onNavigate) {
            return;
          }
          event.preventDefault();
          props.onNavigate(event);
        }}
      >
        {src ? (
          <img className="delpi-ui-avatar__media" src={src} alt="" />
        ) : (
          initials
        )}
      </a>
    );
  }

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
      style={initialStyle}
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
    return <InitialsAvatar {...(props as InitialsAvatarProps)} classNames={classNames} />;
  };
}
