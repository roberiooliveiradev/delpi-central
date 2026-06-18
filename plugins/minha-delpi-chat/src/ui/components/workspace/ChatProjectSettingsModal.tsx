import { Copy, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listChatProjectShares,
  revokeChatProjectShare,
  shareChatProject,
} from "../../../data/api/chatApi";
import type { ChatProject, ChatProjectShare } from "../../../data/api/chatTypes";
import { buildChatProjectHref } from "../../../navigation/chatRoutes";
import { handleChatNavClick } from "../../../navigation/chatNavigation";
import { useConfirmDialog } from "../shared";
import { ChatModal } from "../shared/modal/ChatModal";
import { ChatUserSearchField } from "../shared/ChatUserSearchField";

import "./ChatProjectHome.css";

export type ChatProjectSettingsUpdatePayload = {
  name?: string;
  description?: string | null;
  instructions?: string | null;
  shareConversationContext?: boolean;
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
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function resolveShareConversationContext(project: ChatProject): boolean {
  return Boolean(
    project.shareConversationContext
      ?? project.share_conversation_context
      ?? project.metadata?.shareConversationContext,
  );
}

export function ChatProjectSettingsModal({
  project,
  open,
  onClose,
  onUpdateProject,
  onDeleteProject,
  onClearProject,
  getAccessToken,
}: ChatProjectSettingsModalProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [instructions, setInstructions] = useState(project.instructions || "");
  const [shareConversationContext, setShareConversationContext] = useState(
    resolveShareConversationContext(project),
  );
  const [isSaving, setIsSaving] = useState(false);
  const [projectShares, setProjectShares] = useState<ChatProjectShare[]>([]);
  const [shareTargetUserId, setShareTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState<"viewer" | "editor">("viewer");
  const [isSharingProject, setIsSharingProject] = useState(false);
  const [isLoadingShares, setIsLoadingShares] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const [revokingShareUserId, setRevokingShareUserId] = useState<string | null>(null);
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
    setDescription(project.description || "");
    setInstructions(project.instructions || "");
    setShareConversationContext(resolveShareConversationContext(project));
  }, [
    project.description,
    project.instructions,
    project.metadata,
    project.name,
    project.shareConversationContext,
    project.share_conversation_context,
  ]);

  const loadProjectShares = useCallback(async () => {
    if (!getAccessToken || project.access_role !== "owner") {
      setProjectShares([]);
      return;
    }

    setIsLoadingShares(true);

    try {
      const shares = await listChatProjectShares(project.id, { getAccessToken });
      setProjectShares(shares);
    } catch {
      setProjectShares([]);
    } finally {
      setIsLoadingShares(false);
    }
  }, [getAccessToken, project.access_role, project.id]);

  useEffect(() => {
    if (open) {
      void loadProjectShares();
    }
  }, [open, loadProjectShares]);

  async function copyProjectUsageLink() {
    try {
      await navigator.clipboard.writeText(projectUsageUrl);
      setProjectLinkCopied(true);
      window.setTimeout(() => setProjectLinkCopied(false), 1800);
    } catch {
      setShareMessage("Não foi possível copiar o link do projeto.");
    }
  }

  async function shareCurrentProject() {
    if (project.access_role !== "owner" || !getAccessToken) {
      return;
    }

    const targetUserId = shareTargetUserId.trim();

    if (!targetUserId) {
      setShareMessage("Selecione um usuário para compartilhar.");
      return;
    }

    setIsSharingProject(true);
    setShareMessage(null);

    try {
      await shareChatProject(
        project.id,
        { targetUserId, role: shareRole },
        { getAccessToken },
      );
      setShareMessage("Projeto compartilhado com sucesso.");
      setShareTargetUserId("");
      await loadProjectShares();
    } catch {
      setShareMessage("Não foi possível compartilhar o projeto.");
    } finally {
      setIsSharingProject(false);
    }
  }

  async function revokeProjectShare(targetUserId: string) {
    if (!getAccessToken) {
      return;
    }

    setRevokingShareUserId(targetUserId);

    try {
      await revokeChatProjectShare(project.id, targetUserId, { getAccessToken });
      setShareMessage("Acesso revogado.");
      await loadProjectShares();
    } catch {
      setShareMessage("Não foi possível revogar o acesso.");
    } finally {
      setRevokingShareUserId(null);
    }
  }

  async function saveSettings() {
    setIsSaving(true);

    try {
      await onUpdateProject?.(project.id, {
        name: name.trim() || project.name,
        description: description.trim() || null,
        instructions: instructions.trim() || null,
        shareConversationContext,
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
        <button type="button" onClick={onClose} aria-label="Fechar">
          <X size={20} aria-hidden="true" />
        </button>
      </header>

      <label className="mdc-chat-project-settings__field">
        <span>Nome do projeto</span>
        <input value={name} onChange={(event) => setName(event.target.value)} />
      </label>

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
        <textarea
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
          rows={6}
          placeholder="Defina o contexto e personalize como o assistente responde neste projeto."
        />
        <small className="mdc-chat-project-settings__help">
          O projeto só usa estas instruções nas conversas deste espaço.
        </small>
      </label>

      <label className="mdc-chat-ws-checkbox-row mdc-chat-project-settings__toggle">
        <input
          type="checkbox"
          checked={shareConversationContext}
          onChange={(event) => setShareConversationContext(event.target.checked)}
        />
        <span>
          <strong>Compartilhar contexto entre conversas</strong>
          <small>
            Novas mensagens podem usar resumos das outras conversas deste projeto
            (consultas, filial, período e anexos indexados na sessão).
          </small>
        </span>
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
            className="mdc-chat-ws-outline-btn"
            onClick={() => void copyProjectUsageLink()}
            title="Copiar link do projeto"
          >
            <Copy size={15} aria-hidden="true" />
            <span>{projectLinkCopied ? "Copiado" : "Copiar"}</span>
          </button>
        </div>
        <small>Mesma URL usada ao abrir o projeto no chat.</small>
      </div>

      {project.access_role === "owner" ? (
        <section className="mdc-chat-project-settings__share">
          <h4>Compartilhamento</h4>
          <p className="mdc-chat-muted">
            Conceda acesso de visualização ou edição a outro usuário.
          </p>

          <div className="mdc-chat-project-settings__share-form">
            <ChatUserSearchField
              value={shareTargetUserId}
              onChange={setShareTargetUserId}
              getAccessToken={getAccessToken}
              disabled={isSharingProject}
            />

            <label>
              <span>Papel</span>
              <select
                value={shareRole}
                onChange={(event) => setShareRole(event.target.value as "viewer" | "editor")}
              >
                <option value="viewer">Visualizador</option>
                <option value="editor">Editor</option>
              </select>
            </label>
          </div>

          <button
            type="button"
            className="mdc-chat-ws-outline-btn mdc-chat-project-settings__share-btn"
            disabled={isSharingProject}
            onClick={() => void shareCurrentProject()}
          >
            <span>{isSharingProject ? "Compartilhando..." : "Compartilhar projeto"}</span>
          </button>

          {shareMessage ? <p className="mdc-chat-muted">{shareMessage}</p> : null}

          <div className="mdc-chat-project-settings__share-list">
            {isLoadingShares ? (
              <p className="mdc-chat-muted">Carregando compartilhamentos...</p>
            ) : projectShares.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum compartilhamento ativo.</p>
            ) : (
              projectShares.map((share) => (
                <article key={share.id}>
                  <span>
                    <strong>
                      {share.target_user_name ||
                        share.target_user_email ||
                        share.target_user_id}
                    </strong>
                    <small>
                      {share.target_user_email
                        ? `${share.target_user_email} · ${share.role}`
                        : share.role}
                    </small>
                  </span>
                  <button
                    type="button"
                    className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                    disabled={revokingShareUserId === share.target_user_id}
                    onClick={() => void revokeProjectShare(share.target_user_id)}
                  >
                    {revokingShareUserId === share.target_user_id
                      ? "Revogando..."
                      : "Revogar"}
                  </button>
                </article>
              ))
            )}
          </div>
        </section>
      ) : null}

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
