/**
 * Ajuda in-app do Meu Modelador de Processos (BPMN Modeler).
 * Conteúdo PT-BR canônico — feature-help-sync: toda mudança user-facing
 * deve atualizar estas chaves no mesmo entregável.
 */
export const HELP_TOOLTIPS = {
  library: {
    search: "Busque modelos pelo nome ou identificador.",
    archivedToggle: "Alterna entre modelos ativos, arquivados (somente leitura) ou todos.",
    sort: "Ordena a lista por atualização, criação ou nome.",
    create: "Cria um novo modelo de processo vazio.",
    import: "Importa um arquivo .bpmn existente (BPMN 2.0).",
    actions: "Ações do modelo: abrir, exportar, duplicar, arquivar.",
  },
  editor: {
    save: "Salva o modelo (Ctrl+S). A gravação só é confirmada após leitura do servidor.",
    undo: "Desfaz a última edição do diagrama.",
    redo: "Refaz a edição desfeita.",
    validate: "Valida o diagrama sem salvar e lista problemas na aba Validação.",
    organize: "Organiza o layout automaticamente. Você pode revisar antes de aplicar.",
    export: "Exporta o modelo canônico (.bpmn) ou imagens (SVG/PNG).",
    history: "Revisões imutáveis do modelo. Crie marcos ou restaure versões.",
    moreActions: "Ações secundárias: exportar, arquivar e outras opções do modelo.",
    zoomIn: "Aumenta o zoom do diagrama.",
    zoomOut: "Diminui o zoom do diagrama.",
    fitViewport: "Ajusta o diagrama inteiro à área visível.",
    noUndo: "Nenhuma alteração para desfazer.",
    noRedo: "Nenhuma alteração para refazer.",
    editorLoading: "O editor ainda está carregando.",
  },
  readOnly: {
    archived: "Modelos arquivados são somente leitura. Desarquive para editar.",
    revision: "Revisões são imutáveis. Use Restaurar para voltar a uma versão.",
    tablet: "Em tablets o editor opera em modo somente leitura.",
  },
} as const;
