/**
 * Ajuda in-app do Meu Modelador de Processos (BPMN Modeler).
 * Conteúdo PT-BR canônico — feature-help-sync: toda mudança user-facing
 * deve atualizar estas chaves no mesmo entregável.
 */
export const HELP_TOOLTIPS = {
  library: {
    search: "Busque modelos pelo nome ou identificador.",
    archivedToggle: "Mostra também os modelos arquivados (somente leitura).",
    create: "Cria um novo modelo de processo vazio.",
    import: "Importa um arquivo .bpmn existente (BPMN 2.0).",
  },
  editor: {
    save: "Salva o modelo (Ctrl+S). A gravação só é confirmada após leitura do servidor.",
    validate: "Valida o diagrama sem salvar e lista problemas na aba Validação.",
    organize: "Organiza o layout automaticamente. Você pode revisar antes de aplicar.",
    export: "Exporta o modelo canônico (.bpmn) ou imagens (SVG/PNG).",
    history: "Revisões imutáveis do modelo. Crie marcos ou restaure versões.",
  },
  readOnly: {
    archived: "Modelos arquivados são somente leitura. Desarquive para editar.",
    revision: "Revisões são imutáveis. Use Restaurar para voltar a uma versão.",
    tablet: "Em tablets o editor opera em modo somente leitura.",
  },
} as const;
