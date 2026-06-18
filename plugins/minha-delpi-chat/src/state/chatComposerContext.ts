import type { ComposerContextBarItem } from "./chatAgentActivation";

export const MAX_COMPOSER_AGENTS = 2;
export const MAX_COMPOSER_PROJECTS = 3;

function normalizeId(value: string | null | undefined): string | null {
  const normalized = String(value ?? "").trim();
  return normalized || null;
}

export function normalizeContextIdList(
  values: readonly (string | null | undefined)[] | null | undefined,
): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const value of values ?? []) {
    const normalized = normalizeId(value);

    if (!normalized || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    result.push(normalized);
  }

  return result;
}

export function toggleContextId(
  current: readonly string[],
  id: string,
  maxItems: number,
): string[] {
  const normalized = normalizeId(id);

  if (!normalized) {
    return [...current];
  }

  const index = current.indexOf(normalized);

  if (index >= 0) {
    return current.filter((item) => item !== normalized);
  }

  if (current.length >= maxItems) {
    return [...current];
  }

  return [...current, normalized];
}

export function removeContextId(current: readonly string[], id: string): string[] {
  const normalized = normalizeId(id);

  if (!normalized) {
    return [...current];
  }

  return current.filter((item) => item !== normalized);
}

/** IDs efetivos do turno — página, sessão persistida e overlays do composer. */
export function resolveEffectiveAgentIds(input: {
  pageAgentId?: string | null;
  sessionAgentId?: string | null;
  contextAgentIds?: readonly string[];
  excludedAgentIds?: readonly string[];
}): string[] {
  const pageAgentId = normalizeId(input.pageAgentId);
  const sessionAgentId = normalizeId(input.sessionAgentId);
  const excluded = new Set(normalizeContextIdList(input.excludedAgentIds));
  const overlay = normalizeContextIdList(input.contextAgentIds);
  const combined: string[] = [];

  if (pageAgentId && !excluded.has(pageAgentId)) {
    combined.push(pageAgentId);
  } else if (sessionAgentId && !excluded.has(sessionAgentId)) {
    combined.push(sessionAgentId);
  }

  for (const id of overlay) {
    if (!excluded.has(id) && !combined.includes(id)) {
      combined.push(id);
    }
  }

  return combined.slice(0, MAX_COMPOSER_AGENTS);
}

export function resolveEffectiveProjectIds(input: {
  pageProjectId?: string | null;
  sessionProjectId?: string | null;
  contextProjectIds?: readonly string[];
  excludedProjectIds?: readonly string[];
}): string[] {
  const pageProjectId = normalizeId(input.pageProjectId);
  const sessionProjectId = normalizeId(input.sessionProjectId);
  const excluded = new Set(normalizeContextIdList(input.excludedProjectIds));
  const overlay = normalizeContextIdList(input.contextProjectIds);
  const combined: string[] = [];

  if (pageProjectId && !excluded.has(pageProjectId)) {
    combined.push(pageProjectId);
  } else if (sessionProjectId && !excluded.has(sessionProjectId)) {
    combined.push(sessionProjectId);
  }

  for (const id of overlay) {
    if (!excluded.has(id) && !combined.includes(id)) {
      combined.push(id);
    }
  }

  return combined.slice(0, MAX_COMPOSER_PROJECTS);
}

/** Payload canônico do turno — primário + listas + modo explícito para a API. */
export function buildComposerTurnPayload(input: {
  effectiveAgentIds: readonly string[];
  effectiveProjectIds: readonly string[];
}): {
  agentId: string | null;
  agentIds: string[];
  projectId: string | null;
  projectIds: string[];
  chatMode: "common" | "agent";
} {
  const agentIds = normalizeContextIdList(input.effectiveAgentIds);
  const projectIds = normalizeContextIdList(input.effectiveProjectIds);
  const hasAgent = agentIds.length > 0;

  return {
    agentId: agentIds[0] ?? null,
    agentIds,
    projectId: projectIds[0] ?? null,
    projectIds,
    chatMode: hasAgent ? "agent" : "common",
  };
}

export function resolvePrimaryContextId(ids: readonly string[]): string | null {
  return ids[0] ?? null;
}

export function resolveSupplementalContextIds(ids: readonly string[]): string[] {
  return ids.slice(1);
}

export function resolveComposerContextBarFromLists(input: {
  pageAgentId?: string | null;
  pageProjectId?: string | null;
  sessionAgentId?: string | null;
  sessionProjectId?: string | null;
  contextAgentIds?: readonly string[];
  contextProjectIds?: readonly string[];
  excludedAgentIds?: readonly string[];
  excludedProjectIds?: readonly string[];
}): ComposerContextBarItem[] {
  const pageAgentId = normalizeId(input.pageAgentId);
  const pageProjectId = normalizeId(input.pageProjectId);
  const agentIds = resolveEffectiveAgentIds({
    pageAgentId,
    sessionAgentId: input.sessionAgentId,
    contextAgentIds: input.contextAgentIds,
    excludedAgentIds: input.excludedAgentIds,
  });
  const projectIds = resolveEffectiveProjectIds({
    pageProjectId,
    sessionProjectId: input.sessionProjectId,
    contextProjectIds: input.contextProjectIds,
    excludedProjectIds: input.excludedProjectIds,
  });
  const items: ComposerContextBarItem[] = [];

  for (const id of agentIds) {
    if (!pageAgentId || id !== pageAgentId) {
      items.push({ kind: "agent", id });
    }
  }

  for (const id of projectIds) {
    if (!pageProjectId || id !== pageProjectId) {
      items.push({ kind: "project", id });
    }
  }

  return items;
}

export type UserTurnContextChip = {
  kind: "agent" | "project";
  id: string;
  name: string;
  icon?: string | null;
};

type TurnContextEntity = {
  id?: string | null;
  name?: string | null;
  icon?: string | null;
};

export function buildTurnContextMetadata(input: {
  agents?: readonly TurnContextEntity[];
  projects?: readonly TurnContextEntity[];
}): Record<string, unknown> {
  const agents = (input.agents ?? [])
    .map((item) => ({
      id: normalizeId(item.id),
      name: String(item.name ?? "").trim(),
      icon: String(item.icon ?? "").trim() || null,
    }))
    .filter((item): item is { id: string; name: string; icon: string | null } =>
      Boolean(item.id && item.name),
    );
  const projects = (input.projects ?? [])
    .map((item) => ({
      id: normalizeId(item.id),
      name: String(item.name ?? "").trim(),
      icon: String(item.icon ?? "").trim() || null,
    }))
    .filter((item): item is { id: string; name: string; icon: string | null } =>
      Boolean(item.id && item.name),
    );

  const metadata: Record<string, unknown> = {};

  if (agents[0]) {
    metadata.agentId = agents[0].id;
    metadata.agent = {
      id: agents[0].id,
      name: agents[0].name,
      ...(agents[0].icon ? { icon: agents[0].icon } : {}),
    };
  }

  if (agents.length > 1) {
    metadata.supplementalAgents = agents.slice(1).map((item) => ({
      id: item.id,
      name: item.name,
      ...(item.icon ? { icon: item.icon } : {}),
    }));
  }

  if (projects[0]) {
    metadata.project = {
      id: projects[0].id,
      name: projects[0].name,
      ...(projects[0].icon ? { icon: projects[0].icon } : {}),
    };
  }

  if (projects.length > 1) {
    metadata.supplementalProjects = projects.slice(1).map((item) => ({
      id: item.id,
      name: item.name,
      ...(item.icon ? { icon: item.icon } : {}),
    }));
  }

  return metadata;
}

export function resolveUserMessageTurnContextChips(
  metadata: Record<string, unknown> | null | undefined,
): UserTurnContextChip[] {
  if (!metadata || typeof metadata !== "object") {
    return [];
  }

  const chips: UserTurnContextChip[] = [];

  const pushEntity = (
    kind: UserTurnContextChip["kind"],
    entity: TurnContextEntity | null | undefined,
  ) => {
    const id = normalizeId(entity?.id);
    const name = String(entity?.name ?? "").trim();

    if (!id || !name) {
      return;
    }

    if (chips.some((chip) => chip.kind === kind && chip.id === id)) {
      return;
    }

    chips.push({
      kind,
      id,
      name,
      ...(String(entity?.icon ?? "").trim() ? { icon: String(entity?.icon ?? "").trim() } : {}),
    });
  };

  pushEntity("agent", metadata.agent as TurnContextEntity | undefined);

  const supplementalAgents = metadata.supplementalAgents;

  if (Array.isArray(supplementalAgents)) {
    for (const item of supplementalAgents) {
      pushEntity("agent", item as TurnContextEntity);
    }
  }

  pushEntity("project", metadata.project as TurnContextEntity | undefined);

  const supplementalProjects = metadata.supplementalProjects;

  if (Array.isArray(supplementalProjects)) {
    for (const item of supplementalProjects) {
      pushEntity("project", item as TurnContextEntity);
    }
  }

  return chips;
}

export function formatComposerPlaceholderParts(input: {
  projectNames?: readonly string[];
  agentNames?: readonly string[];
}): string | null {
  const projects = (input.projectNames ?? []).map((name) => String(name).trim()).filter(Boolean);
  const agents = (input.agentNames ?? []).map((name) => String(name).trim()).filter(Boolean);

  if (projects.length === 0 && agents.length === 0) {
    return null;
  }

  const projectLabel =
    projects.length === 1
      ? projects[0]
      : projects.length > 1
        ? `${projects.length} projetos`
        : null;

  const agentLabel =
    agents.length === 1
      ? agents[0]
      : agents.length > 1
        ? `${agents.length} agentes`
        : null;

  if (projectLabel && agentLabel) {
    return `Pergunte sobre ${projectLabel} com ${agentLabel}`;
  }

  if (projectLabel) {
    return `Pergunte sobre ${projectLabel} ou envie um arquivo`;
  }

  if (agentLabel) {
    return `Código, descrição ou pergunta — ${agentLabel} consulta dados autorizados`;
  }

  return null;
}
