import { ChatNativeTextInput } from "../../shared/chatNativeFormFields";
import { useEffect, useState } from "react";

import type { SaveAdminGuidelinePayload } from "../../../../data/api/adminApi";
import type { AdminGuideline } from "./guidelineTypes";
import {
  ChatAdminNativeSelectField,
  ChatAdminNativeTextAreaField,
} from "../shared/chatAdminFormFields";

import "./GuidelineEditorPanel.css";

type GuidelineEditorPanelProps = {
  editingGuideline?: AdminGuideline | null;
  canCreateGuidelines: boolean;
  onCancelEdit?: () => void;
  onSave: (payload: SaveAdminGuidelinePayload) => Promise<void>;
};

export function GuidelineEditorPanel({
  editingGuideline,
  canCreateGuidelines,
  onCancelEdit,
  onSave,
}: GuidelineEditorPanelProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] =
    useState<SaveAdminGuidelinePayload["category"]>("behavior");
  const [environment, setEnvironment] =
    useState<SaveAdminGuidelinePayload["environment"]>("global");
  const [isSaving, setIsSaving] = useState(false);

  const isEditing = Boolean(editingGuideline);
  const canSave = title.trim() && content.trim();

  useEffect(() => {
    if (!editingGuideline) {
      setTitle("");
      setDescription("");
      setContent("");
      setCategory("behavior");
      setEnvironment("global");
      return;
    }

    setTitle(editingGuideline.title);
    setDescription(editingGuideline.description);
    setContent(editingGuideline.content);
    setCategory(editingGuideline.category);
    setEnvironment(editingGuideline.environment ?? "global");
  }, [editingGuideline]);

  async function handleSave() {
    if (!canCreateGuidelines || !canSave || isSaving) {
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
        environment,
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
        setEnvironment("global");
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
        <ChatNativeTextInput
          value={title}
          disabled={!canCreateGuidelines}
          placeholder="Ex.: Não inventar respostas"
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>

      <label>
        <span>Descrição</span>
        <ChatNativeTextInput
          value={description}
          disabled={!canCreateGuidelines}
          placeholder="Resumo curto da diretriz"
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>

      <ChatAdminNativeSelectField
        id="guideline-editor-category"
        label="Categoria"
        span={false}
        value={category}
        disabled={!canCreateGuidelines}
        options={[
          { value: "behavior", label: "Comportamento" },
          { value: "rag", label: "RAG" },
          { value: "tools", label: "Ferramentas" },
          { value: "safety", label: "Segurança" },
        ]}
        onChange={(value) =>
          setCategory(value as SaveAdminGuidelinePayload["category"])
        }
      />

      <ChatAdminNativeSelectField
        id="guideline-editor-environment"
        label="Ambiente"
        span={false}
        value={environment}
        disabled={!canCreateGuidelines}
        options={[
          { value: "global", label: "Global" },
          { value: "dev", label: "DEV" },
          { value: "homolog", label: "HOMOLOG" },
          { value: "prod", label: "PROD" },
        ]}
        onChange={(value) =>
          setEnvironment(value as SaveAdminGuidelinePayload["environment"])
        }
      />

      <ChatAdminNativeTextAreaField
        id="guideline-editor-content"
        label="Conteúdo"
        span={false}
        rows={7}
        value={content}
        disabled={!canCreateGuidelines}
        placeholder="Escreva a regra operacional que deve orientar o chat."
        onChange={setContent}
      />

      <button
        type="button"
        disabled={!canCreateGuidelines || !canSave || isSaving}
        title={
          canCreateGuidelines
            ? undefined
            : "Você não tem permissão para criar ou editar diretrizes."
        }
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
