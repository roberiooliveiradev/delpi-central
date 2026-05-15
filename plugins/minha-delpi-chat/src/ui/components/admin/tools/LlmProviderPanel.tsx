import type { AdminLlmStatus } from "../../../../data/api/adminTypes";

import "./LlmProviderPanel.css";

type LlmProviderPanelProps = {
  llmStatus: AdminLlmStatus | null;
};

export function LlmProviderPanel({ llmStatus }: LlmProviderPanelProps) {
  return (
    <article className="mdc-llm-provider-panel">
      <div>
        <p className="mdc-chat-eyebrow">LLM</p>
        <h2>Provider LLM</h2>
      </div>

      {llmStatus ? (
        <dl className="mdc-llm-provider-panel__kv">
          <div>
            <dt>Provider</dt>
            <dd>{llmStatus.provider}</dd>
          </div>
          <div>
            <dt>Modelo</dt>
            <dd>{llmStatus.model}</dd>
          </div>
          <div>
            <dt>Temperatura</dt>
            <dd>{llmStatus.temperature}</dd>
          </div>
          <div>
            <dt>Máx. tokens</dt>
            <dd>{llmStatus.maxTokens}</dd>
          </div>
        </dl>
      ) : (
        <p className="mdc-chat-muted">Carregando provider...</p>
      )}

      <div className="mdc-llm-provider-panel__future">
        <strong>Pronto para configuração futura</strong>
        <small>
          Quando o backend expuser configuração dinâmica, este painel pode editar modelo,
          temperatura, limite de tokens e fallback sem alterar a estrutura da aba.
        </small>
      </div>
    </article>
  );
}
