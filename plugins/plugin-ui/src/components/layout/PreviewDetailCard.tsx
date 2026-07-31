import type { ButtonHTMLAttributes, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type PreviewDetailCardClassNames = {
  root: string;
  media: string;
  detail: string;
  title: string;
  meta: string;
};

export type PreviewDetailCardProps = {
  /** Prévia / capa (thumb, imagem, ícone). */
  media: ReactNode;
  title: ReactNode;
  /** Badges, contadores, datas — área que cresce para preencher a altura do card. */
  meta?: ReactNode;
  className?: string;
  classNames: PreviewDetailCardClassNames;
  "aria-label"?: string;
} & Pick<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "onClick" | "onContextMenu" | "disabled" | "type"
>;

/** Dual `{prefix}-preview-detail-card*` + `.delpi-ui-preview-detail-card*`. */
export function previewDetailCardBemClasses(prefix: string): PreviewDetailCardClassNames {
  const base = `${prefix}-preview-detail-card`;
  const ui = "delpi-ui-preview-detail-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    media: pair(`${base}__media`, `${ui}__media`),
    detail: pair(`${base}__detail`, `${ui}__detail`),
    title: pair(`${base}__title`, `${ui}__title`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
  };
}

/**
 * Card de biblioteca com capa + detalhe.
 * Em grade com altura uniforme, `__detail` cresce (`flex: 1`) para não deixar
 * espaço vazio na base quando o meta é curto.
 *
 * CSS: `styles/preview-detail-card.css`.
 */
export function PreviewDetailCard({
  media,
  title,
  meta,
  className,
  classNames,
  onClick,
  onContextMenu,
  disabled = false,
  type = "button",
  "aria-label": ariaLabel,
}: PreviewDetailCardProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <button
      type={type}
      className={rootClass}
      disabled={disabled}
      onClick={onClick}
      onContextMenu={onContextMenu}
      aria-label={ariaLabel}
    >
      <span className={classNames.media} aria-hidden="true">
        {media}
      </span>
      <span className={classNames.detail}>
        <span className={classNames.title}>{title}</span>
        {meta != null ? <span className={classNames.meta}>{meta}</span> : null}
      </span>
    </button>
  );
}

export type DashboardPreviewDetailCardProps = Omit<PreviewDetailCardProps, "classNames">;

export function createDashboardPreviewDetailCard(config: {
  classNames: PreviewDetailCardClassNames;
}) {
  return function DashboardPreviewDetailCard(props: DashboardPreviewDetailCardProps) {
    return <PreviewDetailCard classNames={config.classNames} {...props} />;
  };
}
