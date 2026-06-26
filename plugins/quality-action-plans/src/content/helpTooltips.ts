export const PAC_HELP_TOOLTIPS = {
  filters: {
    scope:
      "Escopo da não conformidade: interna (detectada na planta) ou externa (cliente/fornecedor). Vazio = todos.",
    status: "Estágio do plano no fluxo PAC (triagem, contenção, análise, validação, concluído, etc.).",
    severity: "Prioridade do plano: baixa, média, alta ou crítica.",
    branch: "Filial TOTVS (01 ou 02). Vazio = todas as filiais.",
    customer: "Filtra planos pelo nome do cliente informado na identificação.",
    product: "Código do produto vinculado à NC.",
    owner: "Responsável pelo plano (usuário ou identificador cadastrado).",
    department: "Área ou departamento associado ao problema.",
    rootCause: "Texto ou categoria da causa raiz registrada no plano.",
    overdueOnly:
      "Mostra apenas planos com ações ou prazos em atraso conforme regras de SLA do PAC.",
    refresh: "Recarrega a listagem com os filtros atuais.",
    clear: "Remove todos os filtros aplicados.",
  },
  kpis: {
    openPlans: "Planos em andamento (não concluídos nem cancelados) no recorte atual.",
    criticalOpen: "Planos abertos classificados com severidade crítica.",
    overduePlans: "Planos com prazo ou estágio em atraso segundo o SLA configurado.",
    overdueActions: "Ações corretivas/contenção com prazo vencido e ainda não concluídas.",
    waitingValidation: "Planos aguardando validação de eficácia ou encerramento formal.",
    completedThisMonth: "Planos concluídos no mês calendário corrente.",
    avgClosure:
      "Média de dias entre abertura e encerramento dos planos concluídos na janela analítica.",
    avgEffectiveness:
      "Média de dias até o registro de eficácia nos planos revisados na janela analítica.",
    recurrence:
      "Grupos com mesmo produto e modo de falha abertos duas ou mais vezes na janela.",
  },
  charts: {
    overview: "Visão consolidada: abertos, críticos, aguardando validação e concluídos no mês.",
    byBranch: "Comparativo de planos abertos e críticos por filial.",
    byScope: "Distribuição entre NC interna e externa.",
    byStatus: "Quantidade de planos em cada estágio do fluxo.",
    bySeverity: "Distribuição por nível de severidade nos planos carregados.",
    topCategories: "Categorias de problema mais frequentes na janela selecionada.",
    topFailureModes: "Modos de falha que mais se repetem nos planos analisados.",
    actionsMix: "Volume de ações criadas por tipo (contenção, corretiva, preventiva, etc.).",
    topCustomers: "Clientes com maior número de planos de ação na janela.",
    topProducts: "Produtos com mais ocorrências de NC na janela.",
    topOwners: "Responsáveis com maior volume de planos abertos ou tratados.",
    effectivenessByAction:
      "Percentual de eficácia entre planos revisados, agrupado por tipo de ação predominante.",
  },
  sections: {
    problem: "Resumo do relato, severidade, escopo e identificação principal da NC.",
    audit: "Histórico de eventos do plano (criação, alterações, eficácia, reabertura).",
    template: "Relatório estruturado do cliente (ex.: 8D) quando o plano usa template dedicado.",
    ishikawa:
      "Diagrama espinha de peixe (6M): hipóteses de causa por Máquina, Método, Material, Mão de obra, Medição e Meio ambiente.",
    fiveWhys:
      "Trilhas de porquês de ocorrência e detecção. Quantidade flexível; deslize horizontalmente para ver todos os passos.",
    actions:
      "Plano de ações corretivas, preventivas e de contenção com responsável, prazo, evidência e status.",
    effectiveness:
      "Registro da verificação de eficácia após implementação das ações (eficaz, parcial ou ineficaz).",
    evidences: "Anexos que comprovam contenção, correção ou verificação (arquivos, fotos, laudos).",
    similarCases:
      "Planos anteriores com produto, sintoma ou causa semelhantes para reutilizar aprendizado.",
    timeline: "Linha do tempo das mudanças de status e marcos do plano.",
    disciplineProgress:
      "Checklist das disciplinas D0–D8 do método 8D e percentual de preenchimento.",
    recurrencePanel:
      "Agrupamentos com reabertura recorrente do mesmo produto e modo de falha.",
    myQueue: "Fila pessoal de planos e ações sob sua responsabilidade.",
    solutionPatterns: "Padrões de solução reutilizáveis promovidos a partir de planos eficazes.",
  },
  form: {
    identification: "Dados cadastrais do plano: título, cliente, produto, lote e filial.",
    source: "Canal de origem do relato (e-mail, PDF, texto manual) e referência externa.",
    context: "Vínculos opcionais com Kaizen, auditoria 5S ou outras fontes.",
    description: "Narrativa do problema relatado e tags de sintoma para busca futura.",
    actionType: "Classificação da ação: contenção, corretiva, preventiva, verificação, padronização ou treinamento.",
    actionTrack: "Em 8D, indica se a ação trata a causa de ocorrência ou de detecção.",
    actionEvidence:
      "Quando marcado, exige anexo de evidência antes de concluir a ação.",
    rootCause: "Síntese da causa raiz validada após Ishikawa e porquês.",
    confidence: "Grau de confiança da equipe na causa raiz identificada.",
    kaizenLink: "Vincula o plano a uma melhoria contínua (Kaizen) relacionada.",
  },
  alerts: {
    stalled:
      "Planos sem movimentação recente no estágio atual — podem precisar de follow-up.",
    effectivenessPending:
      "Planos com eficácia submetida aguardando aprovação do coordenador.",
    recurrence:
      "Padrões com múltiplas aberturas do mesmo produto e falha nos últimos meses.",
  },
} as const;
