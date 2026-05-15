import { useState } from "react";

import type { GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./GuidelineTestPanel.css";

type GuidelineTestPanelProps = Pick<GuidelineBackendPlaceholders, "testGuidelines">;

export function GuidelineTestPanel({ testGuidelines }: GuidelineTestPanelProps) {
  const [question, setQuestion] = useState("");

  return (
    <article className="mdc-guideline-test-panel">
      <div>
        <p className="mdc-chat-eyebrow">Validação</p>
        <h2>Teste de assertividade</h2>
      </div>

      <p className="mdc-chat-muted">
        Simule perguntas para validar se as diretrizes globais estão orientando a resposta do chat.
      </p>

      <textarea
        value={question}
        rows={8}
        placeholder="Ex.: Quando eu perguntar sobre um produto, como o chat deve priorizar a fonte correta?"
        onChange={(event) => setQuestion(event.target.value)}
      />

      <button
        type="button"
        disabled={!question.trim() || !testGuidelines}
        title={testGuidelines ? "Testar diretrizes" : "Aguardando endpoint de teste"}
        onClick={() => {
          void testGuidelines?.(question.trim());
        }}
      >
        Testar diretrizes
      </button>

      <div className="mdc-guideline-test-panel__placeholder">
        <strong>Pronto para backend</strong>
        <small>
          Resultado esperado: fontes usadas, diretrizes acionadas, score de assertividade e pontos de melhoria.
        </small>
      </div>
    </article>
  );
}
