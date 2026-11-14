import type { PageHeroHighlight } from "@delpi/plugin-ui/index";

import type {
  HomeItem,
  HomeResponse,
  HomeSection,
  HomeSectionKey,
  HomeStatus,
  SectionReason,
} from "../../types/home";

/** Mapeamento puro seção→apresentação. O kit não conhece o domínio e o
 * MFE não recomputa autorização: `forbidden`/`unavailable`/`not_implemented`
 * vêm prontos da engineering-api e são traduzidos honestamente — nunca
 * como "zero itens" nem como erro genérico de conexão. */

export type SectionViewKind =
  | "items"
  | "empty"
  | "unavailable"
  | "forbidden"
  | "not_implemented";

export type SectionView = {
  kind: SectionViewKind;
  items: HomeItem[];
  message: string;
  totalLabel?: string;
};

const SOURCE_LABELS: Record<string, string> = {
  "api-delpi": "API DELPI",
  "requests-api": "Solicitações",
};

const REASON_LABELS: Record<SectionReason, string> = {
  timeout: "a fonte não respondeu a tempo",
  transport_error: "falha de comunicação com a fonte",
  upstream_error: "a fonte retornou erro",
  contract_error: "a resposta da fonte veio fora do formato esperado",
  no_official_source: "ainda não existe fonte oficial para esta informação",
};

export function sourceLabel(system: string | undefined): string {
  if (!system) return "—";
  return SOURCE_LABELS[system] ?? system;
}

export function buildSectionView(section: HomeSection): SectionView {
  switch (section.status) {
    case "available":
      return {
        kind: "items",
        items: section.items,
        message: "",
        totalLabel:
          typeof section.total === "number" && section.total > section.items.length
            ? `${section.items.length} de ${section.total}`
            : undefined,
      };
    case "empty":
      return {
        kind: "empty",
        items: [],
        message: "Nenhum item no momento.",
      };
    case "forbidden":
      return {
        kind: "forbidden",
        items: [],
        message:
          section.message ||
          "Você não tem acesso a esta informação. Se precisar, solicite a permissão ao administrador.",
      };
    case "not_implemented":
      return {
        kind: "not_implemented",
        items: [],
        message:
          section.message ||
          "Esta capacidade está prevista no Portal Engenharia e será liberada em uma próxima etapa.",
      };
    case "unavailable":
    default: {
      const reason = section.reason ? REASON_LABELS[section.reason] : null;
      return {
        kind: "unavailable",
        items: [],
        message:
          section.message ||
          `Não foi possível carregar agora${reason ? ` — ${reason}` : ""}.`,
      };
    }
  }
}

/** Status agregado → apresentação de banner parcial (só quando misto). */
export function partialBannerMessage(status: HomeStatus): string | null {
  if (status !== "partial") return null;
  return "Algumas fontes não responderam — exibindo apenas o que está autorizado e disponível.";
}

export type HomeSectionSpec = {
  key: HomeSectionKey;
  title: string;
  subtitle: string;
};

/** Cabeçalhos fixos — mesma ordem das seções do contrato F2a. */
export const WORK_SECTIONS: readonly HomeSectionSpec[] = [
  {
    key: "attention",
    title: "Precisa de atenção",
    subtitle: "Itens que pedem ação da Engenharia",
  },
  {
    key: "tasks",
    title: "Minhas tarefas",
    subtitle: "Fila de trabalho atribuída a você",
  },
  {
    key: "requests",
    title: "Minhas solicitações",
    subtitle: "Pedidos abertos por você",
  },
  {
    key: "lmps",
    title: "LMPs",
    subtitle: "Licitações e medições em acompanhamento",
  },
];

export const CONTINUITY_SECTIONS: readonly HomeSectionSpec[] = [
  {
    key: "activity",
    title: "Atividade recente",
    subtitle: "Últimas movimentações do seu trabalho",
  },
  {
    key: "collaboration",
    title: "Colaboração",
    subtitle: "Espaços de trabalho compartilhados",
  },
];

/* ---- F3.R1 — composição de portal (hero / eventos) --------------- */

/* ---- Indicador compacto de pendências PRC (PO §38) -------------
 * Substitui a listagem extensa de eventos: um único indicador com o
 * total oficial da seção `tasks` (casos acionáveis, filtrados no
 * backend antes de COUNT/LIMIT) e ação para a fila PRC pré-filtrada.
 * `forbidden` nunca renderiza o card (não expõe acesso sem permissão);
 * `unavailable` nunca mostra zero — só estado honesto. */

export type PendingQueueIndicator =
  | { kind: "ready"; total: number }
  | { kind: "empty" }
  | { kind: "unavailable"; message: string }
  | { kind: "hidden" };

export function buildPendingQueueIndicator(
  sections: Pick<HomeResponse["sections"], "tasks">,
): PendingQueueIndicator {
  const tasks = sections.tasks;
  if (tasks.status === "forbidden") return { kind: "hidden" };
  if (tasks.status === "unavailable") {
    return {
      kind: "unavailable",
      message:
        "A fila de solicitações está indisponível no momento. " +
        "Tente novamente em instantes.",
    };
  }
  if (tasks.status !== "available") return { kind: "hidden" };
  const total =
    typeof tasks.total === "number" ? tasks.total : tasks.items.length;
  return total === 0 ? { kind: "empty" } : { kind: "ready", total };
}

const HIGHLIGHT_SPECS: readonly {
  key: HomeSectionKey;
  label: string;
}[] = [
  /* tasks sai do hero: o indicador compacto de pendências é a única
     representação acionável das tarefas PRC (PO §38). */
  { key: "requests", label: "Minhas solicitações" },
  { key: "lmps", label: "LMPs em acompanhamento" },
];

/** Tiles do Hero — somente fontes autorizadas disponíveis. Fonte
 * indisponível/negada NUNCA renderiza 0. */
export function buildHeroHighlights(
  sections: HomeResponse["sections"],
  loading: boolean,
): PageHeroHighlight[] {
  const highlights: PageHeroHighlight[] = [];
  for (const spec of HIGHLIGHT_SPECS) {
    const section = sections[spec.key];
    if (loading && section.status === "unavailable") {
      highlights.push({
        id: spec.key,
        label: spec.label,
        value: "…",
        loading: true,
      });
      continue;
    }
    if (section.status !== "available" && section.status !== "empty") {
      continue;
    }
    const total =
      typeof section.total === "number"
        ? section.total
        : section.items.length;
    highlights.push({
      id: spec.key,
      label: spec.label,
      value: String(total),
      description: section.status === "empty" ? "Nada pendente" : undefined,
    });
  }
  return highlights;
}

/** Resumo por seção para a página Visão geral — espelha o estado
 * oficial sem recomputar autorização. */
export type OverviewSourceRow = {
  key: HomeSectionKey;
  title: string;
  statusLabel: string;
  detail: string;
  count: number | null;
};

export function buildOverviewRows(
  home: HomeResponse,
): OverviewSourceRow[] {
  const specs = [...WORK_SECTIONS, ...CONTINUITY_SECTIONS];
  return specs.map((spec) => {
    const section = home.sections[spec.key];
    const view = buildSectionView(section);
    const statusLabel =
      section.status === "available"
        ? "Disponível"
        : section.status === "empty"
          ? "Sem itens"
          : section.status === "forbidden"
            ? "Acesso negado"
            : section.status === "not_implemented"
              ? "Capacidade futura"
              : "Indisponível";
    const count =
      section.status === "available" || section.status === "empty"
        ? typeof section.total === "number"
          ? section.total
          : section.items.length
        : null;
    return {
      key: spec.key,
      title: spec.title,
      statusLabel,
      detail: view.kind === "items" ? "" : view.message,
      count,
    };
  });
}
