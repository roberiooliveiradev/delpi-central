import type { ProductGuideHelpTopic } from "../api/tvDashboardApi";
import type { UserManualSection } from "./userManualContent";

/**
 * Help Convergence — o manual central renderiza a semântica do
 * Product Guide V1 (mesma autoridade do VISTA `get_product_guide`).
 *
 * Seções mapeadas derivam `intro`/`bullets` do registry; `links` e
 * bullets locais (navegação/interação de tela) permanecem no MFE.
 * Seções não mapeadas passam intactas. Sem guia: nota explícita de
 * indisponibilidade — NUNCA prosa semântica duplicada de fallback.
 */

export const HELP_SECTION_TOPICS: Record<string, readonly string[]> = {
  overview: ["tv_dashboard_overview"],
  playlists: ["playlist"],
  slides: ["slide"],
  blocks: ["block_types"],
  "data-sources": ["data_sources"],
  "data-models": ["data_models"],
  bindings: ["data_bindings"],
  filters: ["filters_and_layering"],
  formats: ["display_formats"],
  "data-discovery": ["data_route_discovery"],
  "visual-review": ["visual_verification"],
};

export const HELP_LOADING_NOTE = "Carregando conteúdo de ajuda…";

export const HELP_UNAVAILABLE_NOTE =
  "Conteúdo de ajuda indisponível no momento. A navegação abaixo continua válida.";

export const HELP_DRIFT_NOTE =
  "Esta seção está temporariamente sem conteúdo de produto (configuração).";

export const HELP_AUTH_NOTE =
  "Conteúdo de ajuda indisponível: sessão expirada ou sem permissão. Faça login novamente.";

export const HELP_CONFIG_NOTE =
  "Conteúdo de ajuda indisponível: configuração de ajuda não encontrada.";

export function indexTopicsById(
  topics: readonly ProductGuideHelpTopic[],
): Map<string, ProductGuideHelpTopic> {
  return new Map(topics.map((topic) => [topic.id, topic]));
}

/** IDs configurados que não resolveram no payload — drift config/backend. */
export function missingConfiguredTopics(
  topicsById: ReadonlyMap<string, ProductGuideHelpTopic> | null,
): string[] {
  if (!topicsById) return [];
  const missing = new Set<string>();
  for (const topicIds of Object.values(HELP_SECTION_TOPICS)) {
    for (const id of topicIds) {
      if (!topicsById.has(id)) missing.add(id);
    }
  }
  return [...missing];
}

/** Seção local cuja map cobre o tópico — para navegação «Veja também». */
export function sectionIdForTopic(topicId: string): string | null {
  for (const [sectionId, topicIds] of Object.entries(HELP_SECTION_TOPICS)) {
    if (topicIds.includes(topicId)) return sectionId;
  }
  return null;
}

/** related_topics do tópico principal da seção → seções locais existentes. */
export function relatedSectionsFor(
  sectionId: string,
  topicsById: ReadonlyMap<string, ProductGuideHelpTopic> | null,
): readonly { sectionId: string; topicId: string }[] {
  if (!topicsById) return [];
  const topicIds = HELP_SECTION_TOPICS[sectionId] ?? [];
  const out: { sectionId: string; topicId: string }[] = [];
  for (const id of topicIds) {
    const topic = topicsById.get(id);
    for (const related of topic?.related_topics ?? []) {
      const target = sectionIdForTopic(related);
      if (target && target !== sectionId) {
        out.push({ sectionId: target, topicId: related });
      }
    }
  }
  return out;
}

function bulletsForTopic(topic: ProductGuideHelpTopic): string[] {
  return [...(topic.how_to_use ?? []), ...(topic.quality_rules ?? [])];
}

function deriveSectionContent(
  topicIds: readonly string[],
  topicsById: Map<string, ProductGuideHelpTopic>,
): Pick<UserManualSection, "intro" | "bullets"> {
  const topics = topicIds
    .map((id) => topicsById.get(id))
    .filter((t): t is ProductGuideHelpTopic => Boolean(t));
  if (!topics.length) {
    return { intro: HELP_DRIFT_NOTE, bullets: [] };
  }
  const [first] = topics;
  if (topics.length === 1) {
    return {
      intro: first.purpose ? `${first.summary} ${first.purpose}` : first.summary,
      bullets: bulletsForTopic(first),
    };
  }
  return {
    intro: first.summary,
    bullets: topics.map((t) => `${t.title}: ${t.summary}`),
  };
}

/**
 * Merge das seções locais com as projeções help-safe do registry.
 * Semântica derivada vem primeiro; bullets locais (UI) são anexados
 * depois; `links` nunca são substituídos. Indisponível → nota explícita.
 */
export function mergeManualWithGuides(
  sections: readonly UserManualSection[],
  topicsById: Map<string, ProductGuideHelpTopic> | null,
  options?: { loading?: boolean; unavailableNote?: string },
): UserManualSection[] {
  return sections.map((section) => {
    const topicIds = HELP_SECTION_TOPICS[section.id];
    if (!topicIds) return section;
    if (options?.loading) {
      return { ...section, intro: HELP_LOADING_NOTE };
    }
    if (!topicsById) {
      return { ...section, intro: options?.unavailableNote ?? HELP_UNAVAILABLE_NOTE };
    }
    const derived = deriveSectionContent(topicIds, topicsById);
    return {
      ...section,
      intro: derived.intro,
      bullets: [...(derived.bullets ?? []), ...(section.bullets ?? [])],
    };
  });
}
