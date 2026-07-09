import { Copy, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatProject } from "../../../data/api/chatTypes";
import { buildChatProjectHref } from "../../../navigation/chatRoutes";
import { handleChatNavClick } from "../../../navigation/chatNavigation";
import { useConfirmDialog } from "../shared";
import { ChatModal } from "../shared/modal/ChatModal";
import {
  normalizeProjectIcon,
  PROJECT_ICON_LABELS,
  PROJECT_ICON_OPTIONS,
} from "./chatProjectIcon";
import { ChatProjectIcon } from "./ChatProjectIcon";
import { ChatNativeTextAreaControl } from "../admin/shared/chatAdminFormFields";
import { ChatWorkspaceIconPicker } from "./ChatWorkspaceIconPicker";

import "./ChatProjectHome.css";

export type ChatProjectSettingsUpdatePayload = {
  name?: string;
  description?: string | null;
  instructions?: string | null;
  icon?: string | null;
};

type ChatProjectSettingsModalProps = {
  project: ChatProject;
  open: boolean;
  onClose: () => void;
  onUpdateProject?: (
    projectId: string,
    payload: ChatProjectSettingsUpdatePayload,
  ) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onClearProject?: () => void;
  /** Reservado para compartilhamento colaborativo (implementação futura). */
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatProjectSettingsModal({
  project,
  open,
  onClose,
  onUpdateProject,
  onDeleteProject,
  onClearProject,
}: ChatProjectSettingsModalProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [name, setName] = useState(project.name);
  const [icon, setIcon] = useState<string>(() => normalizeProjectIcon(project.icon));
  const [description, setDescription] = useState(project.description || "");
  const [instructions, setInstructions] = useState(project.instructions || "");
  const [isSaving, setIsSaving] = useState(false);
  const [projectLinkCopied, setProjectLinkCopied] = useState(false);

  const projectUsagePath = useMemo(() => buildChatProjectHref(project.id), [project.id]);
  const projectUsageUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return projectUsagePath;
    }

    return `${window.location.origin}${projectUsagePath}`;
  }, [projectUsagePath]);

  useEffect(() => {
    setName(project.name);
    setIcon(normalizeProjectIcon(project.icon));
    setDescription(project.description || "");
    setInstructions(project.instructions || "");
  }, [project.description, project.icon, project.name, project.instructions]);

  async function copyProjectUsageLink() {
    try {
      await navigator.clipboard.writeText(projectUsageUrl);
      setProjectLinkCopied(true);
      window.setTimeout(() => setProjectLinkCopied(false), 1800);
    } catch {
      // Falha silenciosa — usuário pode copiar manualmente pelo link.
    }
  }

  async function saveSettings() {
    setIsSaving(true);

    try {
      await onUpdateProject?.(project.id, {
        name: name.trim() || project.name,
        description: description.trim() || null,
        instructions: instructions.trim() || null,
        icon: normalizeProjectIcon(icon),
      });
      onClose();
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteProject() {
    const confirmed = await confirm({
      title: "Excluir projeto",
      description: `Excluir o projeto "${project.name}"?`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteProject?.(project.id);

    if (deleted) {
      onClearProject?.();
      onClose();
    }
  }

  return (
    <>
      {confirmDialog}
      <ChatModal
        open={open}
        onClose={onClose}
        size="none"
        panelClassName="mdc-chat-project-settings"
        ariaLabel="Configurações do projeto"
      >
        <header>
          <h3>Configurações do projeto</h3>
          <button
            type="button"
            className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
            onClick={onClose}
            aria-label="Fechar"
          >
            <X aria-hidden="true" />
          </button>
        </header>

        <label className="mdc-chat-project-settings__field">
          <span>Nome do projeto</span>
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>

        <div className="mdc-chat-project-settings__field">
          <span>Ícone</span>
          <ChatWorkspaceIconPicker
            options={PROJECT_ICON_OPTIONS}
            labels={PROJECT_ICON_LABELS}
            value={icon}
            onChange={setIcon}
            renderIcon={(option, size) => <ChatProjectIcon icon={option} size={size} />}
            ariaLabel="Ícone do projeto"
          />
        </div>

        <label className="mdc-chat-project-settings__field">
          <span>Descrição</span>
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Explique o objetivo deste projeto..."
          />
        </label>

        <label className="mdc-chat-project-settings__field">
          <span>Instruções</span>
          <ChatNativeTextAreaControl
            value={instructions}
            onChange={setInstructions}
            rows={6}
            placeholder="Defina o contexto e personalize como o assistente responde neste projeto."
          />
          <small className="mdc-chat-project-settings__help">
            O projeto só usa estas instruções nas conversas deste espaço.
          </small>
        </label>

        <div className="mdc-chat-project-settings__link">
          <span className="mdc-chat-project-settings__link-label">Link de uso</span>
          <div className="mdc-chat-project-settings__link-row">
            <a
              href={projectUsagePath}
              onClick={(event) => handleChatNavClick(event, projectUsagePath)}
            >
              {projectUsageUrl}
            </a>
            <button
              type="button"
              className="mdc-chat-ws-outline-btn mdc-chat-modal-tool-btn"
              onClick={() => void copyProjectUsageLink()}
              title="Copiar link do projeto"
            >
              <Copy size={15} aria-hidden="true" />
              <span>{projectLinkCopied ? "Copiado" : "Copiar"}</span>
            </button>
          </div>
          <small>Mesma URL usada ao abrir o projeto no chat.</small>
        </div>

        <footer className="mdc-chat-project-settings__footer">
          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
            onClick={() => void deleteProject()}
          >
            <span>Excluir projeto</span>
          </button>

          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
            onClick={() => void saveSettings()}
            disabled={isSaving}
          >
            <span>{isSaving ? "Salvando..." : "Salvar"}</span>
          </button>
        </footer>
      </ChatModal>
    </>
  );
}
