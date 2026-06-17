import { Plus, X } from "lucide-react";
import { useRef, useState } from "react";

import {
  AGENT_ICEBREAKER_MAX_CHARS,
  AGENT_ICEBREAKER_MAX_COUNT,
  AGENT_ICEBREAKER_PLACEHOLDER_FIELDS,
  AGENT_ICEBREAKER_TEMPLATES,
  buildIcebreakerPlaceholderToken,
  clampIcebreakerDraft,
  formatIcebreakerForDisplay,
  hasShortcutPlaceholders,
} from "../../../agentIcebreakers";

import "./AgentIcebreakersEditor.css";

type AgentIcebreakersEditorProps = {
  icebreakers: string[];
  usingDefaults?: boolean;
  onChange: (next: string[]) => void;
};

export function AgentIcebreakersEditor({
  icebreakers,
  usingDefaults = false,
  onChange,
}: AgentIcebreakersEditorProps) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const inputRefs = useRef<Array<HTMLTextAreaElement | null>>([]);

  function updateIcebreaker(index: number, value: string) {
    onChange(
      icebreakers.map((item, itemIndex) =>
        itemIndex === index ? clampIcebreakerDraft(value) : item,
      ),
    );
  }

  function removeIcebreaker(index: number) {
    const next = icebreakers.filter((_, itemIndex) => itemIndex !== index);
    onChange(next.length > 0 ? next : [""]);
  }

  function addIcebreaker() {
    if (icebreakers.length >= AGENT_ICEBREAKER_MAX_COUNT) {
      return;
    }

    onChange([...icebreakers, ""]);
    setFocusedIndex(icebreakers.length);
  }

  function insertPlaceholder(fieldId: string, index = focusedIndex) {
    const token = buildIcebreakerPlaceholderToken(fieldId);
    const targetIndex = Math.max(0, Math.min(index, icebreakers.length - 1));

    onChange(
      icebreakers.map((item, itemIndex) => {
        if (itemIndex !== targetIndex) {
          return item;
        }

        const input = inputRefs.current[targetIndex];
        const start = input?.selectionStart ?? item.length;
        const end = input?.selectionEnd ?? item.length;
        const nextValue = `${item.slice(0, start)}${token}${item.slice(end)}`;

        return clampIcebreakerDraft(nextValue);
      }),
    );

    requestAnimationFrame(() => {
      const input = inputRefs.current[targetIndex];

      if (!input) {
        return;
      }

      input.focus();
      const cursor = (input.selectionStart ?? 0) + token.length;
      input.setSelectionRange(cursor, cursor);
    });
  }

  function applyTemplate(template: string) {
    const normalizedTemplate = clampIcebreakerDraft(template.trim());

    if (!normalizedTemplate) {
      return;
    }

    if (icebreakers.some((item) => item.trim() === normalizedTemplate)) {
      return;
    }

    const emptyIndex = icebreakers.findIndex((item) => !item.trim());

    if (emptyIndex >= 0) {
      onChange(
        icebreakers.map((item, index) =>
          index === emptyIndex ? normalizedTemplate : item,
        ),
      );
      setFocusedIndex(emptyIndex);
      return;
    }

    if (icebreakers.length >= AGENT_ICEBREAKER_MAX_COUNT) {
      return;
    }

    onChange([...icebreakers, normalizedTemplate]);
    setFocusedIndex(icebreakers.length);
  }

  return (
    <div className="mdc-agent-icebreakers-editor">
      {usingDefaults ? (
        <p className="mdc-agent-icebreakers-editor__defaults-notice">
          Estes são os quebra-gelos padrão exibidos na home do agente. Edite, remova ou salve
          rascunho para torná-los permanentes.
        </p>
      ) : null}

      <p className="mdc-agent-icebreakers-editor__help">
        Use texto livre ou campos editáveis como{" "}
        <code>{buildIcebreakerPlaceholderToken("productCode")}</code> — na home, o clique envia
        a pergunta (com diálogo para placeholders). Até {AGENT_ICEBREAKER_MAX_COUNT} sugestões,{" "}
        {AGENT_ICEBREAKER_MAX_CHARS} caracteres cada.
      </p>

      <div className="mdc-agent-icebreakers-editor__templates" aria-label="Modelos de quebra-gelo">
        <span className="mdc-agent-icebreakers-editor__templates-label">Modelos:</span>
        <div className="mdc-agent-icebreakers-editor__template-list">
          {AGENT_ICEBREAKER_TEMPLATES.map((item) => (
            <button
              key={item.template}
              type="button"
              className="mdc-agent-icebreakers-editor__template-btn"
              onClick={() => applyTemplate(item.template)}
              title={item.template}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mdc-agent-icebreakers-editor__fields" aria-label="Campos editáveis">
        <span className="mdc-agent-icebreakers-editor__fields-label">Inserir campo:</span>
        <div className="mdc-agent-icebreakers-editor__field-list">
          {AGENT_ICEBREAKER_PLACEHOLDER_FIELDS.map((field) => (
            <button
              key={field.id}
              type="button"
              className="mdc-agent-icebreakers-editor__field-btn"
              onClick={() => insertPlaceholder(field.id)}
              title={buildIcebreakerPlaceholderToken(field.id)}
            >
              {field.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mdc-chat-agent-builder__icebreakers">
        {icebreakers.map((icebreaker, index) => (
          <div key={`${index}-${icebreakers.length}`} className="mdc-agent-icebreakers-editor__row">
            <div className="mdc-chat-agent-builder__icebreaker-row">
              <textarea
                ref={(element) => {
                  inputRefs.current[index] = element;
                }}
                className="mdc-chat-agent-builder__icebreaker-field"
                value={icebreaker}
                rows={1}
                maxLength={AGENT_ICEBREAKER_MAX_CHARS}
                onChange={(event) => updateIcebreaker(index, event.target.value)}
                onFocus={() => setFocusedIndex(index)}
                placeholder="Ex.: me fale do produto {{productCode}}"
                aria-label={`Quebra-gelo ${index + 1}`}
                aria-describedby={`icebreaker-count-${index} icebreaker-preview-${index}`}
              />
              <span
                id={`icebreaker-count-${index}`}
                className="mdc-chat-agent-builder__icebreaker-count"
              >
                {icebreaker.length}/{AGENT_ICEBREAKER_MAX_CHARS}
              </span>

              <button
                type="button"
                onClick={() => removeIcebreaker(index)}
                aria-label="Remover quebra-gelo"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>

            {icebreaker.trim() ? (
              <p
                id={`icebreaker-preview-${index}`}
                className="mdc-agent-icebreakers-editor__preview"
              >
                <span>Prévia no card:</span> {formatIcebreakerForDisplay(icebreaker)}
                {hasShortcutPlaceholders(icebreaker) ? (
                  <em> — na home, pede o valor e envia ao clicar.</em>
                ) : null}
              </p>
            ) : null}
          </div>
        ))}

        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          onClick={addIcebreaker}
          disabled={icebreakers.length >= AGENT_ICEBREAKER_MAX_COUNT}
        >
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar quebra-gelo</span>
        </button>
      </div>
    </div>
  );
}
