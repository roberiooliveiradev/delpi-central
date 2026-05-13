import { useCallback, useEffect, useState } from "react";

import {
  createChatAgent,
  createChatProject,
  deleteChatAgent,
  deleteChatProject,
  listChatAgents,
  listChatProjects,
  shareChatAgent,
  shareChatProject,
  updateChatAgent,
  updateChatProject,
  upsertChatAgentAction,
} from "../../data/api/chatApi";
import type {
  ChatAgent,
  ChatProject,
  CreateChatAgentPayload,
  CreateChatProjectPayload,
  ShareChatAgentPayload,
  ShareChatProjectPayload,
  UpdateChatAgentPayload,
  UpdateChatProjectPayload,
  UpsertChatAgentActionPayload,
} from "../../data/api/chatTypes";

type UseChatWorkspaceOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatWorkspace(options: UseChatWorkspaceOptions = {}) {
  const [agents, setAgents] = useState<ChatAgent[]>([]);
  const [projects, setProjects] = useState<ChatProject[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  const loadAgents = useCallback(async () => {
    setIsLoadingAgents(true);
    setWorkspaceError(null);

    try {
      const data = await listChatAgents({
        getAccessToken: options.getAccessToken,
      });

      setAgents(data);
    } catch (err) {
      setWorkspaceError(
        err instanceof Error ? err.message : "Erro ao carregar agentes.",
      );
    } finally {
      setIsLoadingAgents(false);
    }
  }, [options.getAccessToken]);

  const loadProjects = useCallback(async () => {
    setIsLoadingProjects(true);
    setWorkspaceError(null);

    try {
      const data = await listChatProjects({
        getAccessToken: options.getAccessToken,
      });

      setProjects(data);
    } catch (err) {
      setWorkspaceError(
        err instanceof Error ? err.message : "Erro ao carregar projetos.",
      );
    } finally {
      setIsLoadingProjects(false);
    }
  }, [options.getAccessToken]);

  const addAgent = useCallback(
    async (payload: CreateChatAgentPayload) => {
      setWorkspaceError(null);

      try {
        const agent = await createChatAgent(payload, {
          getAccessToken: options.getAccessToken,
        });

        setAgents((current) => [agent, ...current]);
        return agent;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao criar agente.",
        );
        return null;
      }
    },
    [options.getAccessToken],
  );

  const editAgent = useCallback(
    async (agentId: string, payload: UpdateChatAgentPayload) => {
      setWorkspaceError(null);

      try {
        const agent = await updateChatAgent(agentId, payload, {
          getAccessToken: options.getAccessToken,
        });

        setAgents((current) =>
          current.map((item) => (item.id === agent.id ? agent : item)),
        );

        return agent;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao atualizar agente.",
        );
        return null;
      }
    },
    [options.getAccessToken],
  );

  const removeAgent = useCallback(
    async (agentId: string) => {
      setWorkspaceError(null);

      try {
        await deleteChatAgent(agentId, {
          getAccessToken: options.getAccessToken,
        });

        setAgents((current) => current.filter((agent) => agent.id !== agentId));
        return true;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao excluir agente.",
        );
        return false;
      }
    },
    [options.getAccessToken],
  );

  const shareAgent = useCallback(
    async (agentId: string, payload: ShareChatAgentPayload) => {
      setWorkspaceError(null);

      try {
        await shareChatAgent(agentId, payload, {
          getAccessToken: options.getAccessToken,
        });

        return true;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao compartilhar agente.",
        );
        return false;
      }
    },
    [options.getAccessToken],
  );

  const saveAgentAction = useCallback(
    async (agentId: string, payload: UpsertChatAgentActionPayload) => {
      setWorkspaceError(null);

      try {
        await upsertChatAgentAction(agentId, payload, {
          getAccessToken: options.getAccessToken,
        });

        return true;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao salvar action do agente.",
        );
        return false;
      }
    },
    [options.getAccessToken],
  );

  const addProject = useCallback(
    async (payload: CreateChatProjectPayload) => {
      setWorkspaceError(null);

      try {
        const project = await createChatProject(payload, {
          getAccessToken: options.getAccessToken,
        });

        setProjects((current) => [project, ...current]);
        return project;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao criar projeto.",
        );
        return null;
      }
    },
    [options.getAccessToken],
  );

  const editProject = useCallback(
    async (projectId: string, payload: UpdateChatProjectPayload) => {
      setWorkspaceError(null);

      try {
        const project = await updateChatProject(projectId, payload, {
          getAccessToken: options.getAccessToken,
        });

        setProjects((current) =>
          current.map((item) => (item.id === project.id ? project : item)),
        );

        return project;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao atualizar projeto.",
        );
        return null;
      }
    },
    [options.getAccessToken],
  );

  const shareProject = useCallback(
    async (projectId: string, payload: ShareChatProjectPayload) => {
      setWorkspaceError(null);

      try {
        await shareChatProject(projectId, payload, {
          getAccessToken: options.getAccessToken,
        });

        return true;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao compartilhar projeto.",
        );
        return false;
      }
    },
    [options.getAccessToken],
  );

  const removeProject = useCallback(
    async (projectId: string) => {
      setWorkspaceError(null);

      try {
        await deleteChatProject(projectId, {
          getAccessToken: options.getAccessToken,
        });

        setProjects((current) =>
          current.filter((project) => project.id !== projectId),
        );

        return true;
      } catch (err) {
        setWorkspaceError(
          err instanceof Error ? err.message : "Erro ao excluir projeto.",
        );
        return false;
      }
    },
    [options.getAccessToken],
  );

  const clearWorkspaceError = useCallback(() => {
    setWorkspaceError(null);
  }, []);

  useEffect(() => {
    void loadAgents();
    void loadProjects();
  }, [loadAgents, loadProjects]);

  return {
    agents,
    projects,
    isLoadingAgents,
    isLoadingProjects,
    workspaceError,
    clearWorkspaceError,
    loadAgents,
    loadProjects,
    addAgent,
    editAgent,
    removeAgent,
    shareAgent,
    saveAgentAction,
    addProject,
    editProject,
    removeProject,
    shareProject,
  };
}
