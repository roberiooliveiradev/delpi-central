import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

/**
 * Manual in-app do Portal Transforma+.
 * Material de usuário. O tutorial de modelagem continua em
 * docs/12-roadmap-e-evolucao/transformometro-app/TUTORIAL-USUARIO.md.
 */
export type UserManualLink = {
  want: string;
  where: string;
  how: string;
  path?: string;
  requiresManage?: boolean;
};

export type UserManualConcept = {
  term: string;
  meaning: string;
};

export type UserManualSection = {
  id: string;
  title: string;
  intro?: string;
  bullets?: readonly string[];
  links?: readonly UserManualLink[];
};

export function visibleManualLinks(
  links: readonly UserManualLink[] | undefined,
  canManage: boolean,
): UserManualLink[] {
  return (links ?? []).filter((link) => canManage || link.requiresManage !== true);
}

export const USER_MANUAL_CONTENT = {
  backHome: "Voltar ao início",
  scopeNote:
    "Este manual descreve o que o Portal Transforma+ já oferece. Sala de interação e Minhas tarefas ainda não fazem parte deste portal.",
  tocTitle: "Neste manual",
  tocAriaLabel: "Sumário do manual",
  conceptsTitle: "Conceitos",
  concepts: [
    {
      term: "Início",
      meaning: "Hub dos caminhos do portal: Gestão, Processos, Registros, Ajuda e, para quem administra, Administração. A saudação usa o primeiro nome da sessão autenticada.",
    },
    {
      term: "Visão geral",
      meaning: "Indicadores do programa. Competência, datas, unidade e departamento recortam o gráfico. Consolidado reúne todas as unidades do recorte — é filtro, não autorização.",
    },
    {
      term: "Consolidado",
      meaning: "Visão com os totais do universo permitido pelos filtros. Os cards identificam «todas as unidades» e o período. Os valores vêm da API, sem soma na tela.",
    },
    {
      term: "Meus processos",
      meaning: "Lista os processos disponíveis. Abra um processo para ver melhorias, revisões e diagramas.",
    },
    {
      term: "Administração",
      meaning: "Área disponível para usuários responsáveis pela administração do Portal. Configurações fica dentro dela.",
    },
  ] satisfies readonly UserManualConcept[],
  sections: [
    {
      id: "home",
      title: "Início e busca",
      intro:
        "A barra superior leva às áreas do portal. Buscar, ou Ctrl+K, abre os mesmos caminhos em qualquer tela. A busca do Início filtra os cards daquela tela.",
      bullets: [
        "A saudação do Hero usa Bom dia, Boa tarde ou Boa noite e o primeiro nome da sessão. Sem nome, aparece Bem-vindo ao Portal Transforma+.",
        "As métricas do Hero (economia líquida, horas e soluções) vêm do mesmo resumo da Visão geral no mês corrente.",
        "Use a estrela de um caminho para fixá-lo em Favoritos.",
        "Favoritos ficam só ao lado de Buscar, na barra superior.",
        "Abaixo da busca do Início aparecem os últimos acessos, não uma segunda lista de favoritos.",
        "Eventos e interações mostram só sinais já existentes, como revisões a vencer.",
      ],
      links: [{ want: "Abrir o hub", where: "Início", how: "Clique em Início na barra.", path: TRANSFORMOMETRO_ROUTES.home }],
    },
    {
      id: "overview",
      title: "Visão geral",
      intro: "Mostra indicadores e resultados do programa de transformação.",
      bullets: [
        "As visões são Consolidado, Unidade e Departamento. Isso recorta os dados; não muda quem pode abrir o portal.",
        "Em Consolidado, os cards mostram o contexto de todas as unidades e o período.",
        "Em Unidade ou Departamento, o rodapé do card identifica o nome canônico escolhido e o período.",
        "Economia, horas, soluções, investimento e ROI vêm calculados pela API. A tela não soma cards.",
      ],
      links: [
        {
          want: "Ver indicadores",
          where: "Visão geral",
          how: "Abra Visão geral na barra ou no Início.",
          path: TRANSFORMOMETRO_ROUTES.dashboard,
        },
      ],
    },
    {
      id: "processes",
      title: "Meus processos",
      intro: "Lista os processos disponíveis no portal.",
      links: [
        {
          want: "Trabalhar um processo",
          where: "Meus processos",
          how: "Abra a lista e escolha o processo.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "minutes",
      title: "Atas",
      intro: "Reuniões, registros e assinaturas. Assinar depende de ser signatário daquela ata.",
      links: [
        {
          want: "Abrir atas",
          where: "Atas",
          how: "No Início, em Registros.",
          path: TRANSFORMOMETRO_ROUTES.meetingMinutes,
        },
      ],
    },
    {
      id: "data",
      title: "Exportar / Importar",
      intro: "Backup, transferência e restauração. A importação pede prévia e confirmação.",
      links: [
        {
          want: "Fazer backup",
          where: "Exportar / Importar",
          how: "No Início, em Registros.",
          path: TRANSFORMOMETRO_ROUTES.data,
        },
      ],
    },
    {
      id: "administration",
      title: "Administração",
      intro:
        "A área Administração fica disponível para usuários responsáveis pela administração do Portal. Quem só usa o portal no dia a dia não vê essa área na barra nem na busca.",
      bullets: ["Configurações fica dentro de Administração. Não é uma área da barra superior."],
      links: [
        {
          want: "Abrir a administração",
          where: "Administração",
          how: "Use a barra ou o card Administração no Início.",
          path: TRANSFORMOMETRO_ROUTES.administration,
          requiresManage: true,
        },
      ],
    },
    {
      id: "settings",
      title: "Configurações",
      intro: "Unidades, departamentos e o catálogo de recursos compartilhados.",
      bullets: [
        "Unidades são as plantas ou sites usados nos processos e no filtro da Visão geral.",
        "Departamentos são as áreas ligadas às unidades.",
        "Criar ou alterar o catálogo de recursos é administração. Ligar um recurso a uma revisão faz parte do uso normal do processo.",
      ],
      links: [
        {
          want: "Cadastrar unidade",
          where: "Unidades",
          how: "Administração → Configurações → Unidades.",
          path: TRANSFORMOMETRO_ROUTES.settingsUnits,
          requiresManage: true,
        },
        {
          want: "Cadastrar departamento",
          where: "Departamentos",
          how: "Administração → Configurações → Departamentos.",
          path: TRANSFORMOMETRO_ROUTES.settingsDepartments,
          requiresManage: true,
        },
        {
          want: "Cadastrar recurso",
          where: "Recursos compartilhados",
          how: "Administração → Configurações → Recursos compartilhados.",
          path: TRANSFORMOMETRO_ROUTES.settingsSharedResources,
          requiresManage: true,
        },
      ],
    },
  ] satisfies readonly UserManualSection[],
} as const;
