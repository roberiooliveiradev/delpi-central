import type { ReactNode } from "react";

type WorkspaceSourcesPanelProps = {
  children: ReactNode;
  className?: string;
  role?: string;
  headerSlot?: ReactNode;
};

/** Painel canônico de upload + listagem de fontes (projeto, agente, admin). */
export function WorkspaceSourcesPanel({
  children,
  className,
  role,
  headerSlot,
}: WorkspaceSourcesPanelProps) {
  return (
    <div
      className={["mdc-workspace-sources-panel", className].filter(Boolean).join(" ")}
      role={role}
    >
      {headerSlot ? (
        <div className="mdc-workspace-sources-panel__header">{headerSlot}</div>
      ) : null}
      {children}
    </div>
  );
}
