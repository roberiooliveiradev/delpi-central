import { useEffect, useState } from "react";

import type { SaveAdminGuidelinePayload } from "../../../../data/api/adminApi";
import type { AdminGuideline } from "./guidelineTypes";

import "./GuidelineEditorPanel.css";

type GuidelineEditorPanelProps = {
  editingGuideline?: AdminGuideline | null;
  onCancelEdit?: () => void;
  onSave: (payload: SaveAdminGuidelinePayload) => Promise<void>;
};

export function GuidelineEditorPanel({
  editingGuideline,
  onCancelEdit,
  onSave,
}: GuidelineEditorPanelProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] =
    useState<SaveAdminGuidelinePayload["category"]>("behavior");
  const [isSaving, setIsSaving] = useState(false);

  const isEditing = Boolean(editingGuideline);
  const canSave = title.trim() && content.trim();

  useEffect(() => {
    if (!editingGuideline) {
      setTitle("");
      setDescription("");
      setContent("");
      setCategory("behavior");
      return;
    }

    setTitle(editingGuideline.title);
    setDescription(editingGuideline.description);
    setContent(editingGuideline.content);
    setCategory(editingGuideline.category);
  }, [editingGuideline]);

  async function handleSave() {
    if (!canSave || isSaving) {
      return;
    }

    setIsSaving(true);

    try {
      await onSave({
        id: editingGuideline?.id,
        title: title.trim(),
        description: description.trim(),
        content: content.trim(),
        category,
        status: "draft",
        metadata: {
          ...(editingGuideline?.metadata ?? {}),
          origin: "admin_guideline_editor",
          editing: isEditing,
        },
      });

      if (!isEditing) {
        setTitle("");
        setDescription("");
        setContent("");
        setCategory("behavior");
      }

      onCancelEdit?.();
    } finally {
      setIsSaving(false);
    }
  }

  function handleCancel() {
    onCancelEdit?.();

    if (!isEditing) {
      setTitle("");
      setDescription("");
      setContent("");
      setCategory("behavior");
    }
  }

  return (
    <article className="mdc-guideline-editor-panel">
      <div className="mdc-guideline-editor-panel__header">
        <div>
          <p className="mdc-chat-eyebrow">
            {isEditing ? "Editar diretriz" : "Nova diretriz"}
          </p>
          <h2>{isEditing ? "Editar rascunho" : "Criar diretriz"}</h2>
        </div>

        {isEditing ? (
          <button
            type="button"
            className="mdc-guideline-editor-panel__ghost"
            onClick={handleCancel}
          >
            Cancelar
          </button>
        ) : null}
      </div>

      {isEditing ? (
        <div className="mdc-guideline-editor-panel__notice">
          Esta alteração será salva como rascunho. Publique novamente para tornar a diretriz ativa.
        </div>
      ) : null}

      <label>
        <span>Título</span>
        <input
          value={title}
          placeholder="Ex.: Não inventar respostas"
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>

      <label>
        <span>Descrição</span>
        <input
          value={description}
          placeholder="Resumo curto da diretriz"
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>

      <label>
        <span>Categoria</span>
        <select
          value={category}
          onChange={(event) =>
            setCategory(event.target.value as SaveAdminGuidelinePayload["category"])
          }
        >
          <option value="behavior">Comportamento</option>
          <option value="rag">RAG</option>
          <option value="tools">Ferramentas</option>
          <option value="safety">Segurança</option>
        </select>
      </label>

      <label>
        <span>Conteúdo</span>
        <textarea
          value={content}
          rows={7}
          placeholder="Escreva a regra operacional que deve orientar o chat."
          onChange={(event) => setContent(event.target.value)}
        />
      </label>

      <button
        type="button"
        disabled={!canSave || isSaving}
        onClick={() => {
          void handleSave();
        }}
      >
        {isSaving
          ? "Salvando..."
          : isEditing
            ? "Salvar alteração como rascunho"
            : "Salvar rascunho"}
      </button>
    </article>
  );
}
