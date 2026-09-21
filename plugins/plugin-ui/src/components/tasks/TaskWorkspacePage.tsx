import type { ReactNode } from "react";

import type { SectionCardClassNames, SectionCardLabels } from "../layout/SectionCard";
import { TaskWorklistSection } from "./TaskWorklistSection";

export type TaskWorkspaceWorklistProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  actions?: ReactNode;
  search?: ReactNode;
  /** Filtros secundários (tipo, etc.) — entre busca e conteúdo. */
  filters?: ReactNode;
  classNames?: SectionCardClassNames;
  labels?: SectionCardLabels;
};

export type TaskWorkspacePageProps = {
  className?: string;
  /**
   * Hero completo do portal (PageHero / factory / header com TopBar).
   * O kit não monta eyebrow/title — só hospeda o nó.
   */
  hero: ReactNode;
  worklist: TaskWorkspaceWorklistProps;
  /**
   * Loading inicial: substitui o corpo da fila e o editor.
   * Refresh com conteúdo já montado usa `refreshing` + children.
   */
  initialLoading?: ReactNode;
  refreshing?: boolean;
  refreshingLabel?: string;
  /** Warning parcial (ex.: uma fonte da worklist falhou). */
  partialError?: ReactNode;
  /** Erro fatal da fila. */
  error?: ReactNode;
  /** Itens, empty ou loading parcial — domínio no portal. */
  children?: ReactNode;
  /** Slot do editor (TaskEditorFrame + fields do portal). */
  editor?: ReactNode;
};

/**
 * Composição canônica de Minhas tarefas.
 * OWNS: hierarquia visual (hero → status → worklist → editor).
 * DOES NOT OWN: fetch, AuthZ, lifecycle, domínio Task, rotas.
 */
export function TaskWorkspacePage({
  className,
  hero,
  worklist,
  initialLoading,
  refreshing = false,
  refreshingLabel = "Atualizando…",
  partialError,
  error,
  children,
  editor,
}: TaskWorkspacePageProps) {
  const rootClass = ["delpi-ui-task-workspace", className].filter(Boolean).join(" ");
  const showInitial = Boolean(initialLoading);

  return (
    <div className={rootClass} data-refreshing={refreshing || undefined}>
      {hero}
      {partialError ? (
        <div className="delpi-ui-task-workspace__partial" role="status">
          {partialError}
        </div>
      ) : null}
      {error ? (
        <div className="delpi-ui-task-workspace__error" role="alert">
          {error}
        </div>
      ) : null}
      {showInitial ? (
        <div className="delpi-ui-task-workspace__initial" aria-busy="true">
          {initialLoading}
        </div>
      ) : (
        <>
          <TaskWorklistSection
            title={worklist.title}
            subtitle={worklist.subtitle}
            hint={worklist.hint}
            actions={worklist.actions}
            search={worklist.search}
            filters={worklist.filters}
            classNames={worklist.classNames}
            labels={worklist.labels}
          >
            {refreshing ? (
              <p className="delpi-ui-task-workspace__refreshing" role="status" aria-live="polite">
                {refreshingLabel}
              </p>
            ) : null}
            <div
              className="delpi-ui-task-workspace__items"
              aria-busy={refreshing || undefined}
            >
              {children}
            </div>
          </TaskWorklistSection>
          {editor ? <div className="delpi-ui-task-workspace__editor">{editor}</div> : null}
        </>
      )}
    </div>
  );
}
