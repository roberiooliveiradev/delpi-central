// portal/src/ui-kit/button/Button.tsx

import {
  forwardRef,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react";
import { Loader2 } from "lucide-react";
import "./Button.css";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "danger"
  | "danger-soft"
  | "ghost"
  | "link";

export type ButtonSize = "sm" | "md" | "lg";

export type ButtonProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "children"
> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  /** Botão de alternância (filtro, ordenação): marca `aria-pressed`. */
  pressed?: boolean;
  children?: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = "secondary",
      size = "md",
      loading = false,
      icon,
      pressed,
      disabled,
      className,
      type = "button",
      children,
      ...rest
    },
    ref,
  ) {
    const hasLabel = children != null && children !== false;

    const classes = [
      "portal-ui-btn",
      `portal-ui-btn--${variant}`,
      `portal-ui-btn--${size}`,
      loading ? "portal-ui-btn--loading" : "",
      !hasLabel ? "portal-ui-btn--icon-only" : "",
      pressed ? "portal-ui-btn--pressed" : "",
      className ?? "",
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        aria-pressed={pressed}
        {...rest}
      >
        {loading ? (
          <span className="portal-ui-btn__spinner" aria-hidden="true">
            <Loader2 size={size === "sm" ? 14 : 16} />
          </span>
        ) : icon ? (
          <span className="portal-ui-btn__icon" aria-hidden="true">
            {icon}
          </span>
        ) : null}
        {hasLabel ? (
          <span className="portal-ui-btn__label">{children}</span>
        ) : null}
      </button>
    );
  },
);
