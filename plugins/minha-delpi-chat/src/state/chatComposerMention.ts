import { MAX_COMPOSER_AGENTS, MAX_COMPOSER_PROJECTS, normalizeContextIdList } from "./chatComposerContext";

export type ComposerMentionKind = "agent" | "project";

export type ComposerMentionCandidate = {
  kind: ComposerMentionKind;
  id: string;
  name: string;
};

export type ActiveComposerMention = {
  start: number;
  query: string;
};

const MENTION_TOKEN_PATTERN = /@\[([^\]]+)\]/g;

function normalizeName(value: string): string {
  return String(value ?? "").trim().toLocaleLowerCase("pt-BR");
}

export function listComposerMentionCandidates(input: {
  agents?: ReadonlyArray<{ id: string; name: string }>;
  projects?: ReadonlyArray<{ id: string; name: string }>;
}): ComposerMentionCandidate[] {
  const candidates: ComposerMentionCandidate[] = [];

  for (const agent of input.agents ?? []) {
    const name = String(agent.name ?? "").trim();

    if (!name) {
      continue;
    }

    candidates.push({ kind: "agent", id: agent.id, name });
  }

  for (const project of input.projects ?? []) {
    const name = String(project.name ?? "").trim();

    if (!name) {
      continue;
    }

    candidates.push({ kind: "project", id: project.id, name });
  }

  return candidates.sort((left, right) => right.name.length - left.name.length);
}

/** Detecta menção ativa imediatamente antes do cursor (`@query` ou `@[query`). */
export function detectActiveComposerMention(
  value: string,
  cursor: number,
): ActiveComposerMention | null {
  const before = value.slice(0, Math.max(0, cursor));
  const bracketMatch = before.match(/@\[([^\]]*)$/);

  if (bracketMatch && bracketMatch.index !== undefined) {
    return {
      start: bracketMatch.index,
      query: bracketMatch[1] ?? "",
    };
  }

  const plainMatch = before.match(/@([^\s@[\]]*)$/);

  if (!plainMatch || plainMatch.index === undefined) {
    return null;
  }

  return {
    start: plainMatch.index,
    query: plainMatch[1] ?? "",
  };
}

export function filterComposerMentionCandidates(
  candidates: readonly ComposerMentionCandidate[],
  query: string,
  limits?: {
    selectedAgentIds?: readonly string[];
    selectedProjectIds?: readonly string[];
  },
): ComposerMentionCandidate[] {
  const normalizedQuery = normalizeName(query);
  const selectedAgents = new Set(normalizeContextIdList(limits?.selectedAgentIds));
  const selectedProjects = new Set(normalizeContextIdList(limits?.selectedProjectIds));

  return candidates.filter((candidate) => {
    const normalizedName = normalizeName(candidate.name);

    if (normalizedQuery && !normalizedName.includes(normalizedQuery)) {
      return false;
    }

    if (candidate.kind === "agent") {
      return selectedAgents.size < MAX_COMPOSER_AGENTS || selectedAgents.has(candidate.id);
    }

    return selectedProjects.size < MAX_COMPOSER_PROJECTS || selectedProjects.has(candidate.id);
  });
}

export function formatComposerMentionToken(name: string): string {
  return `@[${String(name).trim()}] `;
}

/** Remove a query `@…` ativa sem inserir token — o contexto fica nos badges do composer. */
export function clearComposerMentionQuery(input: {
  value: string;
  cursor: number;
  mentionStart: number;
}): { value: string; cursor: number } {
  const before = input.value.slice(0, input.mentionStart);
  const after = input.value.slice(input.cursor);
  const value = `${before}${after}`;

  return {
    value,
    cursor: before.length,
  };
}

export function applyComposerMentionSelection(input: {
  value: string;
  cursor: number;
  mentionStart: number;
  candidate: ComposerMentionCandidate;
}): { value: string; cursor: number } {
  return clearComposerMentionQuery({
    value: input.value,
    cursor: input.cursor,
    mentionStart: input.mentionStart,
  });
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Remove tokens `@[Nome]` legados do rascunho (badges substituem o texto inline). */
export function stripComposerMentionTokens(value: string): string {
  return value.replace(MENTION_TOKEN_PATTERN, "");
}

export function removeComposerMentionTokenForName(value: string, name: string): string {
  const trimmed = String(name ?? "").trim();

  if (!trimmed) {
    return value;
  }

  const pattern = new RegExp(`@\\[${escapeRegExp(trimmed)}\\]\\s*`, "g");

  return value.replace(pattern, "");
}

function resolveCandidateByName(
  candidates: readonly ComposerMentionCandidate[],
  label: string,
): ComposerMentionCandidate | null {
  const normalizedLabel = normalizeName(label);

  if (!normalizedLabel) {
    return null;
  }

  return (
    candidates.find((candidate) => normalizeName(candidate.name) === normalizedLabel) ?? null
  );
}

/** Extrai agentes/projetos citados com `@[Nome]` no texto da pergunta. */
export function resolveMentionedContextIds(
  text: string,
  candidates: readonly ComposerMentionCandidate[],
): { agentIds: string[]; projectIds: string[] } {
  const agentIds: string[] = [];
  const projectIds: string[] = [];
  const seenAgents = new Set<string>();
  const seenProjects = new Set<string>();

  for (const match of text.matchAll(MENTION_TOKEN_PATTERN)) {
    const label = match[1];

    if (!label) {
      continue;
    }

    const candidate = resolveCandidateByName(candidates, label);

    if (!candidate) {
      continue;
    }

    if (candidate.kind === "agent") {
      if (!seenAgents.has(candidate.id) && agentIds.length < MAX_COMPOSER_AGENTS) {
        seenAgents.add(candidate.id);
        agentIds.push(candidate.id);
      }

      continue;
    }

    if (!seenProjects.has(candidate.id) && projectIds.length < MAX_COMPOSER_PROJECTS) {
      seenProjects.add(candidate.id);
      projectIds.push(candidate.id);
    }
  }

  return { agentIds, projectIds };
}

export function mergeMentionedContextIds(input: {
  mentionAgentIds?: readonly string[];
  mentionProjectIds?: readonly string[];
  overlayAgentIds?: readonly string[];
  overlayProjectIds?: readonly string[];
}): { agentIds: string[]; projectIds: string[] } {
  const agentIds: string[] = [];
  const projectIds: string[] = [];

  for (const id of [
    ...(input.overlayAgentIds ?? []),
    ...(input.mentionAgentIds ?? []),
  ]) {
    if (!agentIds.includes(id) && agentIds.length < MAX_COMPOSER_AGENTS) {
      agentIds.push(id);
    }
  }

  for (const id of [
    ...(input.overlayProjectIds ?? []),
    ...(input.mentionProjectIds ?? []),
  ]) {
    if (!projectIds.includes(id) && projectIds.length < MAX_COMPOSER_PROJECTS) {
      projectIds.push(id);
    }
  }

  return { agentIds, projectIds };
}
