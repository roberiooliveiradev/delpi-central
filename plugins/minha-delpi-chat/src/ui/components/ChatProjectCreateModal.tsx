import { Settings, X } from "lucide-react";
import { useState } from "react";

import type { ChatProject } from "../../data/api/chatTypes";

import { ModalPortal } from "./ModalPortal";
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

  if (!open) {
    return null;
  }

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
    <ModalPortal>
      <div
        className="mdc-chat-project-create-backdrop"
        role="presentation"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onClose();
          }
        }}
      >
      <section
        className="mdc-chat-project-create-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Criar projeto"
      >
        <header>
          <h2>Criar projeto</h2>

          <div>
            <button type="button" aria-label="Configurações de memória">
              <Settings size={19} aria-hidden="true" />
            </button>

            <button type="button" onClick={onClose} aria-label="Fechar">
              <X size={20} aria-hidden="true" />
            </button>
          </div>
        </header>

        <label>
          <span>Nome do projeto</span>
          <input
            value={name}
            autoFocus
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Qualidade, Engenharia, Viagem..."
          />
        </label>

        <label>
          <span>Descrição</span>
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Explique o objetivo deste projeto..."
          />
        </label>

        <label>
          <span>Contexto e instruções</span>
          <textarea
            value={instructions}
            onChange={(event) => setInstructions(event.target.value)}
            placeholder="Defina regras, escopo, preferências e contexto usado nas conversas deste projeto..."
            rows={4}
          />
        </label>

        <div className="mdc-chat-project-create-modal__hint">
          <span>💡</span>
          <p>
            Os projetos mantêm chats, documentos, agentes e instruções em um só
            lugar. Use-os para trabalhos em andamento ou para separar contextos.
          </p>
        </div>

        <footer>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
          >
            {isSaving ? "Criando..." : "Criar projeto"}
          </button>
        </footer>
      </section>
      </div>
    </ModalPortal>
  );
}
