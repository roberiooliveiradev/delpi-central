/**
 * Catálogo central de helps — Administração SI (/settings).
 * Usar com FieldLabel / SectionHintLabel do @delpi/plugin-ui.
 *
 * Doc de referência: plugins/strategic-indicators/docs/HELP-CONTENT-ADMIN.md
 */
export const SI_HELP = {
  shell: {
    pageTitle:
      "Central administrativa do módulo: catálogo estrutural, metas anuais, parâmetros globais e auditoria.",
    refreshSnapshots:
      "Recalcula scores materializados (period_scores) a partir das fontes TOTVS e do catálogo. A leitura atual permanece até a nova versão ficar pronta.",
    lastSync:
      "Momento da última gravação de parâmetros/governança ou último refresh bem-sucedido de scores, conforme o contexto.",
    updatedBy:
      "Usuário registrado na última alteração administrativa persistida no backend.",
  },

  nav: {
    overview:
      "Resumo de saúde do catálogo: contagens, pendências de validação e atalhos.",
    catalog:
      "Departamentos, indicadores estruturais e checagem de consistência (escopo, metas, agregação).",
    goals:
      "Ciclos anuais e metas analíticas por indicador e escopo (Consolidado / 01 / 02).",
    system:
      "Parâmetros globais, governança, backup JSON e trilha de auditoria.",
    tabStructure:
      "Cadastro de departamentos e indicadores — fonte de verdade do painel estratégico.",
    tabValidation:
      "Lista cruzada departamento × indicador × metas ativas com apontamentos automáticos.",
  },

  overview: {
    kpiDepartments:
      "Departamentos ativos no catálogo. Peso de cada um entra no cálculo do IGD.",
    kpiIndicators:
      "Indicadores estruturais ativos vinculados a uma fonte de medição (source_key).",
    kpiGoalsYear:
      "Metas analíticas ativas no ano selecionado no filtro global de metas.",
    kpiValidationIssues:
      "Apontamentos de validação (warning/error) no catálogo do ano corrente.",
    actionGoValidation:
      "Abre a validação com filtro «só pendências» para corrigir antes de publicar.",
    actionNewIndicator:
      "Atalho para criar indicador — selecione o departamento na aba Catálogo.",
    actionNewGoalYear:
      "Abre fluxo de criação de ciclo anual de metas.",
    pendingIssues:
      "Inconsistências detectadas automaticamente: escopo de meta, agregação entre filiais, source_key ausente etc.",
  },

  catalog: {
    searchDepartments:
      "Filtra a lista de departamentos por nome, sigla ou id técnico.",
    newDepartment:
      "Cadastra departamento no organograma estratégico (peso IGD, modo de agregação do IDD).",
    departmentList:
      "Selecione um departamento para ver e editar indicadores no painel ao lado.",
    departmentWeight:
      "Peso percentual do departamento na composição do IGD (soma dos departamentos deve fechar 100%).",
    departmentAggregation:
      "Como o IDD do departamento é calculado na visão consolidada: nota única ou média das filiais 01/02.",
    indicatorList:
      "Indicadores do departamento selecionado. Clique para editar ou use ações de ativar/desativar.",
    newIndicator:
      "Define indicador estrutural: escopo, fonte, formato numérico e agregação entre filiais.",
    searchIndicators:
      "Busca por nome ou id do indicador dentro do departamento selecionado.",

    validationYear:
      "Ano de referência das metas ativas usadas na checagem (goal_year).",
    validationDepartment:
      "Restringe a lista a um departamento ou mostra todos.",
    validationOnlyIssues:
      "Oculta linhas sem apontamento — útil para fechar pendências antes do fechamento do mês.",
    validationColDepartment:
      "Departamento e peso no IGD. Departamento inativo ainda listado se tiver indicador ativo.",
    validationColAggregation:
      "aggregation_mode do departamento (Consolidado vs Média das unidades) — afeta IDD, não rollup do indicador.",
    validationColIndicator:
      "Indicador estrutural e peso dentro do departamento.",
    validationColScope:
      "Escopo do indicador: Consolidado (medição única) ou Por unidade (01/02).",
    validationColGoals:
      "Metas ativas no ano: C = Consolidado, 01 = Santa Catarina, 02 = Espírito Santo.",
    validationColStatus:
      "Pior severidade entre os apontamentos da linha: OK, Info, Atenção ou Erro.",
    validationColIssues:
      "Resumo textual dos apontamentos — detalhe completo no painel lateral (layout proposto).",
  },

  department: {
    sectionIdentity:
      "Identificação do departamento no organograma e na navegação do painel.",
    departmentId:
      "Identificador técnico estável (inglês, snake-case). Alterar exige cuidado — impacta APIs e integrações.",
    departmentName:
      "Nome completo exibido no painel estratégico e dashboards federados.",
    shortName:
      "Sigla curta (ex.: Com., Prod.) usada em tabelas e badges compactos.",
    sectionIdd:
      "Regras de composição do IDD departamental e peso no IGD.",
    weightPct:
      "Participação percentual deste departamento no Índice Geral Delpi.",
    aggregationMode:
      "Consolidado: IDD departamento usa meta/nota consolidada. Média das unidades: média aritmética das filiais 01 e 02.",
    sectionNarrative:
      "Textos executivos exibidos no painel — não alteram cálculo de scores.",
    strategicSummary:
      "Resumo estratégico do departamento para apresentação executiva.",
    headlineGoal:
      "Meta headline legado do painel administrativo (visão de leitura).",
    supportingFocus:
      "Foco de apoio / narrativa complementar no resumo do departamento.",
    displayOrder:
      "Ordem de exibição na lista e no organograma (menor = primeiro).",
    isActive:
      "Departamento inativo some do painel público; indicadores filhos podem permanecer cadastrados.",
  },

  indicator: {
    sectionEssential:
      "Campos que definem identidade, escopo e ligação com a fonte de dados.",
    indicatorId:
      "Identificador técnico único (inglês). Usado em APIs, period_scores e integrações S2S.",
    indicatorName:
      "Nome amigável exibido no painel, dashboards e chat (via api-delpi).",
    weightPct:
      "Peso do indicador dentro do IDD do departamento (soma dos ativos ≈ 100%).",
    scopeType:
      "Consolidado: uma medição para o indicador. Por unidade: realizado e metas separados por filial 01/02.",
    branchValueAggregation:
      "Na visão Consolidado, define como combinar filiais 01/02: soma (ROL), média (%, OTD), automático (por unidade) ou valor da fonte (PPM consolidado TOTVS).",
    sourceKey:
      "Chave que liga o indicador ao provider de snapshot (ex.: commercial_rol). Obrigatória se ativo.",
    performanceDirection:
      "Quanto maior melhor (ROL, OTD) ou quanto menor melhor (PPM, custo). Afeta cálculo da nota.",
    isActive:
      "Indicador inativo não entra no IDD nem nos dashboards; metas podem permanecer cadastradas.",
    sectionFormat:
      "Formatação numérica exibida no painel e exportações.",
    valueUnit:
      "Unidade lógica: moeda, percentual, PPM, dias etc. Influencia agregação «Automático» entre filiais.",
    valueDecimals:
      "Casas decimais na exibição do realizado e das metas comparáveis.",
    valuePrefix:
      "Prefixo fixo antes do número (ex.: R$). Opcional se a unidade já formata.",
    valueSuffix:
      "Sufixo após o número (ex.: %, PPM, dias).",
    strategicDescription:
      "Descrição longa para contexto executivo — não entra no cálculo.",
    displayOrder:
      "Ordem do indicador dentro do departamento no painel.",
  },

  goals: {
    yearList:
      "Ciclos anuais de metas analíticas. Selecione um ano para editar no painel.",
    newYear:
      "Cria goal_year novo e opcionalmente metas iniciais em lote.",
    duplicateYear:
      "Copia metas de um ano para outro — revisar valores por filial após duplicar.",
    fillMissing:
      "Cria metas faltantes a partir de modelo ou indicadores sem meta no ano.",
    yearSummaryIndicators:
      "Indicadores ativos considerados no ciclo do ano selecionado.",
    yearSummaryGoals:
      "Versões ativas de metas (por indicador × escopo) no ano.",
    yearSummaryWarnings:
      "Indicadores ativos sem meta no ano ou com escopo incompleto.",
    goalTableIndicator:
      "Indicador ao qual a meta se aplica.",
    goalTableScope:
      "Escopo da meta: Consolidado (vazio), 01 Santa Catarina ou 02 Espírito Santo.",
    goalTableMode:
      "Padrão: meta fixa no período. Curva: pontos mensais/trimestrais distribuídos no ano.",
    goalTableValue:
      "Valor cadastrado (standard) ou curva — o comparável do período é calculado pelo SI.",
  },

  goalForm: {
    sectionTarget:
      "A qual indicador e ano a meta se aplica.",
    indicatorId:
      "Indicador estrutural destino. Deve estar ativo e com source_key se for usado no painel.",
    goalYear:
      "Ano civil do ciclo (2020–2100). Uma meta ativa por (indicador, ano, escopo).",
    goalScopeBranch:
      "Consolidado: meta única na visão geral. 01/02: meta por filial — obrigatório para departamentos «média das unidades».",
    sectionValue:
      "Valor e periodicidade usados no cálculo da meta comparável do período filtrado.",
    goalLabel:
      "Rótulo exibido no admin e no painel (ex.: «Curva R$», «8 PDIs»).",
    goalValue:
      "Valor numérico cadastrado. Em modo Curva, a API persiste 0 — valores ficam nos pontos da curva.",
    goalPeriodicity:
      "Mensal, trimestral, semanal ou anual. Em Curva, define quantos pontos na grade.",
    goalMode:
      "Padrão: meta fixa proporcional ao período. Curva: soma/média dos pontos cobertos pelo filtro de datas.",
    monthlyTargets:
      "Pontos da curva (mês 1…N). Usados quando goal_mode = monthly_curve.",
    sectionValidity:
      "Vigência opcional da meta — fora do intervalo ela não resolve no catálogo.",
    validFrom:
      "Início da vigência (inclusivo). Vazio = sem limite inferior.",
    validTo:
      "Fim da vigência (inclusivo). Vazio = sem limite superior.",
    notes:
      "Observações internas — não exibidas no painel público.",
  },

  system: {
    sectionParameters:
      "Convenções transversais do módulo (thresholds, labels, flags) persistidas em module_settings.",
    parameterKey:
      "Chave técnica do parâmetro — não alterar sem alinhar com a API.",
    parameterLabel:
      "Rótulo legível exibido neste editor.",
    parameterValue:
      "Valor string persistido — interpretação depende da chave (ver docs da API).",
    sectionGovernance:
      "Notas de governança e políticas internas do módulo (texto livre por item).",
    governanceLabel:
      "Título do item de governança.",
    governanceValue:
      "Conteúdo / política associada.",
    governanceObservation:
      "Observação complementar ou referência normativa.",

    importExportTitle:
      "Backup JSON versionado: departamentos, indicadores, metas ativas e parâmetros globais.",
    exportJson:
      "Baixa snapshot completo do catálogo administrativo para arquivo local.",
    importFile:
      "Selecione JSON exportado deste módulo ou ambiente compatível (schema_version).",
    importModeReplace:
      "Apaga TODO o cadastro atual e importa o arquivo. Scores materializados são limpos até refresh.",
    importModeMerge:
      "Upsert por ID: mantém registros ausentes no arquivo; metas existentes não são sobrescritas.",
    importIncludeGoals:
      "No modo Mesclar: cria metas que ainda não existem; não atualiza metas já cadastradas.",
    importPreview:
      "Simula insert/update/delete antes de aplicar — obrigatório antes de Substituir.",
    importApply:
      "Persiste o bundle após pré-visualização válida.",

    auditSummary:
      "Contagem de eventos administrativos recentes por tipo de entidade.",
    auditLatestByEntity:
      "Última alteração registrada em departamentos, indicadores, metas etc.",
    auditTimeline:
      "Histórico filtrável de alterações com autor, data e diff resumido.",
    auditEntityFilter:
      "Filtra timeline por departamentos, indicadores, metas, parâmetros ou governança.",
    changeRequests:
      "Camada preparatória para workflow de aprovação — solicitações ainda não executam alterações automaticamente.",
  },

  badges: {
    goalScopeConsolidated:
      "Meta cadastrada com escopo Consolidado (goal_scope_branch vazio).",
    goalScope01:
      "Meta cadastrada para filial 01 — Santa Catarina.",
    goalScope02:
      "Meta cadastrada para filial 02 — Espírito Santo.",
    severityOk:
      "Nenhum apontamento — catálogo coerente para este indicador no ano.",
    severityInfo:
      "Informação — revisar se intencional (ex.: indicador per_unit em dept consolidado).",
    severityWarning:
      "Atenção — pode causar meta/realizado inconsistente em alguma visão.",
    severityError:
      "Erro — impede cálculo correto (ex.: ativo sem source_key ou sem meta no ano).",
    branchAggregationAuto:
      "Agregação automática: moeda/contagem somam; percentual/PPM usam média.",
    branchAggregationSum:
      "Soma realizados e metas 01+02 na visão Consolidado (ex.: ROL).",
    branchAggregationAverage:
      "Média aritmética entre filiais 01 e 02 (ex.: OTD, %).",
    branchAggregationSource:
      "Realizado vem da API consolidada; meta só com escopo Consolidado cadastrado.",
  },
} as const;

type HelpLeaf = string | { readonly [key: string]: HelpLeaf };

function collectPaths(
  node: HelpLeaf,
  prefix: string,
  out: Map<string, string>,
): void {
  if (typeof node === "string") {
    out.set(prefix, node);
    return;
  }
  for (const [key, value] of Object.entries(node)) {
    const next = prefix ? `${prefix}.${key}` : key;
    collectPaths(value, next, out);
  }
}

const SI_HELP_INDEX: Map<string, string> = (() => {
  const map = new Map<string, string>();
  collectPaths(SI_HELP as HelpLeaf, "", map);
  return map;
})();

/** Resolve texto de help por chave dotted (ex.: `catalog.validationYear`). */
export function getSiHelp(key: string): string {
  return SI_HELP_INDEX.get(key) ?? "";
}

/** Todas as chaves registradas — útil para testes e auditoria de cobertura. */
export function listSiHelpKeys(): string[] {
  return [...SI_HELP_INDEX.keys()].sort();
}
