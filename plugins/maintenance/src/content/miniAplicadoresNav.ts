import { MAINTENANCE_ROUTES } from "../constants/routes";

export type MiniAplicadoresNavTabId = "home" | "ferramentas" | "relatorio" | "configuracao";

export const MINI_APLICADORES_NAV_CONTENT = {
  ariaLabel: "Mini-aplicadores",
  home: {
    id: "home" as const,
    label: "Início",
  },
  ferramentas: {
    id: "ferramentas" as const,
    label: "Ferramentas",
    path: MAINTENANCE_ROUTES.miniAplicadores,
  },
  relatorio: {
    id: "relatorio" as const,
    label: "Relatório preventivo",
    path: MAINTENANCE_ROUTES.miniAplicadoresRelatorio,
  },
  configuracao: {
    id: "configuracao" as const,
    label: "Configuração",
    path: MAINTENANCE_ROUTES.miniAplicadoresConfiguracao,
  },
} as const;

export const SUBMODULE_BACK_NAV_CONTENT = {
  ariaLabel: "Voltar ao hub",
  home: {
    id: "home" as const,
    label: "Início",
  },
} as const;
