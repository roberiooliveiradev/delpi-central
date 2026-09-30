export const DELPI_MES_COPY = {
  productName: "Delpi MES",
  productDescription: "Supervisão e análise gerencial da execução industrial da Delpi.",
  monitoring: {
    title: "Monitoramento Industrial",
    description: "Estrutura pronta para acompanhamento dos centros de trabalho e seus estados operacionais.",
    guidance: "Selecione a filial e use esta área como ponto de entrada para a visão operacional consolidada.",
  },
  downtimes: {
    title: "Paradas",
    description: "Espaço preparado para consulta gerencial e classificação visual do histórico de paradas.",
    guidance: "Os filtros e resultados serão conectados ao contrato paginado do Delpi MES na próxima etapa funcional.",
  },
  history: {
    title: "Histórico",
    description: "Base de navegação preparada para análise da linha do tempo dos runs de produção.",
    guidance: "O detalhamento preservará os tempos calculados pelo owner dos fatos MES.",
  },
  registrations: {
    title: "Cadastros",
    description: "Configurações globais utilizadas pelo Delpi MES.",
    globalScope: "Cadastro global",
    globalScopeHint: "As alterações são válidas para todas as filiais.",
    downtimeReasons: {
      title: "Motivos de parada",
      description: "Gerencie os motivos utilizados na classificação das paradas MES.",
      action: "Gerenciar",
    },
  },
  help: {
    branch: "A filial faz parte da URL para manter navegação, recarga e compartilhamento no mesmo contexto.",
    permissions: "As áreas visíveis refletem suas permissões; o backend valida novamente cada consulta.",
  },
} as const;
