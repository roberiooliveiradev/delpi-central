import type { ReactNode } from "react";

type Props = {
  header: ReactNode;
  actions?: ReactNode;
  toolbar?: ReactNode;
  children: ReactNode;
};

/** Stack de página de biblioteca (home / templates / share). */
export function TvLibraryPageLayout({ header, actions, toolbar, children }: Props) {
  return (
    <div className="td-page-stack">
      {header}
      {actions ? <div className="td-action-grid">{actions}</div> : null}
      {toolbar ? <div className="td-library-toolbar">{toolbar}</div> : null}
      <div className="td-page-stack__body">{children}</div>
    </div>
  );
}
