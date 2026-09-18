import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

/**
 * Manual in-app do Portal Transforma+.
 * Material de usuário. O tutorial de modelagem continua em
 * docs/12-roadmap-e-evolucao/transformometro-app/TUTORIAL-USUARIO.md.
 */
export type UserManualLink = {
  label: string;
  path: string;
  requiresManage?: boolean;
};

export type UserManualSection = {
  id: string;
  title: string;
  paragraphs: readonly string[];
  links?: readonly UserManualLink[];
};

export function visibleManualLinks(
  links: readonly UserManualLink[] | undefined,
  canManage: boolean,
): UserManualLink[] {
  return (links ?? []).filter((link) => canManage || link.requiresManage !== true);
}

export const USER_MANUAL_CONTENT = {
  tocTitle: "Neste manual",
  tocAriaLabel: "Sumário do manual",
  sections: [
    {
      id: "portal",
      title: "O Portal Transforma+",
      paragraphs: [
        "O Portal Transforma+ acompanha processos, melhorias e resultados.",
        "A barra superior leva às áreas do portal. O botão Buscar, ou Ctrl+K, abre os mesmos caminhos em qualquer tela.",
        "A busca da página Início filtra os cards daquela tela. A busca da barra superior é o atalho do portal inteiro.",
      ],
    },
    {
      id: "home",
      title: "Início",
      paragraphs: [
        "O Início reúne os caminhos: Gestão, Processos, Registros, Administração e Ajuda.",
        "Administração só aparece para quem administra o portal.",
      ],
      links: [{ label: "Abrir Início", path: TRANSFORMOMETRO_ROUTES.home }],
    },
    {
      id: "overview",
      title: "Visão geral",
      paragraphs: [
        "A Visão geral mostra indicadores do programa de transformação.",
        "Competência, datas, unidade e departamento recortam o gráfico. Não mudam quem pode ver o portal.",
        "As visões são Consolidado, Unidade e Departamento.",
      ],
      links: [{ label: "Abrir Visão geral", path: TRANSFORMOMETRO_ROUTES.dashboard }],
    },
    {
      id: "processes",
      title: "Meus processos",
      paragraphs: [
        "Meus processos lista os processos disponíveis no portal.",
        "Abra um processo para ver melhorias, revisões, medição e diagramas.",
      ],
      links: [{ label: "Abrir Meus processos", path: TRANSFORMOMETRO_ROUTES.processes }],
    },
    {
      id: "minutes",
      title: "Atas",
      paragraphs: [
        "Atas reúne reuniões, registros e assinaturas.",
        "Assinar uma ata depende de ser signatário daquela ata.",
      ],
      links: [{ label: "Abrir Atas", path: TRANSFORMOMETRO_ROUTES.meetingMinutes }],
    },
    {
      id: "data",
      title: "Exportar / Importar",
      paragraphs: [
        "Exportar / Importar faz backup, transferência e restauração dos dados do portal.",
        "A importação pede prévia e confirmação antes de substituir dados.",
      ],
      links: [{ label: "Abrir Exportar / Importar", path: TRANSFORMOMETRO_ROUTES.data }],
    },
    {
      id: "administration",
      title: "Administração",
      paragraphs: [
        "A área Administração fica disponível para usuários responsáveis pela administração do Portal.",
        "Quem só usa o portal no dia a dia não vê essa área na barra nem na busca.",
        "Configurações fica dentro de Administração. Não é uma área da barra superior.",
      ],
      links: [
        {
          label: "Abrir Administração",
          path: TRANSFORMOMETRO_ROUTES.administration,
          requiresManage: true,
        },
      ],
    },
    {
      id: "settings",
      title: "Configurações",
      paragraphs: [
        "Unidades são as plantas ou sites usados nos processos e no filtro da Visão geral.",
        "Departamentos são as áreas ligadas às unidades.",
        "Recursos compartilhados são licenças e ferramentas do catálogo. Criar ou alterar o catálogo é administração. Ligar um recurso a uma revisão faz parte do uso normal do processo.",
      ],
      links: [
        { label: "Unidades", path: TRANSFORMOMETRO_ROUTES.settingsUnits, requiresManage: true },
        { label: "Departamentos", path: TRANSFORMOMETRO_ROUTES.settingsDepartments, requiresManage: true },
        {
          label: "Recursos compartilhados",
          path: TRANSFORMOMETRO_ROUTES.settingsSharedResources,
          requiresManage: true,
        },
      ],
    },
    {
      id: "navigate",
      title: "Como navegar",
      paragraphs: [
        "Use a barra superior para Início, Visão geral, Meus processos, Administração e Ajuda.",
        "Use Buscar ou Ctrl+K para achar um caminho e Enter para abrir.",
        "Escape fecha a busca.",
      ],
    },
  ] satisfies readonly UserManualSection[],
} as const;
