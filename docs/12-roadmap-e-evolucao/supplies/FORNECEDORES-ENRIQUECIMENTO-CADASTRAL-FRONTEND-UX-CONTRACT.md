# UX contract — revisão assistida de dados públicos de fornecedores (SA2)

> **TARGET / DOCUMENTED — NÃO IMPLEMENTADO.** Complemento ao [fluxo funcional e backend candidato](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-FLUXO-CONTRATO.md) no PR #106. Especificação de páginas, componentes e critérios para discussão/contract freeze. Não autoriza criação de rota, UI, endpoint, provider, job, DB, deploy nem PUT. A documentação não prova existência dos componentes no HEAD. **Nenhum wireframe desta especificação deve ser confundido com screenshot de runtime.**

## 1. Princípios de produto, escopo e navegação

Objeto desta proposta: **fornecedores SA2**, não clientes SA1. Abrir revisão assistida a partir da **ficha do fornecedor** já existente `/apps/supplies/suppliers/:code/:store`, sem substituir os modos consulta/create/edit/review existentes.

A operação inicial é **sob demanda** e usa CNPJ do fornecedor do cadastro, sem permitir busca arbitrária por documentos de terceiros. Consulta a fonte pública é **read-only**. Aceitar ou recusar sugestão é **decisão sobre proposta**, sem alterar SA2. Apenas revisão final e PUT existente, com AuthZ/gate/tracking aplicáveis, podem gravar; PUT fica indisponível enquanto gates OFF.

A composição preferida é **ficha existente → painel de comparação contextual (rota filha somente se justificada por UX/URL/F5) → revisão existente**. Não gerar cinco páginas independentes só porque há cinco estados. O inventário de rotas/manifest no HEAD deve decidir entre painel na ficha, drawer do kit ou subrota; por padrão **não criar nova rota**. Em caso de revisão longa, filtros/histórico/permalink ou necessidade de F5, uma rota candidata é `/apps/supplies/suppliers/:code/:store/enrichment/:reviewId`, **TARGET não aprovada como manifest**.

### Superfícies detalhadas

| ID | Superfície | Finalidade | Rota proposta | Reuso |
|---|---|---|---|---|
| UX-01 | Ficha de fornecedor / ponto de entrada | Consultar, verificar fonte/recência, iniciar comparação | existente `/suppliers/:code/:store` | Header, SectionCard, ActionButton/Badge |
| UX-02 | Revisão de divergências | Comparar valor atual/externo e decidir por campo e lote | inicialmente painel no detalhe; subrota apenas se comprovada | SectionCard, campos de comparação, filtros, status |
| UX-03 | Confirmação de decisão em lote | Prévia explícita do alcance de aceitar/recusar pendentes | Modal do kit, sem rota | modal + lista/counter |
| UX-04 | Preparação/revisão do draft aceito | Ver diffs elegíveis que serão enviados, conferir conflitos antes PUT | modal de revisão existente de EDIT | diff-only + confirmação |
| UX-05 | Histórico de consultas/decisões | Exibir auditoria autorizada, recusa, consulta, recência e resultado | seção/aba contextual (sem rota por padrão) | tabela paginada ou cards mobile |
| UX-06 | Estados auxiliares | sem diferenças, provider indisponível, parcial, conflito, 403 etc. | dentro das superfícies anteriores | EmptyState, Alert, loading, help |

Histórico persistente (UX-05) depende da decisão D-07 e contrato do backend: **não exibir auditoria fictícia nem prometer histórico entre sessões sem persistência comprovada**.

## 2. Arquitetura de composição UI — kit-first

MFE `plugins/supplies` compõe dados vindos exclusivamente de `supplies-api`. Não consumir provider ou `api-delpi` diretamente; não resolver permissão final. CSS local dentro de `.dashboard-supplies-portal`. Labels e Help PT-BR; identifiers técnicos em inglês. Temas dark/light via tokens do `@delpi/plugin-ui`.

| Responsabilidade conceitual | Candidato de kit a inventariar no HEAD | Composição específica (somente se faltar) | Comportamento |
|---|---|---|---|
| Ponto de entrada e status | PageHero, SectionCard, ActionButton, StatusBadge | `SupplierEnrichmentEntry` | ação somente quando acesso disponível, resumo e última consulta real |
| Container da comparação | SectionCard, PagePath, loading/empty/error | `SupplierEnrichmentReview` | estado de consulta, proveniência, filtros e lista |
| Resumo e contadores | Badge/StatusBadge, alert | `EnrichmentSummary` | N divergentes, elegíveis, protegidos, indisponíveis, pendentes |
| Proveniência | Badge, tooltip/Help | `EnrichmentSourceInfo` | provider, horário, data/versão, confiabilidade/limitações |
| Linha de divergência | FieldLabel/HelpTooltip, card/grid | `EnrichmentFieldComparison` | current/proposed, normalização, eligibility, reason, decisão |
| Agrupamento | SectionCard | `EnrichmentFieldGroup` | identificação/endereço/contato/fiscal conforme campos mapeados |
| Seleção por campo | ActionButton/segmented control | `EnrichmentFieldDecision` | aceitar/recusar/adiar, status acessível e motivo |
| Ações em lote | ActionButton/ModalShell | `EnrichmentBulkActions` | conta pendentes elegíveis e preview explícito |
| Modal de decisão | ModalShell/checkbox/text-area kit | `EnrichmentBulkReviewDialog` | listar campos e impactos sem executar PUT |
| Preparar PUT | ModalShell/review table existente | adapter de draft, evitar modal duplicado | nunca gravar ao aceitar sugestão |
| Histórico | DataTable/CompactPagination/EmptyState | `EnrichmentHistory` se state aprovado | eventos de decisão e operação, acesso restrito |
| Erros/estados | ScreenLoading/EmptyState/AlertQueue | `EnrichmentStateView` | 401/403/404/409/410/429/5xx, partial, offline |
| Ajuda | FieldLabel, HelpTooltip, SectionHintLabel | metadata das labels | o próprio texto é alvo (hover/focus/touch), não ícone ? |

**Inventário obrigatório antes da implementação:** exports reais, props, acessibilidade, MFE atual, rotas, teste e Help; o nome de um componente nesta tabela é *conceitual*, não evidência de export ou ordem para criar novos arquivos. Componentes com regras de fornecedor não entram no kit genérico.

## 3. Wireframes desktop e mobile

### UX-01 — Ficha e ponto de entrada

```text
Fornecedores > 000001 / 01
[Fornecedor · Código/Loja] [Status ERP]
[Identificação] [Endereço] [Contato] [Fiscal] [Financeiro]  (estrutura atual)
┌ Dados públicos / atualização assistida ───────────────────────────────┐
│ Consulte informações estruturadas do CNPJ para comparar com o ERP.    │
│ Fonte: [fonte autorizada/indisponível] · Consulta: [data real ou —]    │
│ [Consultar dados públicos]  [Ver última revisão*]                      │
└────────────────────────────────────────────────────────────────────────┘
*apenas quando backend comprovar revisão armazenada e acesso autorizado
```

Campo CNPJ/CPF já está na identificação e é protegido no EDIT; a ação não muda o documento nem executa gravação. Se fornecedor CPF ou provider não elegível: mostrar motivo e opção desabilitada/ausente conforme regra e acessibilidade.

### UX-02 — Comparação no desktop

```text
Fornecedores / fornecedor / Dados públicos
[Voltar à ficha]  [Atualizar comparação]
Fonte X | Consultado em dd/mm/aaaa hh:mm | Comparação id/revisão (se exposto)
N diferenças · X elegíveis · Y protegidas · Z sem evidência
[Todos] [Divergentes] [Pendentes] [Decididos] [Não aplicáveis]
┌ IDENTIFICAÇÃO ─────────────────────────────────────────────────────────┐
│ Campo          ERP atual         Fonte pública     Estado        Ações  │
│ Razão social   Atual A           Proposta B        Diferente [Aceitar]  │
│                                                       [Recusar]        │
│ Nome fantasia  Nome interno      Nome da fonte     Revisar equivalência│
│ CNPJ           ***.***           ***.***           Protegido (sem CTA) │
├ ENDEREÇO ─────────────────────────────────────────────────────────────┤
│ CEP            00000-000         11111-111        Diferente [Aceitar]   │
│ Cidade/UF      Cidade A          Cidade B          Conciliação pendente │
└────────────────────────────────────────────────────────────────────────┘
2 sugestões elegíveis pendentes
[Recusar todas pendentes] [Aceitar todas pendentes] [Revisar aceitas]
```

Proposta ilustrativa; não representar campo sem fonte comprovada como elegível. Cada linha mostra **valor atual**, **valor sugerido**, origem/data, normalização se relevante, diferença, política de elegibilidade e decisão. Mostrar `Não informado pela fonte` ≠ `vazio no ERP`. Campo informativo/protegido não pode ser selecionado no lote.

### UX-02 mobile

```text
Dados públicos | Fonte · data
2 divergências elegíveis
[Filtrar]
┌ Razão social ────────────────┐
│ ERP atual: ...               │
│ Fonte externa: ...           │
│ Diferente · elegível         │
│ [Aceitar] [Recusar]          │
└──────────────────────────────┘
┌ CEP ─────────────────────────┐
│ ERP atual: ...               │
│ Fonte externa: ...           │
│ [Aceitar] [Recusar]          │
└──────────────────────────────┘
[Decidir todas pendentes] [Revisar aceitas]
```

Botões acessíveis, sem tabela com scroll horizontal compulsório; preserve ordem DOM, labels e foco. Ações em lote não ficam ocultas por teclado virtual/sticky.

### UX-03 — Modal de decisão em lote

```text
┌ Aceitar todas as sugestões pendentes ─────────────────────────────────┐
│ Você está aceitando 2 de 5 diferenças da revisão #...                 │
│ Incluídas: Razão social; CEP                                          │
│ Excluídas: CNPJ (protegido); Cidade (não conciliada); 1 já recusada    │
│ Esta decisão NÃO altera o Protheus.                                   │
│ [Voltar] [Confirmar aceitação de 2 sugestões]                        │
└────────────────────────────────────────────────────────────────────────┘
```

Variante **Recusar todas**: mesma prévia de pendentes, com justificativa se definida pela política e CTA explícito `Confirmar recusa de N sugestões`. Não fazer CTA genérico `Confirmar`. Se nada pendente, desabilitar ação e explicar por quê.

### UX-04 — Revisão final antes PUT

```text
Revisar alterações aceitas
Campo                 ERP atual             Novo valor
Razão social          Atual A               Proposta B
CEP                   00000-000             11111-111
[Apenas preparar rascunho] [Voltar] [Salvar alterações*]
*somente quando autorização e gate de escrita efetivos, após revalidar baseline
```

Ao aceitar uma sugestão, mudar estado `ACCEPTED_FOR_DRAFT`. Reusar o modal de revisão já existente para PUT diff-only; valores externos não substituem automaticamente os digitados pelo usuário. Se campo editado manualmente conflitar com sugestão, pedir escolha explícita. `CONFIRMED` vem do tracking/GET, nunca da decisão de aceite.

### UX-05 — Histórico (condicional)

```text
Histórico de consultas e decisões
Quando              Fonte         Decisão/resumo                 Ator
Data A              Provider X    2 aceitas, 1 recusada          Usuário*
Data B              Provider X    0 divergências                 Usuário*
[Detalhes da revisão] [Próxima página]
*somente conforme escopo e política de privacidade/autorização
```

Sem fonte durável aprovada, UI-05 permanece `PLANNED_BLOCKED`, não criar placeholders persistentes.

## 4. Estados e comportamento por página

| Estado | UX-01 ponto de entrada | UX-02 comparação | UX-03 lote | UX-04 revisão | UX-05 histórico |
|---|---|---|---|---|---|
| initial | CTA consulta | placeholder orientativo | fechado | fechado | histórico ou não disponível |
| loading | bloqueio de clique duplicado | skeleton e progresso não enganoso | bloquear ações | loading somente se revalidando | loading paginado |
| match/zero diferença | resumo nenhuma diferença | EmptyState com fonte/data | botão desabilitado | sem diff | consulta registrada se aprovada |
| differences | CTA ver revisão | linhas por seção + contador | permitir apenas pendentes elegíveis | exibir aceitas | decisões após persistência |
| partial external | aviso de cobertura | `SOURCE_MISSING` em campos afetados | exclui não elegíveis | excluir campo sem prova | marcar consulta parcial |
| source unavailable | erro + tentar novamente | manter última revisão **identificada como stale** | não decidir novo snapshot | não gravar com base stale | histórico legível se autorizado |
| 401 / 403 | autenticar / acesso negado | não revelar dados da fonte | fechar com estado seguro | sem PUT | acesso negado |
| 404 | fornecedor ausente | encerrar revisão | indisponível | indisponível | vazio/404 |
| 409 / stale | aviso de mudança ERP/snapshot | reconsultar, decisões preservadas só como histórico | não aplicar lote | exigir nova revisão | registrar conflito se política |
| 410 / expired | revisão expirada | pedir nova consulta | desabilitar | desabilitar | dados mínimos históricos |
| 429 | excesso de consultas | orientar aguardar, sem retry em loop | não aplicar novo lote | preservação local segura | manter o que existe |
| 5xx / timeout | provider indisponível | diferencia erro técnico vs ausência de dados | não gerar decisão para fonte incerta | nunca PUT automático | sem falsas entradas |
| operation ACK/UNKNOWN | não alegar cadastro salvo | aviso pós-apply | n/a | tracking confiável | vincular operation_id se houver |
| 403 PUT/gate OFF | consulta pode continuar | decisões read-only/draft conforme policy | aceites sem gravar | CTA salvar desabilitado e motivo | decisões auditadas separadamente |

## 5. Contrato conceitual de props/estado — sem implementação

```ts
// Conceitual / TARGET: interfaces não fazem parte do código no HEAD.
type FieldComparisonState =
  | "MATCH" | "DIFFERENT" | "SOURCE_MISSING" | "CURRENT_MISSING"
  | "NOT_COMPARABLE" | "PROTECTED" | "UNSUPPORTED" | "ERROR";
type FieldEligibility = "ELIGIBLE_TO_APPLY" | "PROTECTED" | "NOT_APPLICABLE" | "PENDING_VALIDATION";
type FieldDecision = "PENDING" | "ACCEPTED_FOR_DRAFT" | "REJECTED_SUGGESTION";
type ReviewUiStatus = "IDLE" | "LOADING" | "READY" | "PARTIAL" | "ERROR" | "STALE" | "EXPIRED";

interface EnrichmentFieldComparisonModel {
  fieldKey: string;
  label: string;
  sectionKey: string;
  currentDisplay: string | null;
  suggestedDisplay: string | null;
  comparison: FieldComparisonState;
  eligibility: FieldEligibility;
  eligibilityReason?: string;
  decision?: FieldDecision;
  provenanceId?: string;
  observedAt?: string;
}
interface EnrichmentReviewViewModel {
  reviewId: string;
  supplierCode: string;
  supplierStore: string;
  status: ReviewUiStatus;
  baselineFingerprint: string;
  sourceName: string;
  queriedAt: string;
  fields: EnrichmentFieldComparisonModel[];
}
```

**Contrato técnico a congelar com backend:** essas propriedades não autorizam confiar em `eligibility`, `baselineFingerprint` ou valores enviados pelo frontend; backend recalcula e reautoriza por campo, recurso e versão. `display` é apenas leitura; PUT usa valores tipados aceitos e campo allowlisted. A UI não implementa regras de normalização de negócio divergentes do BFF. A exibição do exemplo usa strings fictícias.

## 6. Matriz de eventos de interface e efeitos

| Evento UI | Efeito local | Chamada backend candidata | Grava SA2? |
|---|---|---|---|
| Consultar | loading e novo snapshot | POST review | **não** |
| Reabrir revisão existente | render autorizado | GET review | não |
| Aceitar campo | marcar decisão e adicionar à seleção para draft | POST decision se estado durável | não |
| Recusar campo | marcar recusa e remover do draft | POST decision se estado durável | não |
| Aceitar todas pendentes | confirmação com lista explícita, atomicidade a definir | POST bulk-decisions | não |
| Recusar todas pendentes | confirmação com lista explícita | POST bulk-decisions | não |
| Desfazer decisão | novo evento auditado se permitido | endpoint de decisão/reversão a congelar | não |
| Atualizar comparação | consulta nova + novo fingerprint | POST new review | não |
| Revisar aceitas | diff+validar estado atual | POST prepare-update | não |
| Confirmar PUT | apenas após AuthZ/gate, sem auto retry | PUT fornecedor existente | **sim** |
| Cancelar/fechar | manter descartar draft conforme política | sem chamada ou evento de abandono se contratado | não |

Não misturar `bulk decisions` com `bulk PUT`. Não emitir requests de escrita por abrir o modal ou ao receber dados de provider.

## 7. Regras de seleção e lote detalhadas

- Padrão recomendado: lote afeta **somente divergências elegíveis e ainda PENDING**, explicitamente listadas na prévia. Uma decisão individual prévia permanece intocada.
- Distinção entre "todas as divergências" e "todos os campos": o texto deve indicar **"todas as sugestões elegíveis pendentes"**. Mostrar contadores de excluídos com razão.
- Recusar é sobre proposta da versão atual, não recusar futuras mudanças externas; reconsulta com nova versão não desfaz histórico.
- Atualização do snapshot ou mudança no fornecedor entre consulta e decisão → 409/STALE; não reaplicar seleção silenciosamente.
- Em lote, registrar por-field outcomes; em falha parcial, apresentar sucessos/falhas e garantir idempotência conforme contrato. Não fingir atomicidade sem transação comprovada.
- Se 100% dos itens estiverem bloqueados/protegidos, ocultar/desabilitar ações em lote e explicar.
- Quando provider omitir campo, `SOURCE_MISSING` não é proposta de apagar o campo.
- Campo protegido não pode entrar no draft por manipulação de UI, payload ou parâmetro de bulk.
- Dependências de UF/município/IBGE devem ser tratadas em grupo de decisão se forem indivisíveis por contrato; caso contrário marcar `PENDING_VALIDATION` até congelar regra.

## 8. Help contextual e textos principais (PT-BR)

| Alvo | Texto proposto |
|---|---|
| Consultar dados públicos | Consulta fonte cadastral autorizada pelo CNPJ para sugerir atualizações. Nenhum dado é gravado automaticamente. |
| Cadastro atual | Valor lido do cadastro interno do fornecedor no Protheus. |
| Dados externos | Informação informada pela fonte consultada na data indicada; confirme antes de aceitar. |
| Divergente | Os valores diferem após comparação conforme as regras desse campo. |
| Aceitar sugestão | Coloca a sugestão no rascunho de atualização; não grava no Protheus. |
| Recusar sugestão | Mantém o cadastro atual e registra a recusa desta versão da sugestão. |
| Aceitar todas pendentes | Seleciona as sugestões elegíveis pendentes mostradas na prévia. Não altera o ERP. |
| Recusar todas pendentes | Recusa as sugestões elegíveis pendentes mostradas na prévia. Não altera o ERP. |
| Protegido | Campo não alterável pelo fluxo; exibido somente para conferência. |
| Fonte indisponível | Não foi possível consultar a origem externa; o cadastro interno permanece intacto. |
| Revisão desatualizada | O cadastro ou a comparação mudou. Faça nova consulta antes de aplicar. |
| Revisar alterações | Confira o diff do rascunho antes da confirmação de uma atualização autorizada. |
| Histórico de decisões | Consultas e decisões registradas, conforme a política de retenção e autorização vigente. |

Help deve seguir o padrão de `FieldLabel`/`HelpTooltip` na label (hover, foco e toque) já usado em fornecedores; não criar ícone ? redundante; texto só publicado após revisão de precisão por owner.

## 9. RQ/AC de frontend e matriz de testes futuros

| AC | Aceite visual/funcional | Prova requerida |
|---|---|---|
| UX-AC-01 | Ação na ficha aparece apenas conforme capability e estado autorizado | teste positive/sibling/negative |
| UX-AC-02 | Não criar página nova desnecessária | inventário de rotas + arquitetura |
| UX-AC-03 | Fonte e horário reais aparecem, sem inventar confiabilidade | contrato + teste render |
| UX-AC-04 | Valor interno e externo legíveis e distintos | snapshots de teste + a11y |
| UX-AC-05 | Campo protegido/incompatível não oferece ações | componente + teste negativo |
| UX-AC-06 | Aceitar/recusar um campo afeta só a proposta correta | testes de eventos + backend |
| UX-AC-07 | Lote só pendentes elegíveis com prévia explícita | positive/negative/bulk |
| UX-AC-08 | Decisões individuais prévias não são sobrescritas | teste misto |
| UX-AC-09 | Aceitação prepara draft, nunca PUT direto | spy de requests e contrato |
| UX-AC-10 | Recusa não altera draft de outros campos/SA2 | spy + tracking |
| UX-AC-11 | Revisão final reutiliza modal e diff-only | teste UI + payload |
| UX-AC-12 | Mudança concorrente bloqueia aplicação | teste 409 / snapshot stale |
| UX-AC-13 | Estados loading/empty/partial/error/403/404/409/410/429/5xx | fixtures e visuais |
| UX-AC-14 | Histórico só aparece se API e retenção forem aprovadas | contrato/403/paginação |
| UX-AC-15 | Responsivo dark/light e teclado/foco/toque acessíveis | screenshots + navegação |
| UX-AC-16 | Help sincronizada e específica por ação | teste help registry + manual |
| UX-AC-17 | URL/F5 funciona nas rotas existentes; se subrota criada, manifest Core atualizado via owner | smoke federado |
| UX-AC-18 | Salvar só sob gate + AuthZ, status ACK/CONFIRMED/UNKNOWN honesto | e2e negativo e tracking |
| UX-AC-19 | CSS restrito ao portal e kit-first | teste estrutural + revisão |
| UX-AC-20 | Documentação e código só evoluem após GO específico | evidências de autorização |

**Nenhum AC está implementado.** Testes UI e screenshots serão exigidos após um P0 de implementação com código/contratos no HEAD. Sem navegador autenticado: `INCONCLUSIVE`, jamais PASS por strings no bundle.

## 10. Dependências do contrato de backend e blockers para implementação

1. Definir se a revisão terá estado durável, `review_id`, expiração, retenção e acesso entre sessões; isso define se UX-05 existe.
2. Decidir fonte oficial e campos disponíveis; não desenhar ações para campos sem mapeamento aprovado.
3. Confirmar elegibilidade dos campos e PUT allowlist com limites SX3/REST.
4. Definir concorrência, versionamento, autorização de decisão e efeitos de bulk; UI nunca resolve sozinha.
5. Definir se recusa deve ser auditada e reapresentada em revisões futuras.
6. Especificar comportamento caso write gate esteja OFF e o usuário aceite sugestões.
7. Garantir Core effective permissions/unidade/resource, sem criar permissão por campo.
8. Revisar LGPD, limite de exposição de CNPJ e dados do provider, retenção, uso de fontes externas.
9. Inventariar kit `@delpi/plugin-ui`, rotas e composição atual — nomes desta spec não são exports comprovados.
10. Obter autorização explícita de implementação/page gate, com sequenciamento e DoD próprio.

## 11. Classificação final

`UX_DOCUMENTATION = TARGET / DOCUMENTED`  
`FRONTEND_IMPLEMENTATION = NOT_AUTHORIZED`  
`BACKEND_IMPLEMENTATION = NOT_AUTHORIZED`  
`NEW_ROUTES = NOT_CREATED`  
`NEW_COMPONENTS = NOT_CREATED`  
`NO_DB_CHANGES / NO_PROTHEUS_WRITES / NO_DEPLOY`

Próximo passo: inventário técnico do frontend HEAD e contract freeze conjunto frontend/backend; decisões D-01..D-10 do documento principal. Esta especificação não dá GO para implementar.
