import { useCallback, useEffect, useState } from "react";

import {
  createChatProject,
  deleteChatProject,
  listChatAgents,
  listChatProjects,
  updateChatProject,
} from "../../data/api/chatApi";
import type {
  ChatAgent,
  ChatProject,
  CreateChatProjectPayload,
  UpdateChatProjectPayload,
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
    loadAgents,
    loadProjects,
    addProject,
    editProject,
    removeProject,
  };
}
