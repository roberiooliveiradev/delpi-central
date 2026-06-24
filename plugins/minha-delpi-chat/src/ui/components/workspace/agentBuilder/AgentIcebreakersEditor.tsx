import { ChevronDown, ChevronUp, Copy, GripVertical, Plus, X } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import {
  AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS,
  AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS,
  AGENT_ICEBREAKER_HINT_MAX_CHARS,
  AGENT_ICEBREAKER_MAX_CHARS,
  AGENT_ICEBREAKER_TITLE_MAX_CHARS,
  buildIcebreakerPlaceholderToken,
  clampIcebreakerDraft,
  clampIcebreakerHintDraft,
  clampIcebreakerTitleDraft,
  createEmptyIcebreakerEntry,
  createIcebreakerField,
  duplicateIcebreakerEntry,
  hasShortcutPlaceholders,
  ICEBREAKER_FIELD_TYPE_OPTIONS,
  reorderIcebreakerEntries,
  resolveIcebreakerCardPresentation,
  syncIcebreakerEntryFields,
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

function adjustExpandedIndicesForDuplicate(indices: Set<number>, sourceIndex: number): Set<number> {
  const next = new Set<number>();

  indices.forEach((index) => {
    if (index <= sourceIndex) {
      next.add(index);
      return;
    }

    next.add(index + 1);
  });

  next.add(sourceIndex + 1);

  return next;
}

function adjustExpandedIndices(indices: Set<number>, removedIndex: number): Set<number> {
  const next = new Set<number>();

  indices.forEach((index) => {
    if (index < removedIndex) {
      next.add(index);
    } else if (index > removedIndex) {
      next.add(index - 1);
    }
  });

  return next;
}

export function AgentIcebreakersEditor({
  entries,
  usingDefaults = false,
  onChange,
}: AgentIcebreakersEditorProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(() => new Set());
  const [newFieldType, setNewFieldType] = useState(ICEBREAKER_FIELD_TYPE_OPTIONS[0]?.value ?? "text");
  const templateRefs = useRef<Array<HTMLTextAreaElement | null>>([]);

  const canReorder = entries.length > 1;

  function toggleExpanded(index: number) {
    setExpandedIndices((current) => {
      const next = new Set(current);

      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }

      return next;
    });
  }

  function expandEntry(index: number) {
    setExpandedIndices((current) => {
      if (current.has(index)) {
        return current;
      }

      const next = new Set(current);
      next.add(index);
      return next;
    });
  }

  function removeEntry(index: number) {
    const next = entries.filter((_, entryIndex) => entryIndex !== index);
    onChange(next.length > 0 ? next : [createEmptyIcebreakerEntry()]);
    setExpandedIndices((current) => adjustExpandedIndices(current, index));
  }

  function addEntry() {
    const nextIndex = entries.length;
    onChange([...entries, createEmptyIcebreakerEntry()]);
    setExpandedIndices((current) => {
      const next = new Set(current);
      next.add(nextIndex);
      return next;
    });
  }

  function duplicateEntry(index: number) {
    onChange(duplicateIcebreakerEntry(entries, index));
    setExpandedIndices((current) => adjustExpandedIndicesForDuplicate(current, index));
  }

  function moveEntry(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex) {
      return;
    }

    onChange(reorderIcebreakerEntries(entries, fromIndex, toIndex));
    setExpandedIndices((current) => {
      const next = new Set<number>();

      current.forEach((index) => {
        if (index === fromIndex) {
          next.add(toIndex);
          return;
        }

        if (fromIndex < toIndex) {
          if (index > fromIndex && index <= toIndex) {
            next.add(index - 1);
            return;
          }
        } else if (index >= toIndex && index < fromIndex) {
          next.add(index + 1);
          return;
        }

        next.add(index);
      });

      return next;
    });
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

  function patchEntry(
    baseEntries: AgentIcebreakerEntry[],
    entryIndex: number,
    patch: Partial<AgentIcebreakerEntry>,
  ): AgentIcebreakerEntry[] {
    return baseEntries.map((item, itemIndex) =>
      itemIndex === entryIndex ? syncIcebreakerEntryFields({ ...item, ...patch }) : item,
    );
  }

  function insertPlaceholder(
    entryIndex: number,
    fieldId: string,
    baseEntries: AgentIcebreakerEntry[] = entries,
  ) {
    const token = buildIcebreakerPlaceholderToken(fieldId);
    const entry = baseEntries[entryIndex];
    const input = templateRefs.current[entryIndex];
    const start = input?.selectionStart ?? entry.template.length;
    const end = input?.selectionEnd ?? entry.template.length;
    const nextTemplate = clampIcebreakerDraft(
      `${entry.template.slice(0, start)}${token}${entry.template.slice(end)}`,
    );

    onChange(patchEntry(baseEntries, entryIndex, { template: nextTemplate }));

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

  function addField(entryIndex: number, fieldType = newFieldType) {
    expandEntry(entryIndex);

    const entry = entries[entryIndex];
    const fields = [...(entry.fields ?? [])];
    const nextField = createIcebreakerField(fields.length, fieldType);

    fields.push(nextField);
    const nextEntries = patchEntry(entries, entryIndex, { fields });
    insertPlaceholder(entryIndex, nextField.id, nextEntries);
  }

  function removeField(entryIndex: number, fieldIndex: number) {
    const entry = entries[entryIndex];
    const field = entry.fields?.[fieldIndex];
    let template = entry.template;

    if (field) {
      const token = buildIcebreakerPlaceholderToken(field.id);
      template = clampIcebreakerDraft(template.split(token).join(""));
    }

    onChange(patchEntry(entries, entryIndex, { template }));
  }

  return (
    <div className="mdc-agent-icebreakers-editor">
      {usingDefaults ? (
        <p className="mdc-agent-icebreakers-editor__notice">
          Sugestões padrão — edite e salve o rascunho para personalizar.
        </p>
      ) : null}

      <p className="mdc-agent-icebreakers-editor__lead">
        Cada card na home tem título, subtítulo e pergunta. Use{" "}
        <code>{buildIcebreakerPlaceholderToken("campo1")}</code> para pedir dados ao clicar.
      </p>

      <div className="mdc-agent-icebreakers-editor__list-head">
        <p className="mdc-agent-icebreakers-editor__list-summary">
          {entries.length} quebra-gelo{entries.length === 1 ? "" : "s"}
        </p>
        <button type="button" className="mdc-chat-ws-outline-btn" onClick={addEntry}>
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar</span>
        </button>
      </div>

      <div className="mdc-agent-icebreakers-editor__list-scroll">
        <div className="mdc-agent-icebreakers-editor__list" aria-label="Lista de quebra-gelos">
        {entries.map((entry, index) => {
          const presentation = resolveIcebreakerCardPresentation(entry);
          const fields = entry.fields ?? [];
          const cardTitle = entry.label?.trim() || `Sugestão ${index + 1}`;
          const isExpanded = expandedIndices.has(index);
          const fieldCount = fields.length;
          const hasDialog = hasShortcutPlaceholders(entry.template) && fieldCount > 0;

          return (
            <article
              key={`icebreaker-entry-${index}`}
              className={[
                "mdc-agent-icebreakers-editor__card",
                isExpanded ? "mdc-agent-icebreakers-editor__card--expanded" : "",
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
              <header className="mdc-agent-icebreakers-editor__card-head">
                {canReorder ? (
                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__drag-handle"
                    draggable
                    onDragStart={(event) => handleDragStart(index, event)}
                    onDragEnd={handleDragEnd}
                    aria-label={`Reordenar ${cardTitle}`}
                    title="Arrastar para reordenar"
                  >
                    <GripVertical size={15} aria-hidden="true" />
                  </button>
                ) : null}

                <button
                  type="button"
                  className="mdc-agent-icebreakers-editor__card-toggle"
                  aria-expanded={isExpanded}
                  aria-controls={`icebreaker-panel-${index}`}
                  onClick={() => toggleExpanded(index)}
                >
                  <div className="mdc-agent-icebreakers-editor__card-title">
                    <span className="mdc-agent-icebreakers-editor__card-title-text">{cardTitle}</span>
                    {presentation.subtitle ? (
                      <span className="mdc-agent-icebreakers-editor__card-subtitle">
                        {presentation.subtitle}
                      </span>
                    ) : null}
                    {!isExpanded && entry.template.trim() ? (
                      <span className="mdc-agent-icebreakers-editor__card-meta">
                        {hasDialog
                          ? `${fieldCount} campo${fieldCount === 1 ? "" : "s"} no diálogo`
                          : "envio direto"}
                      </span>
                    ) : null}
                  </div>
                  <ChevronDown
                    size={16}
                    aria-hidden="true"
                    className="mdc-agent-icebreakers-editor__card-chevron"
                  />
                </button>

                <div className="mdc-agent-icebreakers-editor__card-actions">
                  {canReorder ? (
                    <>
                      <button
                        type="button"
                        className="mdc-agent-icebreakers-editor__icon-btn"
                        onClick={() => moveEntryByStep(index, -1)}
                        disabled={index === 0}
                        aria-label={`Subir ${cardTitle}`}
                      >
                        <ChevronUp size={15} aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        className="mdc-agent-icebreakers-editor__icon-btn"
                        onClick={() => moveEntryByStep(index, 1)}
                        disabled={index === entries.length - 1}
                        aria-label={`Descer ${cardTitle}`}
                      >
                        <ChevronDown size={15} aria-hidden="true" />
                      </button>
                    </>
                  ) : null}
                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__icon-btn"
                    onClick={() => duplicateEntry(index)}
                    aria-label={`Duplicar ${cardTitle}`}
                    title="Duplicar quebra-gelo"
                  >
                    <Copy size={15} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    className="mdc-agent-icebreakers-editor__icon-btn mdc-agent-icebreakers-editor__icon-btn--danger"
                    onClick={() => removeEntry(index)}
                    aria-label={`Remover ${cardTitle}`}
                  >
                    <X size={15} aria-hidden="true" />
                  </button>
                </div>
              </header>

              {isExpanded ? (
                <div
                  id={`icebreaker-panel-${index}`}
                  className="mdc-agent-icebreakers-editor__card-body"
                >
                  <div className="mdc-agent-icebreakers-editor__row mdc-agent-icebreakers-editor__row--2">
                    <label className="mdc-chat-ws-field">
                      <span>Título do card</span>
                      <input
                        type="text"
                        value={entry.label ?? ""}
                        maxLength={AGENT_ICEBREAKER_TITLE_MAX_CHARS}
                        placeholder="Ex.: Status fabril"
                        onChange={(event) =>
                          onChange(
                            updateEntry(entries, index, {
                              label: clampIcebreakerTitleDraft(event.target.value),
                            }),
                          )
                        }
                      />
                    </label>

                    <label className="mdc-chat-ws-field">
                      <span>Subtítulo</span>
                      <input
                        type="text"
                        value={entry.hint ?? ""}
                        maxLength={AGENT_ICEBREAKER_HINT_MAX_CHARS}
                        placeholder="Ex.: Estrutura, MPs, produção e expedição"
                        onChange={(event) =>
                          onChange(
                            updateEntry(entries, index, {
                              hint: clampIcebreakerHintDraft(event.target.value),
                            }),
                          )
                        }
                      />
                    </label>
                  </div>

                  <label className="mdc-chat-ws-field">
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
                          patchEntry(entries, index, {
                            template: clampIcebreakerDraft(event.target.value),
                          }),
                        )
                      }
                    />
                    <small className="mdc-agent-icebreakers-editor__count">
                      {entry.template.length}/{AGENT_ICEBREAKER_MAX_CHARS}
                    </small>
                  </label>

                  <section className="mdc-agent-icebreakers-editor__fields">
                    <div className="mdc-agent-icebreakers-editor__fields-top">
                      <span className="mdc-agent-icebreakers-editor__fields-label">Campos de entrada</span>
                      <div className="mdc-agent-icebreakers-editor__add-field">
                        <select
                          value={newFieldType}
                          onChange={(event) => setNewFieldType(event.target.value)}
                          aria-label="Tipo do novo campo"
                        >
                          {ICEBREAKER_FIELD_TYPE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className="mdc-chat-ws-outline-btn"
                          onClick={() => addField(index)}
                        >
                          <Plus size={14} aria-hidden="true" />
                          <span>Adicionar</span>
                        </button>
                      </div>
                    </div>

                    {fields.length === 0 ? (
                      <p className="mdc-agent-icebreakers-editor__fields-empty">
                        Nenhum campo — a pergunta é enviada direto ao clicar.
                      </p>
                    ) : (
                      <div className="mdc-agent-icebreakers-editor__fields-list">
                        {fields.map((field, fieldIndex) => (
                          <div
                            key={`${field.id}-${fieldIndex}`}
                            className="mdc-agent-icebreakers-editor__field-card"
                          >
                            <div className="mdc-agent-icebreakers-editor__field-card-head">
                              <strong>{field.label || field.id}</strong>
                              <div className="mdc-agent-icebreakers-editor__field-card-actions">
                                <button
                                  type="button"
                                  className="mdc-chat-ws-outline-btn mdc-agent-icebreakers-editor__token-btn"
                                  onClick={() => insertPlaceholder(index, field.id)}
                                  title={buildIcebreakerPlaceholderToken(field.id)}
                                >
                                  Inserir {buildIcebreakerPlaceholderToken(field.id)}
                                </button>
                                <button
                                  type="button"
                                  className="mdc-agent-icebreakers-editor__icon-btn mdc-agent-icebreakers-editor__icon-btn--danger"
                                  onClick={() => removeField(index, fieldIndex)}
                                  aria-label="Remover campo"
                                >
                                  <X size={14} aria-hidden="true" />
                                </button>
                              </div>
                            </div>

                            <div className="mdc-agent-icebreakers-editor__row mdc-agent-icebreakers-editor__row--2">
                              <label className="mdc-chat-ws-field">
                                <span>ID na pergunta</span>
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

                              <label className="mdc-chat-ws-field">
                                <span>Rótulo no diálogo</span>
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
                            </div>

                            <div className="mdc-agent-icebreakers-editor__row mdc-agent-icebreakers-editor__row--meta">
                              <label className="mdc-chat-ws-field">
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

                              <label className="mdc-chat-ws-field">
                                <span>Placeholder</span>
                                <input
                                  type="text"
                                  value={field.placeholder ?? ""}
                                  placeholder="Opcional"
                                  onChange={(event) =>
                                    onChange(
                                      updateField(entries, index, fieldIndex, {
                                        placeholder: event.target.value || undefined,
                                      }),
                                    )
                                  }
                                />
                              </label>

                              <div className="mdc-agent-icebreakers-editor__required-wrap">
                                <label className="mdc-chat-ws-checkbox-row mdc-agent-icebreakers-editor__required">
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
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>

                  {entry.label?.trim() || entry.template.trim() ? (
                    <p className="mdc-agent-icebreakers-editor__preview">
                      <span>Prévia:</span> {presentation.title}
                      {presentation.subtitle ? ` · ${presentation.subtitle}` : ""}
                      {hasDialog ? ` · diálogo com ${fieldCount} campo(s)` : ""}
                    </p>
                  ) : null}
                </div>
              ) : null}
            </article>
          );
        })}
        </div>
      </div>
    </div>
  );
}
