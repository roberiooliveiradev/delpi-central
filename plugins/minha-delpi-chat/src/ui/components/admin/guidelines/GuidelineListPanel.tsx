import type { AdminGuideline } from "./guidelineTypes";

import "./GuidelineListPanel.css";

type GuidelineListPanelProps = {
  guidelines: AdminGuideline[];
  publishGuideline: (guidelineId: string) => Promise<void>;
  archiveGuideline: (guidelineId: string) => Promise<void>;
  onEditGuideline: (guideline: AdminGuideline) => void;
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
  onEditGuideline,
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

      {guidelines.length === 0 ? (
        <div className="mdc-guideline-list-panel__empty">
          <strong>Nenhuma diretriz cadastrada ainda.</strong>
          <p>
            Crie a primeira diretriz no painel ao lado para orientar o comportamento global do chat.
          </p>
        </div>
      ) : (
        <div className="mdc-guideline-list-panel__list">
          {guidelines.map((guideline) => (
            <article key={guideline.id} className="mdc-guideline-list-panel__item">
              <div>
                <strong>{guideline.title}</strong>
                <p>{guideline.description || guideline.content}</p>
              </div>

              <div className="mdc-guideline-list-panel__actions">
                <span className={`is-${guideline.status}`}>
                  {STATUS_LABEL[guideline.status]}
                </span>

                <button
                  type="button"
                  title="Editar diretriz"
                  onClick={() => {
                    onEditGuideline(guideline);
                  }}
                >
                  Editar
                </button>

                <button
                  type="button"
                  disabled={guideline.status === "active"}
                  title="Publicar diretriz"
                  onClick={() => {
                    void publishGuideline(guideline.id);
                  }}
                >
                  Publicar
                </button>

                <button
                  type="button"
                  disabled={guideline.status === "archived"}
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
      )}
    </article>
  );
}
