import { Folder, Lightbulb, Plus, Settings, X } from "lucide-react";
import { useState } from "react";

import type { ChatProject } from "../../data/api/chatTypes";

import { ChatModal } from "./shared/modal/ChatModal";
import "./ChatProjectCreateModal.css";

type ChatProjectCreateModalProps = {
  open: boolean;
  onClose: () => void;
  onCreateProject?: (payload: {
    name: string;
    description?: string | null;
    instructions?: string | null;
  }) => Promise<ChatProject | null>;
  onSelectProject?: (projectId: string | null) => void;
};

export function ChatProjectCreateModal({
  open,
  onClose,
  onCreateProject,
  onSelectProject,
}: ChatProjectCreateModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const canSubmit = name.trim().length >= 2 && !isSaving;

  async function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    setIsSaving(true);

    try {
      const project = await onCreateProject?.({
        name: name.trim(),
        description: description.trim() || null,
        instructions: instructions.trim() || null,
      });

      if (project) {
        onSelectProject?.(project.id);
      }

      setName("");
      setDescription("");
      setInstructions("");
      onClose();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="none"
      panelClassName="mdc-chat-project-create-modal"
      backdropClassName="mdc-chat-project-create-backdrop"
      ariaLabel="Criar projeto"
    >
      <header>
        <h2>Criar projeto</h2>

        <div>
          <button type="button" aria-label="Configurações de memória" title="Em breve">
            <Settings size={19} aria-hidden="true" />
          </button>

          <button type="button" onClick={onClose} aria-label="Fechar">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
      </header>

      <label className="mdc-chat-project-create-modal__field">
        <span>Nome do projeto</span>
        <span className="mdc-chat-project-create-modal__input-wrap">
          <Folder size={18} aria-hidden="true" />
          <input
            value={name}
            autoFocus
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Qualidade, Engenharia..."
            onKeyDown={(event) => {
              if (event.key === "Enter" && canSubmit) {
                event.preventDefault();
                void handleSubmit();
              }
            }}
          />
        </span>
      </label>

      <details className="mdc-chat-project-create-modal__details">
        <summary>Mais opções</summary>
        <div className="mdc-chat-project-create-modal__details-body">
          <label className="mdc-chat-project-create-modal__field">
            <span>Descrição</span>
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Explique o objetivo deste projeto..."
            />
          </label>

          <label className="mdc-chat-project-create-modal__field">
            <span>Instruções</span>
            <textarea
              value={instructions}
              onChange={(event) => setInstructions(event.target.value)}
              placeholder="Contexto e regras usadas nas conversas deste projeto..."
              rows={4}
            />
          </label>
        </div>
      </details>

      <div className="mdc-chat-project-create-modal__hint">
        <Lightbulb size={18} aria-hidden="true" />
        <p>
          Os projetos mantêm conversas e arquivos em um só lugar. Use-os para colaborar em
          equipe e manter as coisas organizadas.
        </p>
      </div>

      <footer>
        <button type="button" className="mdc-chat-ws-toolbar-btn" onClick={onClose}>
          <span>Cancelar</span>
        </button>
        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          onClick={() => void handleSubmit()}
          disabled={!canSubmit}
        >
          <Plus size={16} aria-hidden="true" />
          <span>{isSaving ? "Criando..." : "Criar projeto"}</span>
        </button>
      </footer>
    </ChatModal>
  );
}
