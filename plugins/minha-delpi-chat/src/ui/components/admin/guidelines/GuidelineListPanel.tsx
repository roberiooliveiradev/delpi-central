import type { AdminGuideline } from "./guidelineTypes";
import type { GuidelineStatusFilter } from "./guidelinesSummary";

import "./GuidelineListPanel.css";

type GuidelineListPanelProps = {
  guidelines: AdminGuideline[];
  statusFilter?: GuidelineStatusFilter;
  totalCount?: number;
  publishGuideline: (guidelineId: string) => Promise<void>;
  archiveGuideline: (guidelineId: string) => Promise<void>;
  onEditGuideline: (guideline: AdminGuideline) => void;
  canCreateGuidelines: boolean;
  canPublishGuidelines: boolean;
  canArchiveGuidelines: boolean;
};

const STATUS_LABEL: Record<AdminGuideline["status"], string> = {
  active: "Ativo",
  draft: "Rascunho",
  archived: "Arquivada",
};

const ENVIRONMENT_LABEL: Record<string, string> = {
  global: "Global",
  dev: "DEV",
  homolog: "HOMOLOG",
  prod: "PROD",
};

const STATUS_FILTER_LABEL: Record<GuidelineStatusFilter, string> = {
  all: "todas",
  active: "ativas",
  draft: "rascunho",
  archived: "arquivadas",
};

export function GuidelineListPanel({
  guidelines,
  statusFilter = "all",
  totalCount,
  publishGuideline,
  archiveGuideline,
  onEditGuideline,
  canCreateGuidelines,
  canPublishGuidelines,
  canArchiveGuidelines,
}: GuidelineListPanelProps) {
  return (
    <article className="mdc-admin-panel mdc-guideline-list-panel">
      <header className="mdc-guideline-list-panel__header">
        <div className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Comportamento global</p>
          <h2>Diretrizes globais</h2>
        </div>

        <span className="mdc-admin-badge mdc-admin-badge--muted">
          {statusFilter === "all"
            ? `${guidelines.length} regra(s)`
            : `${guidelines.length} de ${totalCount ?? guidelines.length} (${STATUS_FILTER_LABEL[statusFilter]})`}
        </span>
      </header>

      <p className="mdc-chat-muted">
        Diretrizes que moldam o comportamento geral do chat, antes de agentes, projetos e anexos de conversa.
      </p>

      {guidelines.length === 0 ? (
        <div className="mdc-guideline-list-panel__empty">
          <strong>
            {statusFilter === "all" && (totalCount ?? 0) === 0
              ? "Nenhuma diretriz cadastrada ainda."
              : "Nenhuma diretriz neste filtro."}
          </strong>
          <p>
            {statusFilter === "all" && (totalCount ?? 0) === 0
              ? "Use «Nova diretriz» acima ou o editor ao lado para criar a primeira regra."
              : "Selecione outro status nos cards de resumo ou crie uma nova diretriz."}
          </p>
        </div>
      ) : (
        <div className="mdc-admin-entity-list">
          {guidelines.map((guideline) => (
            <article key={guideline.id} className="mdc-admin-entity-row mdc-guideline-list-panel__item">
              <div className="mdc-admin-entity-row__body">
                <div className="mdc-admin-entity-row__title-line">
                  <strong>{guideline.title}</strong>
                  <span className={`mdc-admin-badge is-${guideline.status}`}>
                    {STATUS_LABEL[guideline.status]}
                  </span>
                </div>
                <p className="mdc-admin-entity-row__detail">
                  {guideline.description || guideline.content}
                </p>
                <small className="mdc-admin-entity-row__detail">
                  Ambiente: {ENVIRONMENT_LABEL[guideline.environment ?? "global"] ?? "Global"}
                </small>
              </div>

              <div className="mdc-admin-entity-row__actions mdc-guideline-list-panel__actions">
                <button
                  type="button"
                  className="mdc-admin-btn"
                  disabled={!canCreateGuidelines}
                  title={
                    canCreateGuidelines
                      ? "Editar diretriz"
                      : "Você não tem permissão para editar diretrizes."
                  }
                  onClick={() => {
                    onEditGuideline(guideline);
                  }}
                >
                  Editar
                </button>

                <button
                  type="button"
                  className="mdc-admin-btn mdc-admin-btn--primary"
                  disabled={guideline.status === "active" || !canPublishGuidelines}
                  title={
                    canPublishGuidelines
                      ? "Publicar diretriz"
                      : "Você não tem permissão para publicar diretrizes."
                  }
                  onClick={() => {
                    void publishGuideline(guideline.id);
                  }}
                >
                  Publicar
                </button>

                <button
                  type="button"
                  className="mdc-admin-btn"
                  disabled={guideline.status === "archived" || !canArchiveGuidelines}
                  title={
                    canArchiveGuidelines
                      ? "Arquivar diretriz"
                      : "Você não tem permissão para arquivar diretrizes."
                  }
                  onClick={() => {
                    void archiveGuideline(guideline.id);
                  }}
                >
                  Arquivar
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </article>
  );
}
