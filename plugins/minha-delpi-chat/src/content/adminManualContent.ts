/**
 * Manual curto do admin por persona (feature-help-sync).
 * Paths de navegação em EN; copy PT.
 */

import type { AdminNavState } from "../navigation/adminNavigation";

export type AdminManualPersonaId = "curator" | "platform" | "auditor";

export type AdminManualLink = {
  label: string;
  nav: AdminNavState;
};

export type AdminManualPersona = {
  id: AdminManualPersonaId;
  title: string;
  summary: string;
  steps: string[];
  links: AdminManualLink[];
};

export const ADMIN_MANUAL_PERSONAS: readonly AdminManualPersona[] = [
  {
    id: "curator",
    title: "Curador de conhecimento",
    summary:
      "Cuida da base global, diretrizes, comportamentos e da fila de aprendizagem.",
    steps: [
      "Revise Documentos e reindexe quando houver fonte nova.",
      "Publique diretrizes só após rascunho revisado.",
      "Trate candidatos em Aprendizagem; use Melhoria contínua como atalho HITL.",
    ],
    links: [
      { label: "Documentos", nav: { section: "knowledge", subTab: "documents" } },
      { label: "Diretrizes", nav: { section: "knowledge", subTab: "guidelines" } },
      { label: "Comportamentos", nav: { section: "knowledge", subTab: "behaviors" } },
      {
        label: "Candidatos",
        nav: { section: "knowledge", subTab: "learning", page: "candidates" },
      },
      { label: "Melhoria contínua", nav: { section: "quality", subTab: "improve" } },
    ],
  },
  {
    id: "platform",
    title: "Operador de plataforma",
    summary:
      "Ajusta inteligência do chat, saúde de tools e especialização via Studio.",
    steps: [
      "Escolha um preset em Inteligência (Rápido / Equilibrado / Máxima) antes de knobs.",
      "Confira Ferramentas e catálogo OpenAPI; testes de action ficam no Studio.",
      "Especialização RAG no catálogo; ficha completa do agente no Studio.",
    ],
    links: [
      { label: "Inteligência", nav: { section: "platform", subTab: "intelligence" } },
      { label: "Ferramentas", nav: { section: "platform", subTab: "tools" } },
      { label: "Especialização", nav: { section: "agents", subTab: "specialization" } },
      { label: "Métricas", nav: { section: "quality", subTab: "metrics" } },
    ],
  },
  {
    id: "auditor",
    title: "Auditor",
    summary: "Investiga eventos, segurança de entrada e qualidade das respostas.",
    steps: [
      "Use Auditoria com filtros na URL (traceId, datas, action).",
      "Do diagnóstico da bolha, abra a auditoria quando houver traceId.",
      "Cruze Segurança com Avaliações e Feedback nas métricas.",
    ],
    links: [
      { label: "Auditoria", nav: { section: "governance", subTab: "audit" } },
      { label: "Segurança", nav: { section: "governance", subTab: "security" } },
      { label: "Avaliações", nav: { section: "quality", subTab: "evaluations" } },
      {
        label: "Feedback",
        nav: { section: "quality", subTab: "metrics", page: "feedback" },
      },
    ],
  },
] as const;

export function getAdminManualPersona(
  id: AdminManualPersonaId,
): AdminManualPersona | undefined {
  return ADMIN_MANUAL_PERSONAS.find((persona) => persona.id === id);
}
