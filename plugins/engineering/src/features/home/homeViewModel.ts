import type { TaskItemPresentation } from "@delpi/plugin-ui/index";

import type {
  HomeItem,
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
  items: TaskItemPresentation[];
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

function toPresentation(item: HomeItem): TaskItemPresentation {
  const hasRoute = typeof item.href === "string" && item.href.startsWith("/apps/");
  return {
    id: item.id,
    title: item.title,
    sourceLabel: sourceLabel(item.source),
    statusLabel: item.status_label || item.status || "—",
    dueDateLabel: item.date || undefined,
    route: hasRoute ? item.href : null,
    actions: { canOpen: hasRoute },
  };
}

export function buildSectionView(section: HomeSection): SectionView {
  switch (section.status) {
    case "available":
      return {
        kind: "items",
        items: section.items.map(toPresentation),
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
