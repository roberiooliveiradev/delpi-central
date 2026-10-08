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
  scopeNote: "Este manual descreve o que o Portal Transforma+ já oferece.",
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
      term: "Meta e IDD",
      meaning: "A Economia bruta é o indicador do programa com meta e nota IDD. A meta parcial, a meta do período e a nota vêm prontas — a tela não calcula. Os outros cards mostram só o valor operacional.",
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
      bullets: [
        "A barra superior leva às áreas do portal. Buscar, ou Ctrl+K, abre os mesmos caminhos em qualquer tela. A busca do Início filtra os cards daquela tela.",
        "A saudação do Hero usa Bom dia, Boa tarde ou Boa noite e o primeiro nome da sessão. Sem nome, aparece Bem-vindo ao Portal Transforma+.",
        "As métricas do Hero (economia líquida, horas e soluções) vêm do mesmo resumo da Visão geral no mês corrente.",
        "Use a estrela de um caminho para fixá-lo em Favoritos. Favoritos ficam ao lado de Buscar, na barra superior; abaixo da busca do Início aparecem os últimos acessos.",
        "Eventos e interações mostram só sinais já existentes, como revisões a vencer.",
      ],
      links: [{ want: "Abrir o hub", where: "Início", how: "Clique em Início na barra.", path: TRANSFORMOMETRO_ROUTES.home }],
    },
    {
      id: "overview",
      title: "Visão geral",
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
      id: "targets-idd",
      title: "Metas e IDD",
      links: [
        {
          want: "Ver metas e IDD",
          where: "Visão geral",
          how: "Abra Visão geral e veja o card Economia bruta.",
          path: TRANSFORMOMETRO_ROUTES.dashboard,
        },
      ],
    },
    {
      id: "processes",
      title: "Meus processos",
      bullets: [
        "No Hero da lista: Processos/Departamentos, busca, status, ordenação, modo de visualização, Atualizar e Novo processo. Abaixo do Hero ficam só os resultados.",
        "Abra um processo para trabalhar no workspace. O caminho, o Hero e as abas horizontais organizam o processo, melhorias e revisões.",
        "Atas continuam em Atas; não há vínculo de ata ao processo neste workspace.",
      ],
      links: [
        {
          want: "Trabalhar um processo",
          where: "Meus processos",
          how: "Abra a lista e escolha o processo. Use o caminho e as abas do Hero para mudar de seção; F5 mantém o caminho.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
        {
          want: "Documentar o processo",
          where: "Documentação do processo",
          how: "No workspace, abra Documentação, crie um documento Markdown, visualize e salve. Excluir pede confirmação.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
        {
          want: "Abrir a sala do processo",
          where: "Workspace do processo",
          how: "Use Sala de interação no Hero do processo ou a aba Sala de interação.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "process-documentation",
      title: "Documentação do processo",
      links: [
        {
          want: "Abrir documentação",
          where: "Workspace do processo",
          how: "Nas abas horizontais do processo, escolha Documentação.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "revision-diagnostic",
      title: "Diagnóstico da revisão",
      links: [
        {
          want: "Abrir o diagnóstico de uma revisão",
          where: "Workspace do processo",
          how: "Abra a revisão e escolha a aba Diagnóstico.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "my-tasks",
      title: "Minhas tarefas",
      links: [
        {
          want: "Criar ou acompanhar uma tarefa",
          where: "Minhas tarefas",
          how: "Use Nova tarefa, os filtros Pendentes/Concluídas/Todas ou Atualizar.",
          path: TRANSFORMOMETRO_ROUTES.myTasks,
        },
      ],
    },
    {
      id: "interaction",
      title: "Sala de interação",
      links: [
        {
          want: "Abrir as salas",
          where: "Sala de interação",
          how: "Use Sala de interação na barra ou no grupo Operação do Início.",
          path: TRANSFORMOMETRO_ROUTES.interactionRooms,
        },
        {
          want: "Começar a conversa de um processo",
          where: "Meus processos",
          how: "Abra o processo e use Sala de interação no painel.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "teo",
      title: "TÉO no ChatGPT",
      intro:
        "Dentro do workspace de um processo, a barra superior mostra a ação TÉO. Ela copia o contexto de navegação atual — processo, melhoria, revisão e seção — para você colar no ChatGPT.",
      bullets: [
        "O contexto é só a localização: identificadores e a seção aberta. Não leva token, permissão nem conteúdo do processo.",
        "No navegador integrado do ChatGPT para desktop, o portal já oferece o contexto como ferramenta do site — o TÉO descobre onde você está sem copiar nada.",
        "O TÉO usa os identificadores para consultar os dados canônicos do Transformômetro. O contexto não concede acesso: quem não pode ver o processo continua sem acesso.",
        "Mudar de processo, melhoria, revisão ou seção atualiza o contexto — copie de novo se mudar de tela.",
      ],
      links: [
        {
          want: "Analisar o contexto atual com TÉO",
          where: "Workspace do processo",
          how: "Abra o processo, escolha a melhoria/revisão e a seção, e use TÉO na barra superior. Cole o contexto no ChatGPT.",
          path: TRANSFORMOMETRO_ROUTES.processes,
        },
      ],
    },
    {
      id: "minutes",
      title: "Atas",
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
