import { ChevronDown, ChevronUp, GripVertical, Plus, X } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import {
  AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS,
  AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS,
  AGENT_ICEBREAKER_HINT_MAX_CHARS,
  AGENT_ICEBREAKER_MAX_CHARS,
  AGENT_ICEBREAKER_TITLE_MAX_CHARS,
  buildIcebreakerPlaceholderToken,
  clampIcebreakerDraft,
  clampIcebreakerHint,
  clampIcebreakerTitle,
  createEmptyIcebreakerEntry,
  createIcebreakerField,
  hasShortcutPlaceholders,
  ICEBREAKER_FIELD_TYPE_OPTIONS,
  reorderIcebreakerEntries,
  resolveIcebreakerCardPresentation,
  type AgentIcebreakerEntry,
  type IcebreakerFieldConfig,
} from "../../../agentIcebreakers";

import "./AgentIcebreakersEditor.css";

type AgentIcebreakersEditorProps = {
  entries: AgentIcebreakerEntry[];
  usingDefaults?: boolean;
  onChange: (next: AgentIcebreakerEntry[]) => void;
};

function updateEntry(
  entries: AgentIcebreakerEntry[],
  index: number,
  patch: Partial<AgentIcebreakerEntry>,
): AgentIcebreakerEntry[] {
  return entries.map((entry, entryIndex) =>
    entryIndex === index ? { ...entry, ...patch } : entry,
  );
}

function updateField(
  entries: AgentIcebreakerEntry[],
  entryIndex: number,
  fieldIndex: number,
  patch: Partial<IcebreakerFieldConfig>,
): AgentIcebreakerEntry[] {
  const entry = entries[entryIndex];
  const fields = [...(entry.fields ?? [])];

  fields[fieldIndex] = { ...fields[fieldIndex], ...patch };

  return updateEntry(entries, entryIndex, { fields });
}

export function AgentIcebreakersEditor({
  entries,
  usingDefaults = false,
  onChange,
}: AgentIcebreakersEditorProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const templateRefs = useRef<Array<HTMLTextAreaElement | null>>([]);

  const canReorder = entries.length > 1;

  function removeEntry(index: number) {
    const next = entries.filter((_, entryIndex) => entryIndex !== index);
    onChange(next.length > 0 ? next : [createEmptyIcebreakerEntry()]);
  }

  function addEntry() {
    onChange([...entries, createEmptyIcebreakerEntry()]);
  }

  function moveEntry(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex) {
      return;
    }

    onChange(reorderIcebreakerEntries(entries, fromIndex, toIndex));
  }

  function moveEntryByStep(index: number, direction: -1 | 1) {
    moveEntry(index, index + direction);
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
      moveEntry(fromIndex, index);
    }

    setDragIndex(null);
    setDropIndex(null);
  }

  function handleDragEnd() {
    setDragIndex(null);
    setDropIndex(null);
  }

  function insertPlaceholder(entryIndex: number, fieldId: string) {
    const token = buildIcebreakerPlaceholderToken(fieldId);
    const entry = entries[entryIndex];
    const input = templateRefs.current[entryIndex];
    const start = input?.selectionStart ?? entry.template.length;
    const end = input?.selectionEnd ?? entry.template.length;
    const nextTemplate = clampIcebreakerDraft(
      `${entry.template.slice(0, start)}${token}${entry.template.slice(end)}`,
    );

    onChange(updateEntry(entries, entryIndex, { template: nextTemplate }));

    requestAnimationFrame(() => {
      const nextInput = templateRefs.current[entryIndex];

      if (!nextInput) {
        return;
      }

      nextInput.focus();
      const cursor = start + token.length;
      nextInput.setSelectionRange(cursor, cursor);
    });
  }

  function addField(entryIndex: number, fieldType = "text") {
    const entry = entries[entryIndex];
    const fields = [...(entry.fields ?? [])];
    const nextField = createIcebreakerField(fields.length, fieldType);

    fields.push(nextField);
    onChange(updateEntry(entries, entryIndex, { fields }));
    insertPlaceholder(entryIndex, nextField.id);
  }

  function removeField(entryIndex: number, fieldIndex: number) {
    const entry = entries[entryIndex];
    const fields = (entry.fields ?? []).filter((_, index) => index !== fieldIndex);
    onChange(updateEntry(entries, entryIndex, { fields }));
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
        Configure título, subtítulo, pergunta e campos de entrada. Use{" "}
        <code>{buildIcebreakerPlaceholderToken("campo1")}</code> na pergunta para cada campo
        adicionado. Na home, o clique abre o diálogo com os tipos escolhidos.
      </p>

      <div className="mdc-agent-icebreakers-editor__list" aria-label="Lista de quebra-gelos">
        {entries.map((entry, index) => {
          const presentation = resolveIcebreakerCardPresentation(entry);
          const fields = entry.fields ?? [];

          return (
            <article
              key={`icebreaker-entry-${index}`}
              className={[
                "mdc-agent-icebreakers-editor__card",
                dragIndex === index ? "mdc-agent-icebreakers-editor__card--dragging" : "",
                dropIndex === index && dragIndex !== index
                  ? "mdc-agent-icebreakers-editor__card--drop-target"
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
              <div className="mdc-agent-icebreakers-editor__card-toolbar">
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

                <strong className="mdc-agent-icebreakers-editor__card-index">
                  Quebra-gelo {index + 1}
                </strong>

                <div className="mdc-agent-icebreakers-editor__card-actions">
                  {canReorder ? (
                    <>
                      <button
                        type="button"
                        className="mdc-agent-icebreakers-editor__reorder-btn"
                        onClick={() => moveEntryByStep(index, -1)}
                        disabled={index === 0}
                        aria-label={`Subir quebra-gelo ${index + 1}`}
                      >
                        <ChevronUp size={15} aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        className="mdc-agent-icebreakers-editor__reorder-btn"
                        onClick={() => moveEntryByStep(index, 1)}
                        disabled={index === entries.length - 1}
                        aria-label={`Descer quebra-gelo ${index + 1}`}
                      >
                        <ChevronDown size={15} aria-hidden="true" />
                      </button>
                    </>
                  ) : null}

                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__remove-btn"
                    onClick={() => removeEntry(index)}
                    aria-label="Remover quebra-gelo"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div className="mdc-agent-icebreakers-editor__grid">
                <label className="mdc-agent-icebreakers-editor__label">
                  <span>Título do card</span>
                  <input
                    type="text"
                    value={entry.label ?? ""}
                    maxLength={AGENT_ICEBREAKER_TITLE_MAX_CHARS}
                    placeholder="Ex.: Status fabril"
                    onChange={(event) =>
                      onChange(
                        updateEntry(entries, index, {
                          label: clampIcebreakerTitle(event.target.value),
                        }),
                      )
                    }
                  />
                </label>

                <label className="mdc-agent-icebreakers-editor__label">
                  <span>Subtítulo</span>
                  <input
                    type="text"
                    value={entry.hint ?? ""}
                    maxLength={AGENT_ICEBREAKER_HINT_MAX_CHARS}
                    placeholder="Ex.: Estrutura, MPs, produção e expedição"
                    onChange={(event) =>
                      onChange(
                        updateEntry(entries, index, {
                          hint: clampIcebreakerHint(event.target.value),
                        }),
                      )
                    }
                  />
                </label>
              </div>

              <label className="mdc-agent-icebreakers-editor__label">
                <span>Pergunta enviada ao clicar</span>
                <textarea
                  ref={(element) => {
                    templateRefs.current[index] = element;
                  }}
                  className="mdc-agent-icebreakers-editor__template"
                  value={entry.template}
                  rows={2}
                  maxLength={AGENT_ICEBREAKER_MAX_CHARS}
                  placeholder="Ex.: qual o status fabril hoje do produto {{productCode}}?"
                  onChange={(event) =>
                    onChange(
                      updateEntry(entries, index, {
                        template: clampIcebreakerDraft(event.target.value),
                      }),
                    )
                  }
                />
                <span className="mdc-agent-icebreakers-editor__count">
                  {entry.template.length}/{AGENT_ICEBREAKER_MAX_CHARS}
                </span>
              </label>

              <div className="mdc-agent-icebreakers-editor__fields-block">
                <div className="mdc-agent-icebreakers-editor__fields-head">
                  <span>Campos de entrada</span>
                  <div className="mdc-agent-icebreakers-editor__field-type-picker">
                    {ICEBREAKER_FIELD_TYPE_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className="mdc-agent-icebreakers-editor__field-type-btn"
                        onClick={() => addField(index, option.value)}
                      >
                        + {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {fields.length === 0 ? (
                  <p className="mdc-agent-icebreakers-editor__fields-empty">
                    Sem campos — a pergunta será enviada direto ao clicar.
                  </p>
                ) : (
                  <div className="mdc-agent-icebreakers-editor__fields-list">
                    {fields.map((field, fieldIndex) => (
                      <div
                        key={`${field.id}-${fieldIndex}`}
                        className="mdc-agent-icebreakers-editor__field-row"
                      >
                        <label className="mdc-agent-icebreakers-editor__mini-label">
                          <span>ID</span>
                          <input
                            type="text"
                            value={field.id}
                            maxLength={AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS}
                            onChange={(event) =>
                              onChange(
                                updateField(entries, index, fieldIndex, {
                                  id: event.target.value
                                    .replace(/[^\w]/g, "")
                                    .slice(0, AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS),
                                }),
                              )
                            }
                          />
                        </label>

                        <label className="mdc-agent-icebreakers-editor__mini-label">
                          <span>Rótulo</span>
                          <input
                            type="text"
                            value={field.label}
                            maxLength={AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS}
                            onChange={(event) =>
                              onChange(
                                updateField(entries, index, fieldIndex, {
                                  label: event.target.value.slice(
                                    0,
                                    AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS,
                                  ),
                                }),
                              )
                            }
                          />
                        </label>

                        <label className="mdc-agent-icebreakers-editor__mini-label">
                          <span>Tipo</span>
                          <select
                            value={field.fieldType}
                            onChange={(event) =>
                              onChange(
                                updateField(entries, index, fieldIndex, {
                                  fieldType: event.target.value,
                                }),
                              )
                            }
                          >
                            {ICEBREAKER_FIELD_TYPE_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label className="mdc-agent-icebreakers-editor__mini-label mdc-agent-icebreakers-editor__mini-label--grow">
                          <span>Placeholder</span>
                          <input
                            type="text"
                            value={field.placeholder ?? ""}
                            placeholder="Opcional"
                            onChange={(event) =>
                              onChange(
                                updateField(entries, index, fieldIndex, {
                                  placeholder: event.target.value.trim() || undefined,
                                }),
                              )
                            }
                          />
                        </label>

                        <label className="mdc-agent-icebreakers-editor__required">
                          <input
                            type="checkbox"
                            checked={field.required !== false}
                            onChange={(event) =>
                              onChange(
                                updateField(entries, index, fieldIndex, {
                                  required: event.target.checked,
                                }),
                              )
                            }
                          />
                          <span>Obrigatório</span>
                        </label>

                        <button
                          type="button"
                          className="mdc-agent-icebreakers-editor__insert-token"
                          onClick={() => insertPlaceholder(index, field.id)}
                          title={buildIcebreakerPlaceholderToken(field.id)}
                        >
                          Inserir {buildIcebreakerPlaceholderToken(field.id)}
                        </button>

                        <button
                          type="button"
                          className="mdc-agent-icebreakers-editor__field-remove"
                          onClick={() => removeField(index, fieldIndex)}
                          aria-label="Remover campo"
                        >
                          <X size={14} aria-hidden="true" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {entry.label?.trim() || entry.template.trim() ? (
                <p className="mdc-agent-icebreakers-editor__preview">
                  <span>Prévia no card:</span> <strong>{presentation.title}</strong>
                  {presentation.subtitle ? (
                    <>
                      {" "}
                      <em>{presentation.subtitle}</em>
                    </>
                  ) : null}
                  {hasShortcutPlaceholders(entry.template) ? (
                    <span> — ao clicar, abre diálogo com {fields.length || "os"} campo(s).</span>
                  ) : null}
                </p>
              ) : null}
            </article>
          );
        })}

        <button type="button" className="mdc-chat-ws-outline-btn" onClick={addEntry}>
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar quebra-gelo</span>
        </button>
      </div>
    </div>
  );
}
