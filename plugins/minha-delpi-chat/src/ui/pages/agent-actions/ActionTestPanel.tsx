import { Plus, Route, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";

import {
  createInitialBodyText,
  createInitialPathFields,
  createInitialQueryFields,
  fieldsToRecord,
  isBodyMethod,
  parseBodyJson,
  type TestField,
} from "./actionTestUtils";
import type { ActionTestPanelProps } from "./types";

import "./ActionTestPanel.css";

function updateField(
  fields: TestField[],
  index: number,
  patch: Partial<TestField>,
): TestField[] {
  return fields.map((field, fieldIndex) =>
    fieldIndex === index ? { ...field, ...patch } : field,
  );
}

function ParameterField({
  field,
  index,
  onChange,
}: {
  field: TestField;
  index: number;
  onChange: (index: number, patch: Partial<TestField>) => void;
}) {
  return (
    <label className="mdc-action-test-panel__parameter">
      <span>
        {field.key}
        {field.required ? <em>obrigatório</em> : null}
      </span>

      <input
        value={field.value}
        onChange={(event) => onChange(index, { value: event.target.value })}
        placeholder={`Valor para ${field.key}`}
      />

      {field.description ? <small>{field.description}</small> : null}
    </label>
  );
}

export function ActionTestPanel({
  action,
  isRunning,
  result,
  logs,
  onRun,
  onClose,
}: ActionTestPanelProps) {
  const [pathFields, setPathFields] = useState<TestField[]>(() =>
    createInitialPathFields(action),
  );
  const [queryFields, setQueryFields] = useState<TestField[]>(() =>
    createInitialQueryFields(action),
  );
  const [bodyText, setBodyText] = useState(() => createInitialBodyText(action));
  const [localError, setLocalError] = useState<string | null>(null);

  const hasBody = isBodyMethod(action.method);

  const routeLabel = useMemo(
    () => `${String(action.method ?? "GET").toUpperCase()} ${action.path ?? "/"}`,
    [action.method, action.path],
  );

  async function runTest() {
    setLocalError(null);

    try {
      await onRun({
        pathParams: fieldsToRecord(pathFields),
        query: fieldsToRecord(queryFields),
        body: hasBody ? parseBodyJson(bodyText) : undefined,
      });
    } catch (error) {
      setLocalError(
        error instanceof Error
          ? error.message
          : "Não foi possível preparar o teste da rota.",
      );
    }
  }

  return (
    <section className="mdc-action-test-panel" aria-label="Teste da rota">
      <header className="mdc-action-test-panel__header">
        <div>
          <strong>Testar rota</strong>
          <span>{routeLabel}</span>
        </div>

        <button
          type="button"
          className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--sm"
          onClick={onClose}
          aria-label="Fechar teste"
        >
          <X aria-hidden="true" />
        </button>
      </header>

      {pathFields.length > 0 ? (
        <div className="mdc-action-test-panel__group">
          <h3>Parâmetros da rota</h3>
          <p>Campos exigidos pelo caminho da URL.</p>

          {pathFields.map((field, index) => (
            <ParameterField
              key={field.key}
              field={field}
              index={index}
              onChange={(fieldIndex, patch) =>
                setPathFields((current) => updateField(current, fieldIndex, patch))
              }
            />
          ))}
        </div>
      ) : null}

      <div className="mdc-action-test-panel__group">
        <div className="mdc-action-test-panel__group-title">
          <div>
            <h3>Query params</h3>
            <p>Filtros e paginação descritos no OpenAPI.</p>
          </div>

          <button
            type="button"
            onClick={() =>
              setQueryFields((current) => [
                ...current,
                { key: "", value: "", location: "query" },
              ])
            }
          >
            <Plus size={15} aria-hidden="true" />
            <span>Adicionar</span>
          </button>
        </div>

        {queryFields.length === 0 ? (
          <div className="mdc-action-test-panel__empty">
            Nenhum query param exigido por esta rota.
          </div>
        ) : null}

        {queryFields.map((field, index) => (
          <div className="mdc-action-test-panel__query-row" key={`${field.key}-${index}`}>
            <input
              value={field.key}
              onChange={(event) =>
                setQueryFields((current) =>
                  updateField(current, index, { key: event.target.value }),
                )
              }
              placeholder="Nome. Ex.: page"
              readOnly={Boolean(field.required)}
            />

            <input
              value={field.value}
              onChange={(event) =>
                setQueryFields((current) =>
                  updateField(current, index, { value: event.target.value }),
                )
              }
              placeholder={field.required ? "Obrigatório" : "Valor"}
            />

            <button
              type="button"
              className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--sm"
              onClick={() =>
                setQueryFields((current) =>
                  current.filter((_, fieldIndex) => fieldIndex !== index),
                )
              }
              aria-label="Remover query param"
              disabled={Boolean(field.required)}
            >
              <Trash2 aria-hidden="true" />
            </button>

            {field.description ? (
              <small className="mdc-action-test-panel__query-description">
                {field.description}
              </small>
            ) : null}
          </div>
        ))}
      </div>

      {hasBody ? (
        <div className="mdc-action-test-panel__group">
          <h3>Body JSON</h3>
          <p>Corpo gerado a partir do schema OpenAPI da rota.</p>

          <textarea
            value={bodyText}
            onChange={(event) => setBodyText(event.target.value)}
            rows={8}
            spellCheck={false}
          />
        </div>
      ) : null}

      {localError ? (
        <div className="mdc-action-test-panel__error">{localError}</div>
      ) : null}

      <div className="mdc-action-test-panel__footer">
        <button type="button" onClick={() => void runTest()} disabled={isRunning}>
          <Route size={16} aria-hidden="true" />
          <span>{isRunning ? "Testando..." : "Executar teste"}</span>
        </button>
      </div>

      {result ? (
        <pre className="mdc-action-test-panel__result">
          {[
            result.ok ? "Teste executado com sucesso." : "Teste retornou erro.",
            `Status: ${result.statusCode ?? "-"}`,
            `Duração: ${result.durationMs}ms`,
            `URL: ${result.url}`,
            "",
            result.errorMessage ? `Erro: ${result.errorMessage}` : "",
            result.responsePreview || "",
          ]
            .filter(Boolean)
            .join("\n")}
        </pre>
      ) : null}

      {logs.length > 0 ? (
        <div className="mdc-action-test-panel__logs">
          <strong>Últimos testes</strong>

          {logs.slice(0, 5).map((log) => (
            <article key={log.id}>
              <span>{log.ok ? "OK" : "Erro"}</span>
              <small>
                {log.statusCode ?? "-"} · {log.durationMs}ms ·{" "}
                {log.createdAt ? new Date(log.createdAt).toLocaleString() : "-"}
              </small>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
