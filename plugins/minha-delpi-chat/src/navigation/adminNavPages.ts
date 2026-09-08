import type { AdminSubTab } from "./adminNavigation";

export type AdminNestedPage = {
  key: string;
  label: string;
  /** Slug canônico EN na URL. */
  slug: string;
  /** Slugs PT (e outros) ainda aceitos no parse. */
  aliases?: string[];
};

/** Sub-abas com páginas internas (3º nível na sidebar e na URL). */
export const ADMIN_NESTED_PAGES: Partial<Record<AdminSubTab, AdminNestedPage[]>> = {
  learning: [
    { key: "pipeline", label: "Pipeline", slug: "pipeline" },
    {
      key: "candidates",
      label: "Candidatos",
      slug: "candidates",
      aliases: ["candidatos"],
    },
    {
      key: "vocabulary",
      label: "Vocabulário",
      slug: "vocabulary",
      aliases: ["vocabulario"],
    },
    {
      key: "memory",
      label: "Memória",
      slug: "memory",
      aliases: ["memoria"],
    },
    {
      key: "evaluation",
      label: "Regressão",
      slug: "regression",
      aliases: ["regressao"],
    },
    {
      key: "finetuning",
      label: "Dataset de treino",
      slug: "fine-tuning",
      aliases: ["ajuste-fino"],
    },
  ],
  metrics: [
    {
      key: "overview",
      label: "Visão geral",
      slug: "overview",
      aliases: ["visao-geral"],
    },
    { key: "cost", label: "Custo e tokens", slug: "cost", aliases: ["custo"] },
    {
      key: "quality",
      label: "Qualidade unificada",
      slug: "quality",
      aliases: ["qualidade"],
    },
    {
      key: "intent",
      label: "Intenção",
      slug: "intent",
      aliases: ["intencao"],
    },
    {
      key: "interactivity",
      label: "Interatividade",
      slug: "interactivity",
      aliases: ["interatividade"],
    },
    { key: "feedback", label: "Feedback", slug: "feedback" },
    { key: "errors", label: "Erros", slug: "errors", aliases: ["erros"] },
    {
      key: "presentation",
      label: "Apresentação",
      slug: "presentation",
      aliases: ["apresentacao"],
    },
    {
      key: "memory",
      label: "Memória de sessão",
      slug: "session-memory",
      aliases: ["memoria-sessao"],
    },
    {
      key: "text",
      label: "Tarefas de texto",
      slug: "text-tasks",
      aliases: ["textos"],
    },
    { key: "web", label: "Pesquisa web", slug: "web" },
    {
      key: "typing",
      label: "Digitação",
      slug: "typing",
      aliases: ["digitacao"],
    },
    {
      key: "drawing",
      label: "Desenhos",
      slug: "drawings",
      aliases: ["desenhos"],
    },
    { key: "vision", label: "Visão", slug: "vision", aliases: ["visao"] },
    { key: "sql", label: "SQL avançado", slug: "sql" },
    {
      key: "operations",
      label: "Operações",
      slug: "operations",
      aliases: ["operacoes"],
    },
  ],
};

const SLUG_BY_SUB: Partial<Record<AdminSubTab, Record<string, string>>> = {};
const KEY_BY_SLUG: Partial<Record<AdminSubTab, Record<string, string>>> = {};

for (const [subTab, pages] of Object.entries(ADMIN_NESTED_PAGES) as Array<
  [AdminSubTab, AdminNestedPage[]]
>) {
  SLUG_BY_SUB[subTab] = Object.fromEntries(pages.map((page) => [page.key, page.slug]));
  const keyBySlug: Record<string, string> = {};
  for (const page of pages) {
    keyBySlug[page.slug] = page.key;
    for (const alias of page.aliases ?? []) {
      keyBySlug[alias] = page.key;
    }
  }
  KEY_BY_SLUG[subTab] = keyBySlug;
}

export function getNestedPages(subTab: AdminSubTab): AdminNestedPage[] {
  return ADMIN_NESTED_PAGES[subTab] ?? [];
}

export function hasNestedPages(subTab: AdminSubTab): boolean {
  return getNestedPages(subTab).length > 0;
}

export function defaultPageForSubTab(subTab: AdminSubTab): string | undefined {
  return getNestedPages(subTab)[0]?.key;
}

export function nestedPageSlug(subTab: AdminSubTab, pageKey: string): string | undefined {
  return SLUG_BY_SUB[subTab]?.[pageKey];
}

export function nestedPageFromSlug(subTab: AdminSubTab, slug: string): string | undefined {
  return KEY_BY_SLUG[subTab]?.[slug];
}

export function getNestedPageLabel(subTab: AdminSubTab, pageKey: string): string | undefined {
  return getNestedPages(subTab).find((page) => page.key === pageKey)?.label;
}
