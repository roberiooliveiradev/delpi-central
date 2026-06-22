import type { ReactNode } from "react";

type WorkspaceFileSourceListProps = {
  children: ReactNode;
  ariaLabel?: string;
  className?: string;
};

/** Lista responsiva de arquivos/fontes — grid 1/2/auto-fill conforme largura. */
export function WorkspaceFileSourceList({
  children,
  ariaLabel,
  className,
}: WorkspaceFileSourceListProps) {
  return (
    <div
      className={["mdc-workspace-file-source-list", className].filter(Boolean).join(" ")}
      aria-label={ariaLabel}
      role="list"
    >
      {children}
    </div>
  );
}

/** Envolve cada card na lista responsiva. */
export function WorkspaceFileSourceListItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={["mdc-workspace-file-source-list__item", className].filter(Boolean).join(" ")}
      role="listitem"
    >
      {children}
    </div>
  );
}
