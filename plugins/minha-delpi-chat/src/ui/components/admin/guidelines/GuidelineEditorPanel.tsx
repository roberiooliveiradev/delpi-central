import { useState } from "react";

import type { SaveAdminGuidelinePayload } from "../../../../data/api/adminApi";

import "./GuidelineEditorPanel.css";

type GuidelineEditorPanelProps = {
  onSave: (payload: SaveAdminGuidelinePayload) => Promise<void>;
};

export function GuidelineEditorPanel({ onSave }: GuidelineEditorPanelProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] =
    useState<SaveAdminGuidelinePayload["category"]>("behavior");
  const [isSaving, setIsSaving] = useState(false);

  const canSave = title.trim() && content.trim();

  async function handleSave() {
    if (!canSave || isSaving) {
      return;
    }

    setIsSaving(true);

    try {
      await onSave({
        title: title.trim(),
        description: description.trim(),
        content: content.trim(),
        category,
        status: "draft",
        metadata: {
          origin: "admin_guideline_editor",
        },
      });

      setTitle("");
      setDescription("");
      setContent("");
      setCategory("behavior");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <article className="mdc-guideline-editor-panel">
      <div>
        <p className="mdc-chat-eyebrow">Nova diretriz</p>
        <h2>Criar diretriz</h2>
      </div>

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
        {isSaving ? "Salvando..." : "Salvar rascunho"}
      </button>
    </article>
  );
}
