import "./AdminGuidelinesTab.css";
export function AdminGuidelinesTab() {
  return (
    <section className="mdc-admin-grid">
      <article className="mdc-admin-card">
        <h2>Diretrizes globais</h2>
        <p className="mdc-chat-muted">
          Próxima etapa: transformar diretrizes em documentos versionados e testáveis.
        </p>

        <div className="mdc-admin-guideline-list">
          <div>
            <strong>Não inventar respostas</strong>
            <span>Ativo</span>
          </div>
          <div>
            <strong>Priorizar fontes globais antes de conhecimento geral</strong>
            <span>Ativo</span>
          </div>
          <div>
            <strong>Executar ferramentas autorizadas quando necessário</strong>
            <span>Ativo</span>
          </div>
        </div>
      </article>

      <article className="mdc-admin-card">
        <h2>Teste de assertividade</h2>
        <p className="mdc-chat-muted">
          Próxima etapa: campo para simular perguntas e verificar quais documentos o RAG usaria.
        </p>

        <textarea
          rows={8}
          disabled
          placeholder="Em breve: escreva uma pergunta de teste para validar a base global."
        />
      </article>
    </section>
  );
}
