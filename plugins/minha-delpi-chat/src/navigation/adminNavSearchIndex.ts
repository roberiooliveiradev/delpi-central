import type { AdminNavState } from "./adminNavigation";
import { getNestedPageLabel } from "./adminNavPages";

export type AdminNavContentEntry = {
  id: string;
  target: AdminNavState;
  /** Rótulo curto no resultado (ex.: bloco da página). */
  title: string;
  /** Breadcrumb exibido no hit. */
  path: string;
  /** Texto indexado: título, sinônimos, descrição, termos técnicos. */
  searchText: string;
};

function entry(
  id: string,
  target: AdminNavState,
  path: string,
  title: string,
  ...searchParts: string[]
): AdminNavContentEntry {
  return {
    id,
    target,
    path,
    title,
    searchText: [path, title, ...searchParts].join(" ").toLowerCase(),
  };
}

function learningPath(pageKey: string, pageLabel: string): string {
  return `Conhecimento · Aprendizagem · ${pageLabel || getNestedPageLabel("learning", pageKey) || pageKey}`;
}

/** Índice estático de conteúdo das telas do admin (busca na sidebar). */
export const ADMIN_NAV_CONTENT_INDEX: AdminNavContentEntry[] = [
  entry(
    "overview-panel",
    { section: "overview" },
    "Painel",
    "Como está o chat?",
    "resumo operacional 24 horas indicadores kpi sessões erros",
    "permissões rbac perfil admin operador auditor viewer superadmin",
    "navegação rápida documentos diretrizes simulação inteligência auditoria",
  ),
  entry(
    "overview-rbac",
    { section: "overview" },
    "Painel",
    "Permissões administrativas (RBAC)",
    "criar diretrizes publicar excluir documentos minha-delpi.chat.admin",
    "capacidades perfil papel role",
  ),
  entry(
    "knowledge-documents",
    { section: "knowledge", subTab: "documents" },
    "Conhecimento · Documentos",
    "Base de conhecimento",
    "ingestão upload arquivo texto título categoria namespace domínio tag",
    "reindexar desativar metadados testar rag chunk índice global",
    "curadoria anexo conversa não entra base",
  ),
  entry(
    "knowledge-guidelines",
    { section: "knowledge", subTab: "guidelines" },
    "Conhecimento · Diretrizes",
    "Diretrizes globais",
    "comportamento padrão versão publicar arquivar teste agente",
    "prompt sistema política",
  ),
  entry(
    "knowledge-behaviors",
    { section: "knowledge", subTab: "behaviors" },
    "Conhecimento · Comportamentos",
    "Comportamentos e skills",
    "skill habilidade prompt reutilizável catálogo agente ações apis",
  ),
  entry(
    "learning-main",
    { section: "knowledge", subTab: "learning", page: "candidates" },
    "Conhecimento · Aprendizagem",
    "Aprendizagem contínua",
    "candidatos vocabulário memória regressão ajuste fino typo glossário",
    "normalização termo definição promover aprovar rejeitar",
  ),
  entry(
    "learning-candidates",
    { section: "knowledge", subTab: "learning", page: "candidates" },
    learningPath("candidates", "Candidatos"),
    "Candidatos pendentes",
    "status pendente aprovado promovido rejeitado auto-aprovado",
    "revisar risco confiança termo definição normalização",
  ),
  entry(
    "learning-vocabulary",
    { section: "knowledge", subTab: "learning", page: "vocabulary" },
    learningPath("vocabulary", "Vocabulário"),
    "Vocabulário aprovado",
    "termo significado normalizado salvar aplicar glossário",
  ),
  entry(
    "learning-memory",
    { section: "knowledge", subTab: "learning", page: "memory" },
    learningPath("memory", "Memória"),
    "Memória de sessão",
    "preferência perfil correção esquecer ativa",
  ),
  entry(
    "learning-regression",
    { section: "knowledge", subTab: "learning", page: "evaluation" },
    learningPath("evaluation", "Regressão"),
    "Casos de regressão",
    "avaliação teste automático falha passou caso",
  ),
  entry(
    "learning-finetuning",
    { section: "knowledge", subTab: "learning", page: "finetuning" },
    learningPath("finetuning", "Ajuste fino"),
    "Ajuste fino e datasets",
    "dataset amostra curada exportar capturada aprovada rejeitada",
  ),
  entry(
    "agents-specialization",
    { section: "agents", subTab: "specialization" },
    "Agentes · Especialização",
    "Agentes especializados",
    "builder domínio rag diretrizes ferramentas provider action",
    "métricas sessões mensagens conversas gráfico volume",
  ),
  entry(
    "agents-simulation",
    { section: "agents", subTab: "simulation" },
    "Agentes · Simulação",
    "Simulação completa do agente",
    "validar prompt diretriz rag ferramentas publicar preview",
  ),
  entry(
    "quality-metrics",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Observabilidade do chat",
    "sessões mensagens latência tokens custo llm erro ferramenta",
    "rag assertividade falhas roteamento intenção janela 24h",
  ),
  entry(
    "quality-intent",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Roteamento de intenção",
    "operational_query clarification mixed_task small_talk sql_route",
    "ambíguo tarefa mista web",
  ),
  entry(
    "quality-interactivity",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Interatividade (chips)",
    "chip clique ctr mais opções impressão resposta",
  ),
  entry(
    "quality-feedback",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Feedback do usuário",
    "csat thumbs positivo negativo perda contexto motivo",
  ),
  entry(
    "quality-presentation",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Apresentação rica",
    "gráfico tabela lousa png exportar eixo formato",
  ),
  entry(
    "quality-sql",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "SQL avançado",
    "cte window dialecto chart bloqueio schema prefetch",
  ),
  entry(
    "quality-memory-metrics",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Contexto e assertividade",
    "memória sessão follow-up ambiguidade risco perda",
  ),
  entry(
    "quality-web",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Pesquisa web confiável",
    "query sanitizada bloqueio fonte oficial baixa confiança",
  ),
  entry(
    "quality-drawing",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Análise de desenhos DELPI",
    "pdf produto analyser snapshot desenho técnico",
  ),
  entry(
    "quality-vision",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Visão de documentos",
    "ocr legível motor estágio documento",
  ),
  entry(
    "quality-errors",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Erros e resultados vazios",
    "recuperável api plano auto-recuperação",
  ),
  entry(
    "quality-unified",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Visão unificada",
    "adoção usuários ativos eficiência segurança consolidado",
  ),
  entry(
    "quality-text",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Especialista em textos",
    "lousa versão anexo tarefa textual mista",
  ),
  entry(
    "quality-operations",
    { section: "quality", subTab: "metrics" },
    "Qualidade · Métricas",
    "Relatório semanal e pendências",
    "qualidade automático feedback recorrente",
  ),
  entry(
    "quality-evaluations",
    { section: "quality", subTab: "evaluations" },
    "Qualidade · Avaliações",
    "Avaliação de respostas",
    "feedback sugestão melhoria conhecimento diretriz llm score",
  ),
  entry(
    "platform-tools",
    { section: "platform", subTab: "tools" },
    "Plataforma · Ferramentas",
    "Ferramentas e integrações",
    "llm ollama saúde banco pgvector ações catálogo provider",
    "permissões gerencia tools agentes oficiais",
  ),
  entry(
    "platform-intelligence",
    { section: "platform", subTab: "intelligence" },
    "Plataforma · Inteligência",
    "Inteligência do chat",
    "políticas pipeline roteamento rag tools toggles análise modo",
    "métricas qualidade inteligência chat",
  ),
  entry(
    "governance-security",
    { section: "governance", subTab: "security" },
    "Governança · Segurança",
    "Segurança operacional",
    "injeção prompt sanitização bloqueio sinalização enforce limite caracteres",
    "testar mensagem risco flags auditoria",
  ),
  entry(
    "governance-audit",
    { section: "governance", subTab: "audit" },
    "Governança · Auditoria",
    "Eventos administrativos",
    "trilha rastreabilidade exportar filtro quando ação usuário",
  ),
];

const CONTENT_BY_TARGET_KEY = new Map<string, string[]>();

for (const item of ADMIN_NAV_CONTENT_INDEX) {
  const key = adminNavTargetKey(item.target);
  const existing = CONTENT_BY_TARGET_KEY.get(key) ?? [];
  existing.push(item.searchText);
  CONTENT_BY_TARGET_KEY.set(key, existing);
}

export function adminNavTargetKey(nav: AdminNavState): string {
  return `${nav.section}/${nav.subTab ?? ""}/${nav.page ?? ""}`;
}

/** Texto de conteúdo agregado para enriquecer busca nos nós da árvore. */
export function getContentSearchTextForTarget(target: AdminNavState): string {
  return (CONTENT_BY_TARGET_KEY.get(adminNavTargetKey(target)) ?? []).join(" ");
}
