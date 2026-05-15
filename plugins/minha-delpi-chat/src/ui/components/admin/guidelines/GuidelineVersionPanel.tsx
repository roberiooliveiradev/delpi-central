import type { GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./GuidelineVersionPanel.css";

type GuidelineVersionPanelProps = Pick<
  GuidelineBackendPlaceholders,
  "loadGuidelines" | "saveGuideline"
>;

export function GuidelineVersionPanel({
  loadGuidelines,
  saveGuideline,
}: GuidelineVersionPanelProps) {
  return (
    <article className="mdc-guideline-version-panel">
      <div>
        <p className="mdc-chat-eyebrow">Versionamento</p>
        <h2>Publicação e histórico</h2>
      </div>

      <p className="mdc-chat-muted">
        Área preparada para listar versões, comparar mudanças, restaurar diretrizes e publicar rascunhos.
      </p>

      <div className="mdc-guideline-version-panel__grid">
        <div>
          <strong>Versão ativa</strong>
          <span>Aguardando endpoint</span>
        </div>

        <div>
          <strong>Rascunhos</strong>
          <span>Aguardando endpoint</span>
        </div>

        <div>
          <strong>Última publicação</strong>
          <span>Aguardando endpoint</span>
        </div>
      </div>

      <div className="mdc-guideline-version-panel__actions">
        <button
          type="button"
          disabled={!loadGuidelines}
          onClick={() => {
            void loadGuidelines?.();
          }}
        >
          Recarregar versões
        </button>

        <button
          type="button"
          disabled={!saveGuideline}
          title="Aguardando editor de diretriz"
        >
          Salvar rascunho
        </button>
      </div>
    </article>
  );
}
