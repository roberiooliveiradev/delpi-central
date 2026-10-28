# Portal Engenharia — Visão geral: contrato de experiência e wireframes (F3.Overview.G0)

> **Estado:** `DESIGN_CANDIDATE` — especificação de produto/UX; não comprova implementação, integração, disponibilidade, aprovação técnica de KPIs nem deploy.  
> **Data:** 2026-10-28. **Owner da experiência:** Portal Engenharia. **Owners dos dados e metas:** APIs de domínio, Strategic Indicators e sistemas oficiais correspondentes.  
> **Referências visuais:** capturas de Visão geral do Portal Comercial, Dashboard Engenharia e Visão geral atual do Portal Engenharia fornecidas pela Coordenação.  
> **Referências de código verificadas:** `plugins/commercial/src/features/overview/OverviewPage.tsx`, `plugins/dashboard-engineering/src/pages/DashboardEngineeringPage.tsx`, `components/EngineeringFilters.tsx`, `hooks/useEngineeringFilters.ts`, `api/engineeringApi.ts`, `plugins/engineering/src/features/overview/OverviewPage.tsx`.  
> **Autoridades documentais:** `KPI-FICHAS.md`, `WIREFRAMES.md`, `ARCHITECTURE.md`, `SCOPE-OWNERSHIP.md`, `PERFIS-E-PERMISSOES.md`. Quando um wireframe histórico divergir de fichas canônicas, não converter o wireframe em regra de domínio.

## 1. Objetivo e delimitação

A Visão geral deve responder **“Como está a Engenharia no período selecionado?”**, mostrando indicadores com valores, origem, unidades, metas/IDD quando autorizados, estado de disponibilidade e recortes que as fontes suportem. A referência **visual** é a Visão geral do Portal Comercial; a referência **funcional** é o Dashboard Engenharia existente. O Portal Engenharia deverá ser o consumidor de uma composição governada na `engineering-api`, jamais importar implementação de outro MFE ou acessar diretamente `/apps/api-delpi` e bancos proprietários.

A atual Visão geral (uma métrica isolada e seis cards de estado de fontes) será substituída por **Hero com filtros → KPIs → aprofundamento autorizado**. Status de fonte não deve dominar a interface e não pode ser disfarçado como valor zero.

**Não confundir:** acesso a indicadores, acesso ao Portal TRANSFORMA+ e futuro acesso ao módulo LMPs no prazo são permissões e contratos distintos.

## 2. Decisões de UX aprovadas nesta especificação

1. Manter Top Bar existente da Engenharia: **Início | Visão geral | Ajuda**, busca, favoritos e avatar, usando `@delpi/plugin-ui`. Manter o mesmo container/padding, tokens claro/escuro e semântica responsiva dos portais maduros.
2. Hero: eyebrow `PORTAL ENGENHARIA`; título `Visão geral`; subtítulo curto; ação `Atualizar` com ícone, loading e prevenção de refresh duplicado. Filtros aparecem **dentro do Hero**, seguindo a referência Comercial.
3. Filtros candidatos: período rápido, data inicial, data final, competência e unidade operacional; somente ofertar controles efetivos que os contratos permitam. **O filtro de unidade não altera KPIs estratégicos consolidados do SI**. Pode filtrar uma subseção operacional se suportado pelo owner, com rótulo de escopo explícito.
4. Grade principal: seis KPIs já presentes no Dashboard Engenharia, agrupados por LMP e TRANSFORMA+. Valores e metas são fornecidos pelos owners, não recalculados no MFE.
5. Área final: **LMPs no prazo** e **TRANSFORMA+** com regras diferentes. LMPs no prazo será futuramente módulo interno do Portal Engenharia e **não deve hoje redirecionar diretamente** ao dashboard legado. Link ao Portal TRANSFORMA+ só aparece quando a Core comprovar acesso efetivo à rota oficial; sem acesso, não mostrar CTA, mas preservar indicadores autorizados.
6. Não introduzir novas permissões, regras de prioridade, score, métricas artificiais, publicação de desenhos, funcionalidades de EVA ou migração de outros portais neste contrato.
7. Estados de erro por seção e KPI, com retries seguros e parcialidade honesta. Não converter `403` em “sem indicadores”.

## 3. Wireframe WF-OV-01 — Desktop ≥ 1200 px (estrutura, não medidas canônicas)

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Início]  [Visão geral •]  [Ajuda]        [Buscar] [☆ Favoritos] [foto/usuário]           │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│  PORTAL ENGENHARIA                                                 [⟳ Atualizar]           │
│  Visão geral                                                                               │
│  Indicadores oficiais de Engenharia — LMPs e TRANSFORMA+                                   │
│  ────────────────────────────────────────────────────────────────────────────────────────  │
│  Período rápido: [Hoje] [Semana] [Este mês] [Mês anterior] [Trimestre] [Ano] [Personalizado]│
│  [Data inicial      ▾] [Data final       ▾] [Competência      ▾] [Unidade*       ▾]       │
│  * Unidade para métricas operacionais com suporte comprovado; SI estratégico consolidado   │
└────────────────────────────────────────────────────────────────────────────────────────────┘
  INDICADORES                                                    Período / escopo / fonte
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│ % LMP dentro do prazo   │ │ Lead time médio         │ │ Total de propostas      │
│ [valor oficial]         │ │ [valor] dias úteis      │ │ [quantidade]            │
│ Meta/IDD se aplicável   │ │ Fonte / período         │ │ Fonte / período         │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│ Ganhos brutos           │ │ Soluções implementadas  │ │ ROI médio TRANSFORMA+   │
│ [moeda / período]       │ │ [quantidade]            │ │ [multiplicador]         │
│ Meta/IDD se aplicável   │ │ Fonte / período         │ │ Fonte / período         │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
  EXPLORAR / APROFUNDAR
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│ LMPs no prazo                     │ │ TRANSFORMA+                       │
│ Futuro módulo interno da          │ │ Indicadores já mostrados acima;   │
│ Engenharia: SEM link ao legado    │ │ [Abrir Portal TRANSFORMA+] só se  │
│ [Integração futura / sem CTA]     │ │ acesso efetivo Core comprovado    │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

**Comportamento:** a largura útil, os gutters, os cards e o Hero seguem o sistema visual do Comercial e os tokens do `plugin-ui`. O layout é uma referência de hierarquia, não especifica pixel fixo.

## 4. Wireframe WF-OV-02 — Tablet e Mobile

```text
┌───────────────────────────────────────┐
│ [Menu/nav adaptativa] [Busca] [Avatar]│
├───────────────────────────────────────┤
│ PORTAL ENGENHARIA                     │
│ Visão geral                           │
│ Indicadores de Engenharia             │
│ [⟳ Atualizar]                         │
│ Período rápido (scroll acessível)     │
│ [Data inicial                        ]│
│ [Data final                          ]│
│ [Competência                         ]│
│ [Unidade operacional*                ]│
├───────────────────────────────────────┤
│ INDICADORES                          │
│ ┌───────────────────────────────────┐ │
│ │ % LMP dentro do prazo             │ │
│ │ [valor / meta / contexto]         │ │
│ └───────────────────────────────────┘ │
│ ┌───────────────────────────────────┐ │
│ │ Lead time médio ...               │ │
│ └───────────────────────────────────┘ │
│ [demais KPIs empilhados]              │
├───────────────────────────────────────┤
│ EXPLORAR                              │
│ [LMPs no prazo • futuro]              │
│ [TRANSFORMA+ • CTA apenas com grant]  │
└───────────────────────────────────────┘
```

**Responsividade:** 3 colunas desktop quando a largura do container comportar; 2 em tablet e 1 no mobile, conforme breakpoints canônicos. Sem rolagem horizontal da página. Controles e cards preservam navegação por teclado, alvos de toque e foco visível.

## 5. Anatomia de cada região

### 5.1 Top Bar e Breadcrumb

Top Bar permanece como implementada no Portal Engenharia. Breadcrumb `Início / Visão geral` apenas se o padrão existente o exigir e sem duplicar navegação. Avatar do usuário usa perfil oficial da Core; foto quando disponível, iniciais como fallback. Não criar identidade paralela.

### 5.2 Hero e filtros

- **Título:** `Visão geral`; **eyebrow:** `PORTAL ENGENHARIA`; **descrição:** `Indicadores oficiais de Engenharia — LMPs e TRANSFORMA+`.
- **Ação Atualizar:** ícone `RefreshCw`; acessível; loading e disabled ligados ao refresh real; preserva dados anteriores quando possível.
- **Período rápido:** presets candidatos `Hoje / Esta semana / Este mês / Mês passado / Este trimestre / Este ano / Personalizado`. Verificar função canônica e natureza temporal de cada KPI antes de habilitar; preservar semântica do `useCompetenceLinkedDates` do dashboard.
- **Data inicial e final:** intervalo válido, data inicial ≤ final, sem datas indevidas; a apresentação/serialização para LMP e TRANSFORMA+ deve seguir o adapter de cada owner.
- **Competência:** mês/ano vinculado ao intervalo conforme contrato existente. Evitar ciclos em sincronização com query params e mudança de período.
- **Unidade operacional:** `Consolidado` como referência inicial. Só permitir filial para KPIs operacionais com contrato suportado. A apresentação estratégica SI continua consolidada (não reproduzir score por filial).
- **URL/share:** filtros podem ser refletidos na URL apenas com parâmetros públicos e canônicos, sem tokens; preserve refresh e navegação.

### 5.3 Grid de indicadores (seis cards)

| ID de apresentação candidato | KPI | Fonte de realizado / regra | Unidade | Escopo e ressalvas |
|---|---|---|---|---|
| `lmp_on_time` | % LMP dentro do prazo | LMP/dashboard oficial; regra do owner | % | Meta/IDD somente se SI autorizar; ID SI `engineering-projects-on-time` tem nome de negócio “Projetos Concluídos no Prazo”, não assumir equivalência sem validar o mapeamento |
| `lmp_lead_time` | Lead time médio | LMP/dashboard oficial | dias úteis | Natureza temporal definida pelo owner |
| `lmp_total_proposals` | Total de propostas | LMP/dashboard oficial | quantidade | Não misturar propostas e LMPs sem semântica validada |
| `transforma_gross_savings` | Ganhos brutos TRANSFORMA+ | Provider TRANSFORMA+ / SI conforme contrato | R$ ou unidade oficial | Meta/score SI `engineering-transforma-plus` apenas em escopo canônico consolidado |
| `transforma_solutions` | Soluções implementadas | TRANSFORMA+ oficial | quantidade | Não inferir ranking/status |
| `transforma_roi` | ROI médio TRANSFORMA+ | TRANSFORMA+ oficial | multiplicador `×` | Não recalcular ROI no frontend |

Estes seis KPIs constam da implementação vigente de `DashboardEngineeringPage`. **O status de cada adapter da nova `engineering-api` continua `TO_INVENTORY`**, até contrato e testes de implementação.

**Card padrão:** título, ícone semântico, valor principal, unidade, contexto (período e escopo), fonte/atualização, meta/IDD apenas quando aplicável e comprovado, tooltip de ajuda e estados loading/empty/partial/forbidden/unavailable. Não mostrar meta ou tendência fictícias. Os indicadores estratégicos referenciados em `KPI-FICHAS.md` devem preservar owner, ID, meta, direção e score, sem recálculo no MFE.

### 5.4 Rodapé “Explorar / Aprofundar”

**LMPs no prazo:** módulo **futuro** dentro de `/apps/engineering`; o destino concreto e sua permissão ainda serão definidos no contrato de migração. Nesta fase, mostrar card informativo `Integração futura` sem CTA navegável. **Proibido** adicionar redirecionamento direto ao dashboard legado `/apps/dashboard-engineering` como solução final.

**TRANSFORMA+:** card informativo sobre acesso ao portal oficial. Somente renderizar link/CTA se a **Core** confirmar permissão efetiva de usuário para a rota oficial existente. O frontend não deduz permissão do JWT nem do sucesso na obtenção de indicadores. Se não autorizado, **omitir o atalho**; indicadores já autorizados permanecem. Se o app/rota oficial não for comprovado, não renderizar link mesmo com permissão semelhante.

**Não confundir** atalho para portal com acesso aos dados; ambos exigem validações próprias.

## 6. Dados, APIs e ownership

```text
Keycloak (identidade) → Core (acesso efetivo engineering.access + escopo de rota)
                                    ↓
Portal host → MFE plugins/engineering / Visão geral
                                    ↓
                            engineering-api (BFF)
                        ↙           ↓            ↘
           Owner LMP/api-delpi  Owner TRANSFORMA+  Strategic Indicators
                 (leitura/escopo/autorização oficiais; sem DB cruzado)
```

A `engineering-api` deve expor um contrato dedicado **a definir** para a Visão geral (por exemplo `GET /v1/overview` com parâmetros governados), **não presumir que já exista**. O `GET /v1/home` atual não contém os seis KPIs estratégicos/operacionais nem os filtros necessários; não deve ser estendido de maneira oportunista.

Antes de implementar: inventariar endpoints oficiais para LMP summary, TRANSFORMA summary e SI scores/metas, audiences JWT/delegação, Core effective permissions, filtros, período, timeout, custo de fan-out, validade dos números e contratos de erro. O BFF agrega e apresenta, **não recalcula** regras de LMP, ROI, metas, notas ou scores.

**Segurança:** somente JWT humano autorizado; proibição de `X-Delpi-Service-Token` em chamadas personalizadas de usuário, conforme F2a.R1. Acesso de recurso é decidido pelo owner; `engineering.access` não concede universalmente `ENGINEERING_LMP_ACCESS`, indicadores de terceiros ou acesso ao Portal TRANSFORMA+.

**Resposta candidata** (não contrato aprovado): `schema_version`, `generated_at`, `filters` com escopo efetivo, `status` agregado, `indicators[]` com `id,label,value,unit,scope,period,source,availability,goal?,idd?`, `errors` sanitizados e sem dados ocultos. Versão, endpoints, enum e formato final devem ser congelados no Contract Gate.

## 7. Estados e interações

| Situação | UX obrigatória |
|---|---|
| Primeira carga | Skeleton nos cards e controles seguros; não renderizar `0` |
| Refetch após filtro | Loading contextual, cancelamento de requisição anterior, evitar mistura de períodos |
| Dados completos | Indicadores reais com origem, escopo e período |
| Uma fonte indisponível | `partial` global e card afetado `unavailable`; dados restantes preservados |
| Fonte sem registros | `empty` legítimo, não presumir valor zero |
| Sem permissão em indicador | `forbidden`, sem valor, meta ou informação sensível |
| Token expirado | Fluxo canônico de sessão do Portal; sem refresh próprio |
| Erro de contrato | Falha explícita e observável, sem usar dado stale como atual |
| Troca de usuário/unidade/período | Descartar requests anteriores, revalidar escopo, nenhuma mistura de identidades |
| Sem acesso ao portal TRANSFORMA+ | Omitir link; manter KPIs que tenham autorização independente |
| LMPs no prazo ainda não migrado | Card informativo futuro, sem redirecionamento legado |

**Acessibilidade:** texto e estados não dependem apenas de cor; labels de filtros, aria-live no loading, tooltip acessível, teclado, foco, contraste e formato pt-BR. **Temas:** tokens do `@delpi/plugin-ui` e mesmo padrão de layout do Comercial, sem copiar CSS comercial.

## 8. Jornada e behavior de filtros

1. Abrir Visão geral → carregar defaults canônicos (sem inventar filtro).
2. Alterar período rápido → resolver competência/datas por política oficial; invalidar request anterior.
3. Alterar competência → aplicar vínculo oficial das datas; atualizar KPI somente onde filtro suportado.
4. Alterar unidade → mostrar escopo operacional na UI; indicadores SI estratégicos permanecem consolidados (rótulo explícito); não apresentar falsas comparações por filial.
5. Atualizar → executar novo fetch com os filtros efetivos, exibindo progresso e mantendo acesso fail-closed.
6. Abrir destino autorizado → navegação pelo host/Portal, sem URL gerada por dados inseguros.
7. Exibir help → explicar indicadores estratégicos vs operacionais, realizado/meta/IDD, escopo consolidado e fonte.

## 9. Reuso de componentes

Reutilizar `PageHero`, `ActionButton`, componentes de filtros/period presets realmente disponíveis, `DashboardKpiCard` ou card semântico do kit, `SectionCard`, `EmptyState`, `PagePath`, `Tooltip`, etc., **após confirmar exports vigentes**. A composição do Comercial é referência; não importar seus use cases, stores ou CSS. Se um componente genérico faltar, aplicar Abstraction Gate com owners/consumers e regressão.

Não migrar `plugins/dashboard-engineering` nesta fase; seu comportamento é referência para contrato e paridade. A migração futura do módulo LMPs terá decisão própria de owner, rota, compatibilidade e cutover.

## 10. Critérios de aceite de design e implementação (gates separados)

**Design / UX**
- D01: Wireframes desktop e mobile aprovados; layout alinhado ao Comercial e com personalidade de Engenharia.
- D02: Hero com período, competência, datas e unidade apenas conforme capacidades verificadas.
- D03: Seis KPIs apresentados em cards responsivos; valor, unidade, período, fonte, estado e metas/IDD sem invenção.
- D04: Atalhos finais distintos: LMPs futuro interno; TRANSFORMA+ somente com permissão Core.
- D05: Loading/empty/partial/forbidden/unavailable, temas claro/escuro e a11y documentados.

**Contrato / segurança**
- C01: Owners e endpoints reais inventariados para cada KPI e score.
- C02: Contrato do BFF fechado antes de implementar; request/response, AuthN/AuthZ, erros, limites, compatibilidade, observabilidade e postconditions.
- C03: Sem acesso direto do MFE às APIs de domínio, sem DB cruzado e sem service token privilegiado em chamada personalizada.
- C04: SI mantém seus dois IDs canônicos e scope consolidado; nenhuma nota/meta recalculada no MFE.
- C05: Filtros suportados por owner; diferenças entre dados estratégicos e operacionais explícitas.
- C06: Link TRANSFORMA+ somente por rota oficial e effective permissions na Core.
- C07: Gate de migração LMPs formalizado, sem link direto para app legado.

**Execução futura**
- E01: Testes de filtros, serialização, período, unidade, authz, nulls, falha parcial e paridade no mesmo recorte.
- E02: Testes de regressão F1–F3; visual desktop/mobile claro/escuro; auditorias e build.
- E03: Deploy canônico e smoke autenticado, evidências no SHA e rollback; **nenhuma dessas execuções é comprovada por este documento**.

## 11. Riscos, gaps e decisões pendentes

| Item | Estado | Próxima prova |
|---|---|---|
| Seis KPIs exibidos no Dashboard Engenharia | `PROVEN` no código do dashboard | Contratos de API e semântica final |
| Fonte de meta/score SI e IDs | `PROVEN` na ficha de indicadores | AuthZ, API HTTP e critérios de recorte para BFF |
| Filtro de unidade global sobre SI | **NÃO APROVADO** | SI consolidado; qualquer alteração exige decisão do owner |
| Rota e contrato `GET /v1/overview` | `TARGET` | Contract Gate |
| Migração futura “LMPs no prazo” para dentro da Engenharia | `PLANNED` | Owner, rotas, autorização, testes e plano de cutover |
| Permissão de atalho ao Portal TRANSFORMA+ | `TO_INVENTORY` | Manifest, rota e effective permissions Core |
| Filtros rápidos | `DESIGN_CANDIDATE` | Presets, datas e competência canônicos |
| Gráficos detalhados e exportação | `PLANNED` / fora deste design inicial | Contratos e necessidade real |
| Paridade de valores/metas/IDD com dashboard atual | `PENDING` | Comparação por período/unidade/fonte, com aceite do owner |
| Visual produtivo autenticado | `TEST_NOT_RUN` neste documento | Screenshots e QA em sessão governada |

## 12. Plano de implementação subsequente, não executado aqui

- **G0:** validar wireframe e as decisões de UX com Coordenação.
- **G1:** inventário owner → fontes → filtros → permissões, incluindo strategic-vs-operational.
- **G2:** congelar contrato do BFF, schemas, erros, unidades/escopos e metas.
- **G3:** implementar adapters oficiais + caso de uso de agregação com timeout e fail-closed.
- **G4:** refatorar `plugins/engineering/src/features/overview/OverviewPage.tsx` para Hero/filtros/KPIs/atalhos condicionais.
- **G5:** testar contract, security, dados, paridade, visual e a11y.
- **G6:** documentar evidências e implantar pelo fluxo canônico com gates de autorização.
- **G7:** validar visualmente em produção e registrar resultado; não ativar links sem acesso efetivo.

**Critério de fechamento desta especificação:** documento versionado e rastreável; estado permanece `DESIGN_CANDIDATE` até validação explícita da Coordenação. Nenhuma implementação ou grant fica autorizada pela mera criação do documento.
