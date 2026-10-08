import { describe, expect, it } from "vitest";

import type { ProductGuideHelpTopic } from "../api/tvDashboardApi";
import {
  HELP_AUTH_NOTE,
  HELP_DRIFT_NOTE,
  HELP_LOADING_NOTE,
  HELP_SECTION_TOPICS,
  HELP_UNAVAILABLE_NOTE,
  indexTopicsById,
  mergeManualWithGuides,
  missingConfiguredTopics,
  relatedSectionsFor,
  sectionIdForTopic,
} from "./helpGuideContent";
import { USER_MANUAL_CONTENT } from "./userManualContent";

/** Fixture Wave-1: exatamente os 11 tópicos aprovados no diagnóstico. */
const WAVE1_TOPICS: ProductGuideHelpTopic[] = [
  { id: "tv_dashboard_overview", title: "Visão geral", summary: "O que são Painéis TV." },
  { id: "playlist", title: "Playlist", summary: "Programação de telas." },
  { id: "slide", title: "Slide", summary: "Tela individual." },
  { id: "block_types", title: "Blocos", summary: "Famílias de elementos." },
  { id: "data_sources", title: "Fontes", summary: "Origem dos dados." },
  { id: "data_models", title: "Modelos", summary: "Transformação de dados." },
  { id: "data_bindings", title: "Ligações", summary: "Vínculo visual↔dado." },
  {
    id: "filters_and_layering",
    title: "Filtros",
    summary: "Camadas de filtro.",
    related_topics: ["data_route_discovery", "data_sources"],
  },
  { id: "display_formats", title: "Formatos", summary: "Cobertura parcial de formatação." },
  { id: "data_route_discovery", title: "Rotas", summary: "Descoberta de rotas de dados." },
  {
    id: "visual_verification",
    title: "Verificação",
    summary: "Escala de evidência visual.",
    how_to_use: ["Editor aberto captura o palco."],
    quality_rules: ["Esquemático não é pixels."],
  },
];

const ALL_TOPIC_IDS = WAVE1_TOPICS.map((t) => t.id);

describe("HELP_SECTION_TOPICS — mapa seção→tópico", () => {
  it("cobre exatamente os 11 tópicos Wave-1, 1:1, sem tópico desconhecido", () => {
    const configured = Object.values(HELP_SECTION_TOPICS).flat();
    expect([...configured].sort()).toEqual([...ALL_TOPIC_IDS].sort());
  });

  it("todas as seções locais com map resolvem no índice do registry", () => {
    const byId = indexTopicsById(WAVE1_TOPICS);
    expect(missingConfiguredTopics(byId)).toEqual([]);
  });

  it("detecta drift: tópico configurado ausente no índice", () => {
    const byId = indexTopicsById(WAVE1_TOPICS.filter((t) => t.id !== "display_formats"));
    expect(missingConfiguredTopics(byId)).toEqual(["display_formats"]);
  });

  it("sectionIdForTopic é o inverso do mapa", () => {
    for (const [sectionId, ids] of Object.entries(HELP_SECTION_TOPICS)) {
      for (const id of ids) expect(sectionIdForTopic(id)).toBe(sectionId);
    }
    expect(sectionIdForTopic("nonexistent")).toBeNull();
  });
});

describe("mergeManualWithGuides", () => {
  const sections = USER_MANUAL_CONTENT.sections;

  it("loading: nota explícita, semântica ainda não presente", () => {
    const merged = mergeManualWithGuides(sections, null, { loading: true });
    for (const s of merged) {
      expect(s.intro).toBe(HELP_LOADING_NOTE);
      // links locais permanecem mesmo no loading
      expect(s.links).toBeDefined();
    }
  });

  it("sem guia: nota de indisponibilidade, links locais intactos, sem prosa semântica", () => {
    const merged = mergeManualWithGuides(sections, null);
    for (const s of merged) {
      expect(s.intro).toBe(HELP_UNAVAILABLE_NOTE);
    }
    const playlist = merged.find((s) => s.id === "playlists")!;
    expect(playlist.links?.length).toBeGreaterThan(0);
    expect(playlist.bullets ?? []).toHaveLength(0);
  });

  it("nota customizada para auth (401/403)", () => {
    const merged = mergeManualWithGuides(sections, null, {
      unavailableNote: HELP_AUTH_NOTE,
    });
    expect(merged.every((s) => s.intro === HELP_AUTH_NOTE)).toBe(true);
  });

  it("sucesso: semântica do guide entra; bullets locais são anexados, não duplicados", () => {
    const merged = mergeManualWithGuides(sections, indexTopicsById(WAVE1_TOPICS));
    const visual = merged.find((s) => s.id === "visual-review")!;
    expect(visual.intro).toContain("Escala de evidência visual");
    expect(visual.bullets).toContain("Editor aberto captura o palco.");
    expect(visual.bullets).toContain("Esquemático não é pixels.");
    // conteúdo local: apenas links navegacionais, sem duplicar prosa do guide
    const sources = merged.find((s) => s.id === "data-sources")!;
    expect(sources.intro).toBe("Origem dos dados.");
    expect(sources.links?.some((l) => l.how.includes("Testar rota"))).toBe(true);
  });

  it("tópico ausente individual → nota de drift nessa seção apenas", () => {
    const byId = indexTopicsById(WAVE1_TOPICS.filter((t) => t.id !== "slide"));
    const merged = mergeManualWithGuides(sections, byId);
    expect(merged.find((s) => s.id === "slides")!.intro).toBe(HELP_DRIFT_NOTE);
    expect(merged.find((s) => s.id === "playlists")!.intro).toBe("Programação de telas.");
  });

  it("related_topics viram navegação para seções locais existentes", () => {
    const byId = indexTopicsById(WAVE1_TOPICS);
    const related = relatedSectionsFor("filters", byId);
    expect(related.map((r) => r.sectionId)).toEqual(["data-discovery", "data-sources"]);
    expect(relatedSectionsFor("filters", null)).toEqual([]);
  });
});
