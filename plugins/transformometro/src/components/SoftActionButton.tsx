import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

type SoftActionButtonProps = {
  children: ReactNode;
  icon?: LucideIcon;
  /** Compact density for tertiary row actions. */
  compact?: boolean;
  className?: string;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children">;

const BASE = "ds-soft-btn";

/**
 * Soft tonal action button for Process Workspace CTAs.
 * Uses DS accent tokens (light + dark) — presentation only.
 */
export function SoftActionButton({
  children,
  icon: Icon,
  compact = false,
  className,
  type = "button",
  ...rest
}: SoftActionButtonProps) {
  const classes = [BASE, compact ? `${BASE}--compact` : null, className]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} {...rest}>
      {Icon ? <Icon size={compact ? 14 : 16} strokeWidth={1.75} aria-hidden="true" /> : null}
      <span className={`${BASE}__label`}>{children}</span>
    </button>
  );
}

/** Class string for SoftActionButton (e.g. EditableSectionCard ghost override). */
export function softActionBtnClass(compact = false): string {
  return compact ? `${BASE} ${BASE}--compact` : BASE;
}
