import type { AdminGuideline, GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./GuidelineListPanel.css";

type GuidelineListPanelProps = GuidelineBackendPlaceholders & {
  guidelines: AdminGuideline[];
};

const STATUS_LABEL: Record<AdminGuideline["status"], string> = {
  active: "Ativo",
  draft: "Rascunho",
  review: "Revisar",
};

export function GuidelineListPanel({
  guidelines,
  publishGuideline,
  archiveGuideline,
}: GuidelineListPanelProps) {
  return (
    <article className="mdc-guideline-list-panel">
      <div className="mdc-guideline-list-panel__header">
        <div>
          <p className="mdc-chat-eyebrow">Comportamento global</p>
          <h2>Diretrizes globais</h2>
        </div>

        <span>{guidelines.length} regra(s)</span>
      </div>

      <p className="mdc-chat-muted">
        Diretrizes que moldam o comportamento geral do chat, antes de agentes, projetos e anexos de conversa.
      </p>

      <div className="mdc-guideline-list-panel__list">
        {guidelines.map((guideline) => (
          <article key={guideline.id} className="mdc-guideline-list-panel__item">
            <div>
              <strong>{guideline.title}</strong>
              <p>{guideline.description}</p>
            </div>

            <div className="mdc-guideline-list-panel__actions">
              <span className={`is-${guideline.status}`}>
                {STATUS_LABEL[guideline.status]}
              </span>

              <button
                type="button"
                disabled={!publishGuideline}
                title={publishGuideline ? "Publicar diretriz" : "Aguardando endpoint de publicação"}
                onClick={() => {
                  void publishGuideline?.(guideline.id);
                }}
              >
                Publicar
              </button>

              <button
                type="button"
                disabled={!archiveGuideline}
                title={archiveGuideline ? "Arquivar diretriz" : "Aguardando endpoint de arquivamento"}
                onClick={() => {
                  void archiveGuideline?.(guideline.id);
                }}
              >
                Arquivar
              </button>
            </div>
          </article>
        ))}
      </div>
    </article>
  );
}
