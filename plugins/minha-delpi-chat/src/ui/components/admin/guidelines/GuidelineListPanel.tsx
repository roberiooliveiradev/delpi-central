import type { AdminGuideline } from "./guidelineTypes";

import "./GuidelineListPanel.css";

type GuidelineListPanelProps = {
  guidelines: AdminGuideline[];
  publishGuideline: (guidelineId: string) => Promise<void>;
  archiveGuideline: (guidelineId: string) => Promise<void>;
};

const STATUS_LABEL: Record<AdminGuideline["status"], string> = {
  active: "Ativo",
  draft: "Rascunho",
  archived: "Arquivada",
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
                disabled={false}
                title="Publicar diretriz"
                onClick={() => {
                  void publishGuideline(guideline.id);
                }}
              >
                Publicar
              </button>

              <button
                type="button"
                disabled={false}
                title="Arquivar diretriz"
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
    </article>
  );
}
