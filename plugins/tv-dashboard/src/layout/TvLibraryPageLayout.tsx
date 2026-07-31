import type { ReactNode } from "react";

type Props = {
  header: ReactNode;
  actions?: ReactNode;
  toolbar?: ReactNode;
  children: ReactNode;
  /** Classe extra no stack (ex.: `td-page-stack--share` para coluna centralizada). */
  className?: string;
};

/** Stack de página de biblioteca (home / templates / share). */
export function TvLibraryPageLayout({ header, actions, toolbar, children, className }: Props) {
  const rootClass = ["td-page-stack", className].filter(Boolean).join(" ");
  return (
    <div className={rootClass}>
      {header}
      {actions ? <div className="td-action-grid">{actions}</div> : null}
      {toolbar ? <div className="td-library-toolbar">{toolbar}</div> : null}
      <div className="td-page-stack__body">{children}</div>
    </div>
  );
}
