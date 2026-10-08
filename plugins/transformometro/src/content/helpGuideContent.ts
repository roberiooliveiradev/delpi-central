import type { ProductGuideHelpTopic } from "../data/api/transformometroProductGuideApi";
import type { UserManualSection } from "./userManualContent";

/**
 * Help Convergence V1 — Portal Help renders product-guide semantics
 * from the shared registry (same authority as TÉO get_product_guide).
 *
 * MAPPED sections derive `intro`/`bullets` from the registry; `links`
 * (navigation: where/how/path) stay local — they are UI-specific.
 * Unmapped sections pass through untouched.
 */

export const HELP_SECTION_TOPICS: Record<string, readonly string[]> = {
  home: ["portal_overview"],
  overview: ["dashboard"],
  "targets-idd": ["dashboard"],
  processes: ["process", "instance", "revision"],
  "process-documentation": ["process_documents"],
  "revision-diagnostic": ["diagnostic"],
  "my-tasks": ["tasks"],
  interaction: ["interaction_room"],
  minutes: ["meeting_minutes"],
  data: ["data_transfer"],
  settings: ["branch", "department", "shared_resources"],
};

export const HELP_LOADING_NOTE = "Carregando conteúdo de ajuda…";

export const HELP_UNAVAILABLE_NOTE =
  "Conteúdo de ajuda indisponível no momento. A navegação abaixo continua válida.";

export function indexTopicsById(
  topics: readonly ProductGuideHelpTopic[],
): Map<string, ProductGuideHelpTopic> {
  return new Map(topics.map((topic) => [topic.id, topic]));
}

function bulletsForTopic(topic: ProductGuideHelpTopic): string[] {
  const semantic = [...(topic.how_to_use ?? []), ...(topic.quality_rules ?? [])];
  return semantic.length ? semantic : topic.summary ? [topic.summary] : [];
}

function deriveSectionContent(
  topicIds: readonly string[],
  topicsById: Map<string, ProductGuideHelpTopic>,
): Pick<UserManualSection, "intro" | "bullets"> {
  const topics = topicIds
    .map((id) => topicsById.get(id))
    .filter((t): t is ProductGuideHelpTopic => Boolean(t));
  if (!topics.length) {
    return { intro: HELP_UNAVAILABLE_NOTE, bullets: [] };
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
 * Merge local manual sections with registry help views. Mapped sections
 * get `intro` + leading `bullets` from the guide; any bullets left in
 * `userManualContent` for a mapped section are UI-specific (navigation,
 * screen behavior) and are appended after the derived ones. `links`
 * are never replaced. When the registry is unavailable, mapped sections
 * show the unavailable note instead of stale copy.
 */
export function mergeManualWithGuides(
  sections: readonly UserManualSection[],
  topicsById: Map<string, ProductGuideHelpTopic> | null,
  options?: { loading?: boolean },
): UserManualSection[] {
  return sections.map((section) => {
    const topicIds = HELP_SECTION_TOPICS[section.id];
    if (!topicIds) return section;
    if (options?.loading) {
      return { ...section, intro: HELP_LOADING_NOTE };
    }
    if (!topicsById) {
      return { ...section, intro: HELP_UNAVAILABLE_NOTE };
    }
    const derived = deriveSectionContent(topicIds, topicsById);
    return {
      ...section,
      intro: derived.intro,
      bullets: [...(derived.bullets ?? []), ...(section.bullets ?? [])],
    };
  });
}
