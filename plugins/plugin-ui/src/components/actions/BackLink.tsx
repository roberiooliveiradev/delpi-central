import type { MouseEventHandler, ReactNode } from "react";

type BackLinkBaseProps = {
  children: ReactNode;
  className?: string;
  variant?: "default" | "prominent";
};

export type BackLinkProps = BackLinkBaseProps &
  (
    | {
        href: string;
        onClick?: MouseEventHandler<HTMLAnchorElement>;
      }
    | {
        href?: undefined;
        onClick: () => void;
      }
  );

/**
 * Link de navegação «voltar» com seta, usado no topo das páginas.
 *
 * CSS: `styles/action-controls.css` (`.delpi-ui-back-link`).
 */
export function BackLink(props: BackLinkProps) {
  const { children, className, variant = "default" } = props;
  const rootClass = [
    "delpi-ui-back-link",
    variant === "prominent" ? "delpi-ui-back-link--prominent" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const content = (
    <>
      <span className="delpi-ui-back-link__arrow" aria-hidden={true}>
        ←
      </span>
      {children}
    </>
  );

  if ("href" in props) {
    return (
      <a className={rootClass} href={props.href ?? ""} onClick={props.onClick}>
        {content}
      </a>
    );
  }

  return (
    <button type="button" className={rootClass} onClick={props.onClick}>
      {content}
    </button>
  );
}
