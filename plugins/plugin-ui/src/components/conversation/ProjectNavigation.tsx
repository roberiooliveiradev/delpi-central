import { FolderKanban } from "lucide-react";

/** Authorized project projection from its rightful owner, not DÉLIA state. */
export type ProjectNavigationItem = {
  id: string;
  title: string;
  selected?: boolean;
};

export type ProjectNavigationProps = {
  /** Never infer "empty" from missing data or a local array. */
  status?: "contract_unavailable" | "ready" | "loading" | "authorized_empty" | "error";
  /** Host-authorized items only. Shared and personal groups require distinct owner projections. */
  projects?: readonly ProjectNavigationItem[];
  /** Selection intent; the owning API still validates current authorization. */
  onSelectProject?: (id: string) => void;
  /** Only show on real authorized error, never for a missing contract. */
  onRetry?: () => void;
  className?: string;
};

/**
 * Presentation only. No project API, creation, search, membership or local
 * persistence. Not a second app catalog or a substitute for Portal/Core.
 */
export function ProjectNavigation({
  status = "contract_unavailable",
  projects = [],
  onSelectProject,
  onRetry,
  className,
}: ProjectNavigationProps) {
  return (
    <div className={["delpi-ui-project-navigation", className].filter(Boolean).join(" ")} data-state={status}>
      {status === "contract_unavailable" ? (
        <p className="delpi-ui-project-navigation__message">Projetos estarão disponíveis após a integração autorizada.</p>
      ) : status === "loading" ? (
        <p className="delpi-ui-project-navigation__message" role="status">Carregando projetos…</p>
      ) : status === "authorized_empty" ? (
        <p className="delpi-ui-project-navigation__message">Nenhum projeto disponível.</p>
      ) : status === "error" ? (
        <div className="delpi-ui-project-navigation__feedback">
          <p className="delpi-ui-project-navigation__message" role="alert">Não foi possível carregar projetos.</p>
          {onRetry ? <button type="button" className="delpi-ui-project-navigation__retry" onClick={onRetry}>Tentar novamente</button> : null}
        </div>
      ) : onSelectProject && projects.length > 0 ? (
        <section aria-label="Meus projetos">
          <h2 className="delpi-ui-conversation-sidebar__section-heading">Meus projetos</h2>
          <ul className="delpi-ui-project-navigation__list">
            {projects.map(item => (
              <li key={item.id}>
                <button type="button" className="delpi-ui-project-navigation__item"
                  aria-label={item.title} aria-current={item.selected ? "page" : undefined}
                  title={item.title} onClick={() => onSelectProject(item.id)}>
                  <FolderKanban size={18} strokeWidth={1.8} aria-hidden="true" />
                  <span className="delpi-ui-project-navigation__title">{item.title}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
