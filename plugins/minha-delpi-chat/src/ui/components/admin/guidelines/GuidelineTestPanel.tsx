import { useState } from "react";

import type { AdminRagTestResponse } from "../../../../data/api/adminFutureTypes";
import type { GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./GuidelineTestPanel.css";

type GuidelineTestPanelProps = Pick<GuidelineBackendPlaceholders, "testGuidelines">;

export function GuidelineTestPanel({ testGuidelines }: GuidelineTestPanelProps) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AdminRagTestResponse | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleTest() {
    const normalizedQuestion = question.trim();

    if (!normalizedQuestion || !testGuidelines || isTesting) {
      return;
    }

    setIsTesting(true);
    setError(null);
    setResult(null);

    try {
      const response = await testGuidelines(normalizedQuestion);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao testar diretrizes.");
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <article className="mdc-guideline-test-panel">
      <div>
        <p className="mdc-chat-eyebrow">Validação</p>
        <h2>Teste de assertividade</h2>
      </div>

      <p className="mdc-chat-muted">
        Simule perguntas para validar se a base global e as diretrizes estão orientando a resposta.
      </p>

      <textarea
        value={question}
        rows={8}
        placeholder="Ex.: Como o chat deve responder quando não encontrar fonte suficiente?"
        onChange={(event) => setQuestion(event.target.value)}
      />

      <button
        type="button"
        disabled={!question.trim() || !testGuidelines || isTesting}
        onClick={() => {
          void handleTest();
        }}
      >
        {isTesting ? "Testando..." : "Testar diretrizes"}
      </button>

      {error ? (
        <div className="mdc-guideline-test-panel__error" role="alert">
          {error}
        </div>
      ) : null}

      {result ? (
        <section className="mdc-guideline-test-panel__result">
          <div>
            <span>Score</span>
            <strong>{Math.round(result.score * 100)}%</strong>
          </div>

          <article>
            <h3>Prévia da resposta</h3>
            <p>{result.answerPreview}</p>
          </article>

          <article>
            <h3>Diretrizes aplicadas</h3>
            {(result.appliedGuidelines ?? result.triggeredGuidelines).length === 0 ? (
              <p>Nenhuma diretriz ativa aplicada neste teste.</p>
            ) : (
              <ul>
                {(result.appliedGuidelines ?? result.triggeredGuidelines).map((guideline) => (
                  <li key={guideline.id}>
                    <strong>{guideline.title}</strong>
                    <span>{guideline.category ?? "global"}</span>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article>
            <h3>Documentos acionados</h3>
            {result.matchedDocuments.length === 0 ? (
              <p>Nenhum documento encontrado.</p>
            ) : (
              <ul>
                {result.matchedDocuments.map((document) => (
                  <li key={document.id}>
                    <strong>{document.title}</strong>
                    <span>{Math.round(document.score * 100)}%</span>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article>
            <h3>Chunks usados</h3>
            {!result.chunks || result.chunks.length === 0 ? (
              <p>Nenhum chunk retornado.</p>
            ) : (
              <div className="mdc-guideline-test-panel__chunks">
                {result.chunks.map((chunk) => (
                  <section key={chunk.id}>
                    <div>
                      <strong>{chunk.title}</strong>
                      <span>{Math.round(chunk.score * 100)}%</span>
                    </div>
                    <p>{chunk.preview}</p>
                  </section>
                ))}
              </div>
            )}
          </article>
        </section>
      ) : null}
    </article>
  );
}
