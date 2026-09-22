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
        "Use Período rápido para escolher intervalos comuns ou selecione Personalizado para informar datas manualmente.",
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
      id: "targets-idd",
      title: "Metas e IDD",
      intro:
        "A Visão geral mostra a meta e a nota IDD do programa no card de Economia bruta, quando esses dados estão disponíveis.",
      bullets: [
        "Economia bruta é o indicador do programa com meta.",
        "Meta parcial é a referência já calculada para o recorte de datas aberto — não é uma conta feita na tela.",
        "Meta do período (ou meta do mês) é a referência do intervalo canônico.",
        "A nota IDD do card e o selo no título da página vêm prontos. Sem dado, o valor operacional continua e a meta some.",
        "Consolidado, Unidade e Departamento recortam os números do programa. A meta estratégica do programa permanece a referência de Engenharia e é rotulada quando for consolidada.",
        "Status (dentro, abaixo ou acima da meta) e a direção (quanto maior ou menor, melhor) acompanham a meta da Economia bruta.",
      ],
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
      intro:
        "Lista os processos com filtros e contagem no Hero. Abre o workspace com caminho, Hero e abas horizontais: visão geral, melhorias, revisões, diagrama, documentação Markdown, tarefas e Sala de interação.",
      bullets: [
        "No Hero da lista: Processos/Departamentos, busca, status, Atualizar e Novo processo. Ordenação e modos de visualização ficam na barra da listagem.",
        "Abra um processo para trabalhar no workspace. O caminho, o Hero e as abas horizontais organizam o processo, melhorias e revisões.",
        "Processo-mestre não pertence a uma única unidade: unidade e departamento aparecem na melhoria.",
        "Medições, investimentos e recursos compartilhados ficam em cada revisão — não invente pontuação no resumo.",
        "Documentação do processo guarda textos em Markdown (criar, visualizar, editar e excluir). Não substitui diagrama, revisão nem dados estruturados.",
        "Sala de interação abre a conversa canônica daquele processo. Tarefas relacionadas são só as criadas a partir de mensagens da sala.",
        "Atas continuam em Atas; não há vínculo de ata ao processo neste workspace.",
        "Não há árvore de pastas: a hierarquia Processo → Melhoria → Revisão aparece no caminho e na aba Melhorias.",
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
      intro:
        "Registre o conhecimento textual do processo em documentos Markdown dentro do workspace.",
      bullets: [
        "Crie quantos documentos precisar; cada um tem título, conteúdo Markdown, autoria e data de atualização.",
        "Use Editar / Visualizar para escrever e conferir a renderização segura antes de salvar.",
        "A documentação descreve o processo — não redefine diagrama, revisão, medição, ata ou evidências.",
        "Excluir um documento pede confirmação e remove apenas aquela documentação.",
      ],
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
      id: "my-tasks",
      title: "Minhas tarefas",
      intro:
        "Crie tarefas do portal, atribua um responsável e acompanhe prazos. Assinaturas de ata pendentes também aparecem aqui, sem virar outra tarefa.",
      bullets: [
        "Nova tarefa pede título, responsável, prazo opcional e descrição. Revise o resumo e confirme antes de gravar.",
        "O responsável é um usuário do diretório. O nome é só exibição; a tarefa guarda o identificador.",
        "Edite ou conclua só a tarefa criada no portal. Concluir tira o item de Pendentes.",
        "A busca fica na fila e combina com Pendentes, Concluídas e Todas.",
        "Assinatura pendente de ata não se edita nem se conclui nesta lista: abra a ata e assine lá. Depois que assinar, o item some.",
      ],
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
      intro:
        "A sala reúne a conversa de um processo. A lista mostra só processos que já têm sala. Abrir um processo cria a sala daquele processo na primeira vez.",
      bullets: [
        "Na barra, Sala de interação abre Conversas. A busca filtra pelo nome ou código do processo.",
        "Todas, Não lidas, Menções e Processos usam a leitura e as menções reais da sala.",
        "Escreva a mensagem, mencione uma pessoa com @, responda, reaja ou anexe um arquivo e envie. Também dá para colar uma imagem direto no editor. O texto permanece se o envio falhar. As reações ficam na mensagem; para reagir, use as opções da mensagem.",
        "Na conversa, mensagens seguidas da mesma pessoa ficam agrupadas. Toque na citação de uma resposta para ir até a mensagem original. Anexos aparecem na bolha com prévia; você pode remover o anexo que você mesmo enviou. Menções ficam destacadas e as fotos de perfil aparecem quando disponíveis.",
        "Use Localizar no chat (ícone de busca no cabeçalho da sala) para achar texto nas mensagens já carregadas.",
        "Ao editar a própria mensagem, use o mesmo editor rico do envio (formatação e @). Arquivos e links reúne o que foi enviado na sala. O painel da sala mostra o processo, quem falou e as mensagens fixadas.",
        "Atualizar busca as mensagens de novo. A conversa também é atualizada enquanto a sala está aberta. Use Carregar mensagens anteriores para ver o histórico mais antigo. O botão ao lado da linha divisória recolhe ou mostra a lista de conversas; arraste a linha para mudar a largura.",
        "A sala não substitui tarefas, atas nem revisões. Cada uma continua no seu lugar.",
      ],
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
