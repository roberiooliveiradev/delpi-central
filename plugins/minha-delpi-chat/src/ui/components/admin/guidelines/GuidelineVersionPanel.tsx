import "./GuidelineVersionPanel.css";

export function GuidelineVersionPanel() {
  return (
    <article className="mdc-guideline-version-panel">
      <div>
        <p className="mdc-chat-eyebrow">Versionamento</p>
        <h2>Publicação e histórico</h2>
      </div>

      <p className="mdc-chat-muted">
        O versionamento das diretrizes será ativado quando criarmos o modelo persistente
        no backend. Por enquanto, as diretrizes visíveis nesta tela são regras-base do front
        e o teste de assertividade já usa o RAG real.
      </p>

      <div className="mdc-guideline-version-panel__grid">
        <div>
          <strong>Teste RAG</strong>
          <span>Ativo</span>
        </div>

        <div>
          <strong>Diretrizes persistentes</strong>
          <span>Próxima etapa</span>
        </div>

        <div>
          <strong>Histórico de versões</strong>
          <span>Próxima etapa</span>
        </div>
      </div>
    </article>
  );
}
