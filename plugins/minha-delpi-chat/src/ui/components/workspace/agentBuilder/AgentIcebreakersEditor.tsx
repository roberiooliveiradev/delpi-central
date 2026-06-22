import { ChevronDown, ChevronUp, GripVertical, Plus, X } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import {
  AGENT_ICEBREAKER_MAX_CHARS,
  AGENT_ICEBREAKER_PLACEHOLDER_FIELDS,
  AGENT_ICEBREAKER_TEMPLATES,
  buildIcebreakerPlaceholderToken,
  clampIcebreakerDraft,
  formatIcebreakerForDisplay,
  hasShortcutPlaceholders,
  reorderIcebreakers,
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
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const inputRefs = useRef<Array<HTMLTextAreaElement | null>>([]);

  const canReorder = icebreakers.length > 1;

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
    onChange([...icebreakers, ""]);
    setFocusedIndex(icebreakers.length);
  }

  function moveIcebreaker(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex) {
      return;
    }

    onChange(reorderIcebreakers(icebreakers, fromIndex, toIndex));
    setFocusedIndex(toIndex);
  }

  function moveIcebreakerByStep(index: number, direction: -1 | 1) {
    moveIcebreaker(index, index + direction);
  }

  function handleDragStart(index: number, event: DragEvent) {
    setDragIndex(index);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(index));
  }

  function handleDragOver(index: number, event: DragEvent) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";

    if (dropIndex !== index) {
      setDropIndex(index);
    }
  }

  function handleDrop(index: number, event: DragEvent) {
    event.preventDefault();

    const rawFrom = dragIndex ?? Number(event.dataTransfer.getData("text/plain"));
    const fromIndex = Number.isFinite(rawFrom) ? rawFrom : -1;

    if (fromIndex >= 0 && fromIndex !== index) {
      moveIcebreaker(fromIndex, index);
    }

    setDragIndex(null);
    setDropIndex(null);
  }

  function handleDragEnd() {
    setDragIndex(null);
    setDropIndex(null);
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
        a pergunta (com diálogo para placeholders). {AGENT_ICEBREAKER_MAX_CHARS} caracteres por
        sugestão; a home exibe todas com rolagem quando necessário.
        {canReorder ? (
          <> Arraste pela alça à esquerda ou use as setas para definir a ordem na home.</>
        ) : null}
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

      <div
        className="mdc-chat-agent-builder__icebreakers"
        aria-label="Lista de quebra-gelos"
      >
        {icebreakers.map((icebreaker, index) => (
          <div
            key={`icebreaker-${index}`}
            className={[
              "mdc-agent-icebreakers-editor__row",
              dragIndex === index ? "mdc-agent-icebreakers-editor__row--dragging" : "",
              dropIndex === index && dragIndex !== index
                ? "mdc-agent-icebreakers-editor__row--drop-target"
                : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onDragOver={canReorder ? (event) => handleDragOver(index, event) : undefined}
            onDrop={canReorder ? (event) => handleDrop(index, event) : undefined}
            onDragLeave={
              canReorder
                ? () => {
                    if (dropIndex === index) {
                      setDropIndex(null);
                    }
                  }
                : undefined
            }
          >
            <div className="mdc-chat-agent-builder__icebreaker-row">
              {canReorder ? (
                <button
                  type="button"
                  className="mdc-agent-icebreakers-editor__drag-handle"
                  draggable
                  onDragStart={(event) => handleDragStart(index, event)}
                  onDragEnd={handleDragEnd}
                  aria-label={`Reordenar quebra-gelo ${index + 1}`}
                  title="Arrastar para reordenar"
                >
                  <GripVertical size={16} aria-hidden="true" />
                </button>
              ) : null}

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

              {canReorder ? (
                <div
                  className="mdc-agent-icebreakers-editor__reorder-actions"
                  role="group"
                  aria-label={`Mover quebra-gelo ${index + 1}`}
                >
                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__reorder-btn"
                    onClick={() => moveIcebreakerByStep(index, -1)}
                    disabled={index === 0}
                    aria-label={`Subir quebra-gelo ${index + 1}`}
                    title="Subir"
                  >
                    <ChevronUp size={15} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__reorder-btn"
                    onClick={() => moveIcebreakerByStep(index, 1)}
                    disabled={index === icebreakers.length - 1}
                    aria-label={`Descer quebra-gelo ${index + 1}`}
                    title="Descer"
                  >
                    <ChevronDown size={15} aria-hidden="true" />
                  </button>
                </div>
              ) : null}

              <button
                type="button"
                className="mdc-agent-icebreakers-editor__remove-btn"
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
        >
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar quebra-gelo</span>
        </button>
      </div>
    </div>
  );
}
