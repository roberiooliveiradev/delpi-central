# KPI orientado a dados — Plano de produto, contratos e implantação

> **Status:** TARGET / PLANNED — especificação de comportamento desejado, **não** declaração de implementação.
> **ID:** TV-KPI-DATA-DRIVEN-COMPOSABLE-001
> **Data:** 2026-11-04
> **Autoridade de domínio:** tv-dashboard-api / PresentationMutation / DataModel e enrichment.
> **Consumidores:** plugins/tv-dashboard (authoring), plugins/tv-dashboard-presentation (palco compartilhado), plugins/public-hub (kiosk) e VISTA (capability).
> **Regra:** HEAD > código e contratos vigentes > ADRs > este plano. Este documento é uma proposta de produto/arquitetura; após aprovação e implementação, contratos técnicos reais permanecem nas fontes canônicas.
> **Decisão geral de produto:** cada parte informacional do KPI é independente em **visibilidade**, **origem do conteúdo**, **formato** e **estilo**, respeitando o tipo da propriedade.
> **Implementação:** condicionada ao inventário E0 e aos gates de contrato; não aplicar novas chaves ou schemas exemplificativos sem validação.

## 0. Como usar este documento

1. Reancorar no HEAD real, git status, Project Instructions, regras aplicáveis, responsibility-map, README de Painéis TV, tv-dashboard-api/README, capability matrix VISTA, ADR de Display Format Ownership, catálogo de PresentationMutation, READMEs dos componentes e testes.
2. Ler esta especificação **inteira** antes de gerar commits; elaborar inventário CURRENT vs TARGET e matriz de lacunas.
3. Toda linha deste plano marcada TARGET é objetivo e **não** prova de capacidade existente.
4. Localizar equivalentes e registrar **EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY** e **REUSE_DECISION=REUSE|EXTEND|NEW** para cada família de mudança.
5. Resolver causa/owner/contrato, executar etapas E0–E7 com testes/aceite; não substituir por patch de um exemplo de OEE.
6. Devolver VISTA/TV EXECUTION REPORT e atualizar este documento com evidence + links, sem promovê-lo a cópia dos schemas técnicos.

### Fontes de reancoragem

- [Documentação principal](./README.md).
- [Playbook de Excelência](./PLAYBOOK-EXCELENCIA.md).
- [MDD — Minha Delpi Deck](./MDD-MINHA-DELPI-DECK.md).
- [Owner TV API](../../../tv-dashboard-api/README.md).
- [VISTA capability matrix](../../../tv-dashboard-api/docs/integrations/vista-capability-matrix.md).
- [Presentation Ops Catalog](../../../tv-dashboard-api/docs/presentation-ops-catalog.md).
- [ADR Display Format Ownership](../../../tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md).
- Regras: .cursor/rules/plan-construction.mdc, root-cause-generalized-fix.mdc, contract-evolution-backward-compatibility.mdc, tv-dashboard-presentation-parity.mdc, tv-dashboard-persist-local-edits.mdc e responsibility-map.json.

## 1. Contexto, caso real e evidências

O pedido nasceu de uma experiência real: a VISTA inseriu no slide de laboratório um KPI com valor OEE, configurou em seguida um DataModel com realizado e meta, vinculou targetField, mas o card não exibiu numericamente a meta. O usuário quer **poder compor qualquer KPI a partir de campos de um modelo de dados**, não apenas corrigir um texto "Meta: 85%". Também quer **todos os subcomponentes ativáveis/desativáveis**, sem que vincular dados obrigue exibi-los.

**Caso de reprodução**, usar como fixture de laboratório, nunca como regra especial de negócio:

- Playlist LAB VISTA: 33b29bbf-efad-489a-bcce-ea745b71367d.
- Slide: 75884060-8bf8-456c-ba57-242b423948cb (rótulo histórico "DEMO | 4 modelos de KPI — VISTA", embora contenha cinco).
- Bloco: vista_kpi_meta_20261104.
- Model: vista_oee_dynamic_model.
- Revisão observada em leitura autenticada da VISTA: 73 (é um snapshot, não a revisão que o executor deve assumir).
- Fontes aprovadas: get_si_indicator_production_oee_realized e get_si_indicator_production_oee_meta.
- Snapshot da prévia: value=93.7 e comparable_goal=85, dependencyStatus=ok, sem transformError/runtimeErrors.
- Bindings persistidos: metrics[0].field=value; metrics[0].targetField=comparable_goal; kpiOptions.targetField=comparable_goal; comparação=target; higherIsBetter=true; colorRules gte/lt compareField=comparable_goal.
- Sintoma: comparação +8,70 p.p. e status aparecem, mas não aparece o número "85,00%" como elemento do card; hint é texto literal "Meta oficial dinâmica · últimos 30 dias".
- Outros gaps a investigar: kpiOptions.target=85 legado coexistindo com targetField; outputSchema classificando comparable_goal como string apesar de runtime numérico e changeType declarado; datas fixas 05/10–03/11 vs hint relativo; alerta de densidade de 5 KPIs no slide. São fatos do snapshot, não causas globais comprovadas.

**Evidência de código já consultada (deve ser revalidada em E0):**

- tv-dashboard-api/tv_app/application/services/data/display_format_service.py: resolve targetField, calcula comparison/status/progress e materializa kpiPresentation.targetValue, sem targetDisplay explícito no trecho inspecionado.
- plugins/tv-dashboard-presentation/src/resolveKpiPresentation.ts: usa valueDisplay, comparisonDisplay, titleDisplay, subtitleDisplay; monta hint sem meta numérica explícita.
- plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx: compõe partes title, value, hint, comparison, progress, icon e sparkline; kpiParts e contentRuns existentes.
- tv-dashboard-api/tv_app/content/presentation_ops_content.json: contratos existentes para metrics[].targetField, targetAggregation, colorRules.compareField, kpiOptions.titleField/subtitleField e modelId.
- O playbook documenta textProjection, dataRef, contentRuns[].dataRef e texto misto. **Não assumir** que cada um já opera dentro de todas as partes de KPI.

Estados: bindings atuais e prévia **PROVEN no snapshot consultado**; ausência de meta visível **PROVEN na captura fornecida**; solução completa, UI de todas as partes e paridade após correção **TARGET**.

## 2. North Star, não objetivos e invariantes

### North Star

**Um DataModel com N campos e M linhas pode alimentar múltiplas partes de um ou vários KPIs**, com projeções/agregações tipadas e autorizadas. Cada parte informacional escolhe *o que exibir*, *de onde vem*, *como formatar*, *se aparece* e *como se comporta em ausência/erro*.

A composição não exige uma fonte por campo; não exige duplicar motores; não obriga que todos os elementos apareçam.

### Não objetivos

- Não criar um segundo renderer, formatter, comparador de metas, motor de expressão, DSL, executor, endpoint/proxy genérico ou source of truth no frontend.
- Não implementar "meta dinâmica" por interpolação de string manual nem gravar valores runtime dentro de nativeConfig/MDD.
- Não reativar M-DELPI/script retirado ou fluxos /data/copilot/* retired.
- Não inventar políticas de negócio OEE/retrabalho por nome da rota; a direção e as unidades vêm do contrato.
- Não impor nova UI a slides legados nem fazer todos os novos campos aparecerem por default.
- Não alterar dados de produção/filiais para provar comportamento.
- Não converter estilos físicos (fontes/coords/cores livres) em fórmulas arbitrárias; apenas regras de estilo tipadas autorizadas.
- Não confundir setup do painel de edição com prova de TV real.

### Invariantes

1. Keycloak identifica; Core RBAC + PlaylistAccessService ou owner atual autorizam; tv-dashboard-api governa.
2. VISTA capability <= authenticated user capability; catalog informa, backend autoriza; write READ→PREPARE→CONFIRM se exigido→COMMIT→READ-BACK→VERIFY.
3. DataModel/Transform owner define dados; DisplayFormatService ou owner canônico define strings/estados; editor escolhe configuração; presentation package representa; public-hub não redecide.
4. Um palco canônico editor ≡ preview ≡ TV; mesmas revisões, payload e formatter.
5. Binding, cálculo, visibilidade e formatação são dimensões distintas.
6. Uma parte **oculta** não deixa de fornecer valores para comparações/regras de outras partes, quando isso estiver configurado e autorizado.
7. Ausência de valor dinâmico não vira 0; ausência de fonte não vira estado favorável; exibir "—" ou ocultar conforme política tipada.
8. Legado continua com seu visual e semântica; sem migração destrutiva.
9. Dados enriquecidos são runtime-only; MDD preserva definição portável e não snapshot de dados.
10. Não forçar um quinto KPI em tela quando a auditoria indicar densidade; este é tema distinto do contrato de dados.

## 3. Ledger de requisitos — produto alvo

| ID | Requisito | Estado no plano | Etapa | Evidência de aceite |
|---|---|---|---|---|
| RQ-01 | 1 DataModel → N campos → N propriedades | ATENDIDO_NO_PLANO | E1/E2 | mesmo model e bindings independentes |
| RQ-02 | Valor principal, meta e comparação dinâmica | ATENDIDO_NO_PLANO | E2/E3 | meta muda sem editar slide |
| RQ-03 | Título, subtítulo, hint, rótulo, data e período dinâmicos | ATENDIDO_NO_PLANO | E2/E3/E4 | campos diferentes e contexto de filtro |
| RQ-04 | Conteúdo misto literal + múltiplos campos | ATENDIDO_NO_PLANO | E2/E3/E4 | 2+ refs num único texto |
| RQ-05 | Visibilidade individual para toda parte informacional | ATENDIDO_NO_PLANO | E1/E4/E5 | toggle não apaga binding |
| RQ-06 | Formato, locale, unidade e escala canônicos | ATENDIDO_NO_PLANO | E2/E3 | percent/BRL/date/null |
| RQ-07 | Comparação, condição de cor, status e progress sem cálculo FE | ATENDIDO_NO_PLANO | E3/E5 | payload resolvido e no client recalc |
| RQ-08 | Séries/sparkline e ícones condicionais tipados quando semanticamente aplicável | ATENDIDO_NO_PLANO | E1/E6 | reuse/typed mapping ou gap explícito |
| RQ-09 | UX editor seletor literal/campo/misto/derivado por parte | ATENDIDO_NO_PLANO | E4 | fluxo de seleção/undo/F5 |
| RQ-10 | Sem coerção entre data ausente, zero, erro e fallback | ATENDIDO_NO_PLANO | E2/E3 | negativos determinísticos |
| RQ-11 | Tipo real pós-transform no outputSchema | ATENDIDO_NO_PLANO | E0/E2 | comparable_goal numeric coerente ou rationale |
| RQ-12 | Período exibido corresponde a filtros efetivos | ATENDIDO_NO_PLANO | E2/E3/E4 | fixed vs rolling test |
| RQ-13 | Preserve editor/preview/TV e layout 1080p | ATENDIDO_NO_PLANO | E5/E7 | same revision + pixels |
| RQ-14 | Backward compatibility/MDD/WS/cache | ATENDIDO_NO_PLANO | E6/E7 | round-trip e refresh |
| RQ-15 | VISTA usa operações existentes sem Action nova | ATENDIDO_NO_PLANO | E6/E7 | PREPARE/COMMIT/readback |
| RQ-16 | Segurança/filial e public payload | ATENDIDO_NO_PLANO | E0/E6/E7 | RBAC negatives |
| RQ-17 | Sem forçar visibilidade e sem perda autoral | ATENDIDO_NO_PLANO | E4/E5/E6 | legacy+hidden snapshot |
| RQ-18 | Diagnóstico honesto de contrato/runtime/visual | ATENDIDO_NO_PLANO | E0/E7 | report por evidence level |

## 4. Arquitetura CURRENT → TARGET

### CURRENT observado

~~~text
api-delpi: OEE realizado + meta
  → DataModel inputs + transforms
    → outputSchema + value/comparable_goal
      → kpiProjection.metrics[0].field / targetField
        → DisplayFormatService: kpiPresentation(value, comparison, status, progress, targetValue)
          → resolveKpiPresentation (hint textual legado)
            → DelpiKpiCard (parts/title/value/comparison/progress/hint)
              → editor/preview/kiosk
~~~

O link entre meta numérica resolvida e apresentação numérica opcional **não estava presente no trecho consultado**. Não concluir que toda propriedade dinâmica está ausente sem inventariar outros componentes.

### TARGET

~~~text
api-delpi / APIs aprovadas + escopo efetivo
  → DataModel(inputs, transform, outputSchema, contextFields)
    → BINDINGS TIPADOS DE PARTES (reutilizar contratos existentes)
      → backend resolve campo / agregação / runs / estados / erros
        → backend cria KpiPresentation resolvida:
             valor, meta formatada, título/subtítulo/rótulos/período,
             comparação, progresso, tons/regras tipados, diagnósticos
          → presentation package: paint/layout/visibilidade por parts
            ├─ editor (mesmo palco + UX de autoria)
            ├─ preview admin (TV parity)
            └─ public-hub kiosk
~~~

**Sem segundo owner**: tipagem/validação/resolução e regras semânticas no backend; renderer pode aplicar layout/visibilidade/CSS apenas com resultados tipados já resolvidos. Um fallback authoring pré-enrich só é admissível se for comportamento canônico já existente e nunca sobrescrever bake de servidor.

## 5. Modelo conceitual das partes e capacidades

Distinção fundamental:

- **Binding:** literal, campo de DataModel, texto misto por runs, valor derivado tipado (de acordo com semântica).
- **Visibilidade:** visible true/false por parte; zero acoplamento ao binding/cálculo.
- **Formato:** locale, unidade, precisão, máscaras tipadas, formato de data, fallback definido pelo owner.
- **Estilo/layout:** tipografia/cores/posicionamento/variante dentro do renderer compartilhado.
- **Estado:** ready, null, missing, incompatible, forbidden, stale/refresh etc. conforme diagnóstico tipado vigente; **não criar enum contratual sem inventário**.

| Parte | Binding TARGET | Visibilidade TARGET | Observações |
|---|---|---|---|
| card/chrome | não tem "dado" obrigatório; estilo/mapeamento tipado quando preciso | controle conforme contrato existente | contêiner não é dado |
| title | literal, campo, mixed runs | independente | título não deve ser substituído por label técnico |
| subtitle | literal, campo, mixed runs | independente | não reescrever texto manual |
| value | campo numérico/agregação/derivado tipado | independente | dados podem alimentar outras partes se oculto |
| target/meta | literal, campo ou ausência | independente da comparação | usar targetValue + formato backend; mostrar opcionalmente |
| comparison | backend delta/status resolvido, rótulo misto permitido | independente | direção maior/menor é melhor |
| status/semantic label | backend estado e rótulo | independente | não computar na UI |
| hint/texto auxiliar | literal, campo, mixed runs | independente | preservar autoria e precedence |
| date/período | campos, contextFields de filtros efetivos ou literal | independente | time zone, locale, start/end e rolling |
| labels complementares | literal, campo, mixed runs | independente | 2+ referências num mesmo texto |
| progress | numerador/denominador/meta no backend | independente | a barra pode ter clamp visual |
| sparkline | série tipada e dimensão temporal | independente | não inventar pontos ou agregações FE |
| icon / estado visual | estático ou mapping tipado a estado resolvido | independente | catálogo de ícones allowlisted |
| cores condicionais | operands literal/campo/derivado + prioridade | independente do componente pintado | resultado autoritativo backend |
| unidade/sufixo | formato canônico, potencial label dinâmico | independente onde exibido | nunca "0,85" ↔ "85%" sem escala declarada |

**Requisito normativo de produto:** *toda parte que apresenta informação* pode receber conteúdo dinâmico **quando seu tipo semântico o permite**. Isso não implica tornar cada pixel/propriedade CSS uma expressão.

**Decisões de design pendentes de E0/E1:** se meta merece part própria ou slot semântico existente; se status e período usam part dedicada ou composição via hint/runs; regra default para novo KPI. Não impor nova part sem provar inexistência de equivalente. Para legados, a meta **não deve aparecer compulsoriamente**.

## 6. Referência de dados, projeção e contratos propostos

### 6.1 Identidade e validação

Toda referência deve identificar a fonte lógica permitida (modelId), campo estável (nome de outputSchema), seletor/agregação para várias linhas, tipo/unidade e política de ausência. O servidor valida cardinalidade, disponibilidade, permissão/filial, compatibilidade de tipos e limites de custo. Não aceitar paths arbitrários, SQL/HTTP/JS ou templates executáveis.

**Primeira escolha:** estender os tipos reais de dataRef, DynamicContentSpec, contentRuns.dataRef, textProjection e kpiProjection onde aplicáveis. Campos como targetField/titleField/subtitleField já existem; não inventar um "propertyBindingEngine" concorrente para unificar por estética. A matriz de E0 decide REUSE/EXTEND.

### 6.2 Contrato de autoria — exemplo NÃO NORMATIVO

~~~json
{
  "type": "kpi_view",
  "modelId": "vista_oee_dynamic_model",
  "kpiProjection": {
    "metrics": [
      {
        "field": "value",
        "aggregation": "first",
        "targetField": "comparable_goal",
        "targetAggregation": "first",
        "comparisonMode": "target",
        "higherIsBetter": true,
        "format": "percent"
      }
    ]
  },
  "kpiOptions": {
    "comparisonMode": "target",
    "targetField": "comparable_goal",
    "higherIsBetter": true
  },
  "kpiParts": {
    "title": { "visible": true },
    "value": { "visible": true },
    "comparison": { "visible": true },
    "hint": { "visible": false },
    "progress": { "visible": true },
    "icon": { "visible": false }
  }
}
~~~

Mostra o **shape já reconhecível** de KPI; **não** especifica o futuro binding textual ou da meta visível. Semântica de part de meta deve ser decidida após E0. O contrato persistido inclui escolhas do autor, jamais valores de resolução.

### 6.3 Projeção backend — exemplo alvo NÃO NORMATIVO

~~~json
{
  "kpiPresentation": {
    "valueDisplay": "93,70%",
    "targetValue": 85,
    "targetDisplay": "85,00%",
    "comparisonDisplay": "▲ +8,70 p.p. vs meta",
    "statusLabel": "Acima da meta",
    "comparisonTone": "positive",
    "progressPct": 110.2352941176,
    "titleDisplay": null,
    "subtitleDisplay": null,
    "bindingDiagnostics": null
  }
}
~~~

**targetDisplay é nome candidato**, não contrato existente; usar propriedade equivalente se houver. Estados e labels exibidos passam por formatação/validação canônica. O renderer **não recalcula 93.7 vs 85, não decide cor e não concatena meta em porcentagem**. A meta oculta ainda pode alimentar cálculo. Para valor nulo/ausente, não usar o antigo target literal silenciosamente quando targetField está declarado, salvo semântica legada explicitamente comprovada e versionada.

### 6.4 Texto misto e período

TARGET: texto tipo "Meta do período {periodo}: {meta}" e "OEE · {filial}" deve suportar mais de um campo no **mesmo** conteúdo, incluindo contexto efetivo de filtros. Reutilizar runs/dataRef existentes; sem evaluator custom React nem linguagem livre.

- Para períodos, priorizar contextFields e filtros efetivos do modelo (ex.: início/fim/label). Datas em RFC3339/ISO na fonte devem ser formatadas pelo owner para pt-BR; distinguir fuso, data sem hora e intervalos inclusivos.
- Se o autor digita "últimos 30 dias" manualmente e a fonte usa datas fixas, a UI não deve afirmar atualização automática. Oferecer binding explícito ao rótulo do período, sem alterá-lo silenciosamente.
- Textos muito longos: quebra/truncamento e heurísticas visuais canônicas; preservar informação sem desabilitar binding.
- Regras de precedência literal/dynamic/mixed, fallback e edição inline devem ser definidas UMA vez; preservar contentRuns existentes e editor undo/redo.

### 6.5 Comparação, progresso e condições

- Operando esquerdo/direito: literal, campo compatível do mesmo DataModel ou derivado tipado autorizado.
- Operadores allowlisted e regra de prioridade existente; não executar expressão arbitrária.
- Direção higherIsBetter/lowerIsBetter governada por contrato. Maior meta nem sempre significa melhor desempenho.
- Separar **delta numérico**, **status semântico**, **comparação formatada** e **tom/cor pintado**; backend é fonte técnica.
- Percent vs percent: delta em p.p. somente quando escalas são comparáveis; ausência/null ≠ 0; divisão por zero não gera NaN/Infinity no payload.
- Barra visual pode clamp 0–100%, mas progressPct semântico pode superar 100%; estado de ausência é distinto.
- Definir comportamento de cores quando há regras explícitas vs tone padrão, sem second eval no MFE.
- Não reativar status "positivo" em KPI de meta isolada sem avaliação configurada.

## 7. Wireframes de produto (esquemáticos, não pixels nem contrato técnico)

### 7.1 Wireframe A — Card com informações selecionadas

~~~text
╔══════════════════ KPI STANDARD • TV 1080p ══════════════════╗
║  OEE • FILIAL 02                             [ícone opc.]   ║
║  93,70%                                                      ║
║  ▲ +8,70 p.p. · Acima da meta                                ║
║  ███████████████████████░░  [progresso opcional]              ║
║  Meta oficial do período:                        85,00%       ║
║  05/10/2026 – 03/11/2026  [período opcional/dinâmico]        ║
║  Observação derivada/literal/mista [hint opcional]            ║
╚══════════════════════════════════════════════════════════════╝
~~~

O campo "Meta: 85,00%" deve ser **resolvido**, não string hardcoded. Não existe obrigação de exibir todas as linhas. O wireframe representa **uma combinação de toggles**.

### 7.2 Wireframe B — Mesma métrica com meta oculta

~~~text
╔══════════════ KPI COMPACT • APENAS 2 PARTES ════════════════╗
║  OEE • FILIAL 02                                             ║
║  93,70%                                                      ║
╚══════════════════════════════════════════════════════════════╝

Mesmo com a meta oculta, targetField=comparable_goal pode continuar
sendo usado por regras de cor, comparação/progresso SE essas partes
estiverem habilitadas. Ocultar a meta não apaga seu binding.
~~~

### 7.3 Wireframe C — Inspector de autoria, uma propriedade por vez

~~~text
┌────────── FORMATAR KPI ────────────┬───────── DADOS ─────────┐
│ Elementos do KPI                   │ Modelo conectado        │
│ [x] Card   [x] Título              │ Qualidade / OEE         │
│ [x] Valor  [x] Meta                │ Campos:                 │
│ [x] Comparação [ ] Progresso       │  • value (number/%)     │
│ [ ] Ícone  [ ] Sparkline           │  • comparable_goal (%)  │
│ [x] Período [ ] Subtítulo          │  • nome (text)          │
│ [x] Texto auxiliar                 │  • filtro/data (date)   │
│                                    │                        │
│ Parte selecionada: META            │                        │
│ Exibir: [x]                        │                        │
│ Origem: ( ) literal (●) DataModel │                        │
│ Campo: [comparable_goal       v]   │                        │
│ Agregação: [first             v]   │                        │
│ Formato: [percent · pt-BR      v]  │                        │
│ Exemplo resolvido: 85,00%          │                        │
│ Diagnóstico: OK                    │                        │
│                                    │                        │
│ Texto/label opcional:              │                        │
│ [Meta oficial do período      ]   │                        │
│                        [Prévia]    │                        │
└────────────────────────────────────┴────────────────────────┘
~~~

As partes e tabs deverão **reaproveitar inspectors e pickers atuais**. A proposta de "Meta" como parte independente deve passar pelo gate E0/E1.

### 7.4 Wireframe D — Texto misto (título, subtítulo, hint, período)

~~~text
PARTE: SUBTÍTULO         [x] Exibir
Modo: ( ) Literal  ( ) Campo  (●) Misto
[Texto] "Meta do período "
[Campo] [periodo_label ▼]
[Texto] ": "
[Campo] [comparable_goal ▼] formato [percent ▼]

Prévia do backend:
"Meta do período 05/10/2026 – 03/11/2026: 85,00%"

[Remover run] [Adicionar texto] [Adicionar campo]
~~~

Não implementar um editor de templates novo se contentRuns/rich editor já cobre essa edição.

### 7.5 Wireframe E — Regras condicionais

~~~text
PARTE: COR DO VALOR     [x] Exibir valor
Regra #1:
Se [value ▼] [>= ▼] [campo ▼ comparable_goal]
  então [positivo ▼]

Regra #2:
Se [value ▼] [< ▼]  [campo ▼ comparable_goal]
  então [negativo ▼]

Preview autoritativo: 93,70 >= 85,00 → positivo
Fallback/ausência: [neutro / indisponível, conforme política]
~~~

Regra "mostrar valor" é independente de regra "avaliar tom". A UI apresenta resultado, nunca contém a fórmula de negócio.

### 7.6 Wireframe F — Ausência/erro de campo

~~~text
KPI • Meta: — [indisponível]
Info de authoring (não no kiosk público):
"Campo comparable_goal não disponível no outputSchema"
[Abrir DataModel] [Escolher outro campo] [Usar literal autorizado]
~~~

Não divulgar diagnóstico interno, nomes de rota, credenciais ou escopo privado no kiosk.

## 8. Fluxos e regras de UX

### Fluxo de criação

1. Usuário insere KPI/preset existente; escolhe DataModel/rota autorizada.
2. Inspector apresenta fields com tipo, unidade, origem, filtros e cardinalidade; nunca inventa um field só porque apareceu em memória.
3. Usuário seleciona uma part, alterna visibilidade e escolhe literal/dado/misto/derivado permitido.
4. Preview enriquecido solicita/consome backend autorizado; mostra valor, diagnóstico, freshness e diferenças de configuração.
5. Salva via write boundary existente, com autosave, undo/redo, CAS/revisão e reabertura F5.
6. Editor/preview/TV usam exatamente a mesma composição de palco e bundle.

### Fluxo de alteração da origem

- Mudança de valor/target/texto/período na origem → pipeline de refresh/cache oficial → payload resolvido atualizado → todas as parts vinculadas se atualizam sem alteração de configuração.
- Reordenação/rename de campo exige identity/compatibilidade contratada ou diagnóstico; nunca reconectar silenciosamente a outro campo.
- Filial/filtro não autorizado: backend nega ou exclui conforme contrato; UI não "recupera" o dado por requisição direta.

### Fluxo de ocultação

- Toggle visible=false altera apresentação apenas; não apaga targetField, dataRef, text runs nem input model.
- Ao reativar, retorna binding e configuração anterior. Testar persistência/undo/F5/MDD.
- Desabilitar comparação/progress **não** desabilita necessariamente a meta como dado. "Desconectar campo" é operação separada, explícita.

### Defaults e desenho responsivo

- **Legacy:** preservar visibilidade e aparência exatas (zero elemento novo compulsório).
- **Novo KPI:** defaults precisam de decisão de produto e evidência A/B; não impor exibição simultânea de todas as partes.
- Tipografia contextual (hero/standard/compact/scorecard), limites do card, safe areas/contraste; não mascarar conteúdo com font-size pequeno nem criar segundo renderer.
- Exibição por período e densidade: otimizar com configuração explícita e auditoria; "Q5 PASS" certifica mínimos, não distância real.

## 9. Backend — entregáveis e contrato owner

**Responsável:** tv-dashboard-api, DataModel/SlideDataResolutionService/enrichment, owner real de DisplayFormatService e PresentationMutation.

Investigar a pipeline verdadeira antes de editar. Resultado desejado:

1. A validação de binding inspeciona o outputSchema real, tipo pós-transform, agregação, contexto, permissão e unidade.
2. Resolução de valor, meta, título, subtítulo, runs mistos, período, status, progresso e regras; no mesmo enrich/model materialization sem N+1.
3. Projeção de apresentação com valores e textos prontos para pintura; targetDisplay e outros campos **somente se não existir equivalente**.
4. Erros tipados e estado ausente/indisponível sem 0 fabricado.
5. Cache/fingerprint inclui dependências de todas as partes dinâmicas e contexto de filtros.
6. Coerência de outputSchema: quando changeType(number) resulta em 85 numérico, não expor "string" como verdade técnica sem justificativa/contrato; provar causa antes de patch.
7. Na meta dinâmica, guardar precedência targetField vs target literal; documentar fallback e limpar literal legado somente se a API suportar operação segura.
8. Proteção contra loops/ref recursiva, alto custo de transform/aggregations, e vazamento public.
9. Sem quebra de operationId, sem segunda source of truth para display/progress.

**Classificar contrato antes de patch:** ADDITIVE, BEHAVIORAL, DEPRECATED ou BREAKING, com estratégia de expand/migrate/verify/contract quando necessário.

## 10. Frontend/editor — entregáveis

**Responsável:** plugins/tv-dashboard como UX/authoring. Não calcular dados.

- Painéis "Elementos do KPI" e abas Formatar KPI/Dados/Seleção sem duplicação de estado; cada parte expõe **toggle**, **origem**, **binding**, **formato**, **estilo** e **diagnóstico**, quando aplicáveis.
- Filtrar tipos (meta/valor: number, período: date/context, título: string/misto, sparkline: série).
- Multi-field picker no mesmo DataModel com rótulos amigáveis e chaves técnicas visíveis em detalhe.
- Texto misto com contentRuns / mecanismo atual; ao clicar em partes, inspector contextual; não alterar semântica de seleção de partes no palco.
- Preview apenas consome materialização autorizada. Tratamento de loading, stale, null e erro; feedback "campo inválido" sem esconder configuração.
- Undo/redo, F5, autosave, WS, concorrência e draft compatíveis.
- Acessibilidade: teclado, foco, aria-label, contraste e preview em escala TV.
- Ajuda/tooltips versionados junto com a capacidade, não antes.
- Não introduzir chamadas diretas à api-delpi, nem avaliação de conditionalColor/format em React.

## 11. Presentation package e public-hub

**Responsável:** tv-dashboard-presentation/DelpiKpiCard existentes; public-hub somente host.

- Reutilizar parts/visible e o único renderer; provar equivalência com preview admin e kiosk.
- Exibir valor de meta formatado de forma opcional, separada de hint manual se necessário e sem nova linha obrigatória em legados.
- Suportar outros textos/resolved runs sem recálculo, inclusive data/período, respeitando precedência autoral.
- CSS/typography/part positioning de KPI em todos os consumidores; não patch específico do viewer público.
- Em render com nova projeção e bundle antigo: ignorar campos opcionais sem crash; em bundle novo com projeção antiga: manter legacy fallback.
- Não recomputar percentuais/comparações em JS quando serverDisplayApplied/serverProjectionApplied estão presentes.

## 12. Segurança, portabilidade, compatibilidade, rollout

- Keycloak AuthN → Core fresh RBAC → resource/filial AuthZ → TV write boundary. JWT não é autorização final.
- VISTA uses catalog + typed ops existentes; nova typed op não gera Action automaticamente; Action Surface Gate obrigatório.
- Sem model reference cruzando playlist/filial sem autorização; data in public somente pelo contrato de apresentação.
- Persistir config/bindings/visibilidade; não persistir resolved/kpiPresentation/cache/credenciais no nativeConfig/MDD.
- MDD export/import preview≠apply; round-trip com diferentes modelos e refs portáveis; falha informativa para missing data model.
- KPIs legados (meta literal, sem meta, com hint manual, partes ocultas, fixed/auto typography, variantes) mantêm comportamento.
- Multiversão/rollout: exigir análise de producer/client old/new e rollback; feature flag somente se comprovadamente necessária, sem flag nova por reflexo.
- Sem escrita direta em slides operacionais; usar fixtures ou LAB. Deploy separado de desenvolvimento, gates antes de publicação.

## 13. Plano executável por entregas bounded (E*.S*)

### E0 — Inventário e fechamento de decisões (NO PRODUCT PATCH)

- **E0.S1** Registrar HEAD, status, regras, owner e arquivos/contratos. Lista de consumidores, shaders, tests e docs.
- **E0.S2** Reproduzir caso OEE no runtime materializado e no DOM; isolar targetDisplay, hint, typed output, fallback, render, seletor UI, período.
- **E0.S3** Matriz CURRENT vs TARGET para cada part, com evidence e equivalente já existente.
- **E0.S4** Decidir contrato mínimo, visibilidade da meta, precedence, multi-run, status/error e defaults novos, com Product/Architecture quando necessário. **STOP** se houver conflito material.
- **Gate:** ROOT_CAUSE=PROVEN para bugs; EXISTING_EQUIVALENT e REUSE_DECISION preenchidos por componente; zero patch especulativo.

### E1 — Contrato/semântica congelados

- **E1.S1** Especificar com JSON Schema/TS/Python reais as extensões compatíveis de binding por part, sem registry paralelo.
- **E1.S2** Especificar precendência literal/field/mixed/derived, hidden vs unbound, fallback/ausência, typing e formato.
- **E1.S3** Especificar UI e test matrix versionados; classification ADDITIVE/BEHAVIORAL/BREAKING.
- **Gate:** contract tests/compatibility and approval of product decisions.

### E2 — DataModel e backend de resolução

- **E2.S1** Resolver todas as refs tipadas/contexts permitidos e corrigir type post-transform se comprovado.
- **E2.S2** Formatar meta e textos/periodo; aplicar regras e diagnósticos; materialização única/sem N+1.
- **E2.S3** Testar null, zero, mismatched units, multi-row, missing/renamed field, performance, filial access.
- **Gate:** payload enriquecido completo + ausência de valores inventados.

### E3 — Projeção de composição informacional

- **E3.S1** Reutilizar textProjection/contentRuns/dataRef ou equivalentes em KPI informacional.
- **E3.S2** Suportar meta opcional, title/subtitle/hint, data/período, label/comparison; status/progress/conditional tone paint-only.
- **E3.S3** Provar formatação de vários campos na mesma string e teste metamórfico (mudar meta/data muda só outputs dependentes).
- **Gate:** contract unit/integration backend + shared consumers; sem cópia de lógica no FE.

### E4 — Inspector e UX authoring

- **E4.S1** Implementar/melhorar escolha de campo/origem/aggregator e toggles por parte.
- **E4.S2** Editor mixed-text e contexto de filtro com picker existente, sem authoring paralelo.
- **E4.S3** Undo/redo, autosave, F5, WS, keyboard, mensagens de erro; docs/tooltips.
- **Gate:** fluxos de wireframes A–F navegáveis + persistência.

### E5 — Renderer compartilhado e parity

- **E5.S1** Compor target/textos com same DelpiKpiCard/parts e styles existentes.
- **E5.S2** Confirmar current/old payload, hidden parts, variants e type visual; perf/safe-area.
- **E5.S3** Comparar editor, preview (parity=tv) e TV com mesma revisão/payload, incluindo pixels reais.
- **Gate:** sem second renderer/formatter e sem layout regressions.

### E6 — Integrações VISTA, MDD, segurança

- **E6.S1** Atualizar catálogo tipado/guia VISTA se necessário; sem nova Action por default.
- **E6.S2** MDD preview/apply round-trip; source/filter/cache fingerprint.
- **E6.S3** Negative RBAC/filial, no data leakage public, revision CAS, idempotency.
- **Gate:** VISTA PREPARE/COMMIT/readback live em LAB autorizado + negativos.

### E7 — Aceite operacional e deploy

- **E7.S1** Rodar testes/CI/architecture guardrails, build dos consumidores afetados, canary LAB e rollback plan.
- **E7.S2** Provar meta dinâmica alterada (85→95) sem editar slide: texto meta, comparison, tone, progress; repetição com ocultação de meta.
- **E7.S3** Provar data/período dinâmico, mixed content, 4 variantes, update via WS/F5, MDD, editor-preview-TV e screenshot.
- **E7.S4** Documentar gaps e evidência com SHA/deploy. Não declarar pixel verified sem captura real.
- **Gate:** ACCEPT/ACCEPT_WITH_RESIDUAL por review GPT; FAIL/INCONCLUSIVE se sem evidência-chave.

## 14. Matriz de testes mínimos / definição de pronto

| Cenário | Condição | Resultado exigido |
|---|---|---|
| Original OEE | value 93.7, targetField=85 | meta numericamente visível SE part ON, +8.70 p.p., tom correto |
| Meta muda | value 93.7, target 95 | meta 95, delta e cor negativos, sem editar slide |
| Meta oculta | same model, meta part OFF | meta não aparece; comparação/tonalidade ainda corretas se ON |
| Comparação oculta | meta ON, comparação OFF | meta aparece, comparação não |
| Título/subtítulo | campos textuais do modelo | valores atualizam sem editar slide |
| Mixed text | 2+ campos e literal | sequência, locale e ausência corretas |
| Período | datas fixas vs rolling | label corresponde aos filtros efetivos |
| Sem meta | unset | sem 0 ou comparação falsa |
| Missing target field | schema mismatch | diagnostic tipado, sem fallback silencioso |
| Zero | meta=0 | divisões protegidas; zero numérico ≠ missing |
| Negativo e menor é melhor | retrabalho | direção semântica preservada |
| Multi-row | sem aggregation explícita | rejeita ou aplica owner canônico; nunca first arbitrário |
| Unit mismatch | moeda vs percentual | validação falha controladamente |
| Conditional rule | compareField + precedência | apenas backend decide regra/status |
| Sparkline | série inexistente | ausente, não inventar pontos |
| Icon conditional | sem mapping válido | ícone estático/fallback permitido, não executa expressão |
| Legacy | literal goal/manual hint/parts hidden | aparência e resultado preservados |
| MDD | export/preview/apply isolado | config/parts/bindings preservados; sem resolved |
| AuthZ | filial/model inacessível | bloqueio backend; nenhum leak |
| Parity | same rev/payload | editor=preview=TV em DOM e pixels |
| VISTA | ops existentes | PREPARE→COMMIT→readback, sem bypass |
| Performance | várias parts um model | sem N+1, refresh/caches corretos |

**Aceite de produto:** o usuário consegue configurar um KPI inteiro com campos dinâmicos de um só DataModel, ligar/desligar partes à vontade e obter a mesma informação em editor, preview e TV; textos e meta acompanham a origem sem digitação manual; nenhuma regra duplicada no frontend.

## 15. Decisões pendentes antes de codar

| ID | Questão | Owner da decisão | Gate |
|---|---|---|---|
| D-01 | Meta visível como part própria ou slot existente? | TV API contract + presentation component + Product | E0/E1 |
| D-02 | Como se expressa binding de texto misto em partes KPI? | owner textBindingOwner / contracts | E0/E1 |
| D-03 | Defaults de visibilidade para KPIs novos? | Product/design | E0/E1; legado inalterado |
| D-04 | Exibir status, período e label como parts ou runs? | Product + presentation | E0/E1 |
| D-05 | Política de target literal quando field dynamic falha? | tv-dashboard-api | E0/E1 |
| D-06 | Inference pós-transform de comparable_goal | DataModel owner | E0/E2 |
| D-07 | Mapeamento dinâmico de ícone/cor por estado tipado | domain/renderer | E0/E1/E6, não bloquear core |
| D-08 | Semântica de múltiplas linhas por part | DataModel + projection | E0/E1 |
| D-09 | Período contexto e atualização automática | DataModel/filter owner | E0/E1 |
| D-10 | Gate de rollout e compatibilidade mixed versions | Architecture/Coordination | E0/E6 |

Decisão em aberto não autoriza implementar uma hipótese. Se não houver evidência suficiente, devolver DIAGNOSTIC REPORT com alternativas, sem inventar abstração.

## 16. Evidência e handoff obrigatório

Cada etapa deve entregar VISTA/TV EXECUTION REPORT com:

~~~text
TASK / E*.S*
BASE HEAD / FINAL HEAD / BRANCH / git status
AUTHORITIES READ / DOCUMENTATION DRIFT
FILES INSPECTED / CHANGED
REQUIREMENT LEDGER (RQ → decisão → etapa → teste → aceite)
CURRENT FACTS / ROOT CAUSE / HYPOTHESES
EXISTING_EQUIVALENT / REUSE_DECISION
OWNER / CONTRACT CLASSIFICATION / COMPATIBILITY
IMPLEMENTATION / ROLLBACK
SECURITY / FILIAL / RBAC
EDITOR / PREVIEW / TV PARITY
TEST COMMANDS + PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN
PIXEL EVIDENCE / USER-PERCEIVED OUTCOME
RESIDUAL SEARCH / UNRESOLVED GAPS / STOP CONDITION
~~~

**Review:** ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE.

**STOP CONDITIONS:** owner/boundary conflitante, contrato breaking não aprovado, novo motor/registry desnecessário, FE redecidindo semântica, perda de compatibilidade, segurança falhando, evidência inválida, HEAD divergente, ou necessidade de autorização de deploy não contemplada.

---

**Princípio final:** *qualquer parte informacional do KPI deve poder consumir valores dinâmicos quando semanticamente aplicável; todas as partes têm visibilidade independente; o backend resolve/autoriza e o palco único apresenta. Reutilizar contratos antes de inventar.*

## 17. Evidência E0 e decisões fechadas por código (2026-11-04)

HEAD de inventário: `07c8e762f1` (documento já na `main`). Esta seção registra fatos; não substitui schemas.

| Capacidade | EXISTING_EQUIVALENT | REUSE |
|---|---|---|
| Valor via `metrics[].field` | YES | REUSE |
| Meta numérica `targetField` → `targetValue` / comparação / progresso | YES | REUSE |
| Texto formatado da meta no card | NO (`targetDisplay` ausente; hint é autoria) | EXTEND |
| Visibilidade da meta independente da comparação | NO (não há part `target`) | EXTEND via `showTarget` (irmão de `showComparison`), default oculto |
| Título/subtítulo dinâmicos | YES (`titleField`/`subtitleField`) | REUSE |
| `contentRuns` de estilo em title/hint | YES | REUSE |
| `dataRef` dentro de partes KPI | NO (dataRef resolve em bloco texto/forma) | TO_INVENTORY — não criar engine |
| Cor `compareField` | YES | REUSE |
| Período = filtros efetivos | TO_INVENTORY (`filter.*` em extract) | não auto-reescrever hint |
| Ícone condicional | NO mapping tipado | DEFER (D-07) |

**Causa do laboratório (PROVEN no código, não reexecutada no DOM desta sessão):** comparação usa `targetValue`; o card não pinta o número da meta. Não é falha de `targetField`.

| ID | Decisão | Base |
|---|---|---|
| D-01 (**SUPERSEDED na §18**) | Sem `KpiPartRef` novo. `kpiPresentation.targetDisplay` + `kpiOptions.showTarget` (omitido = oculto). | Decisão histórica E0; insuficiente para o requisito de edição integral |
| D-02 | Misto multi-campo em partes KPI permanece no owner de `contentRuns`/`dataRef` de texto. Não estender nesta entrega. | STOP de engine nova |
| D-03 | Legado não ganha meta visível. Novo KPI não liga `showTarget` sozinho. | Plano §8 |
| D-04 | Status continua dentro da comparação. Período não vira part. | Partes atuais |
| D-05 | `targetField` declarado e não resolvido → meta nula, sem cair no literal. | `_resolve_kpi_target_number` |
| D-06 | Tipo pós-transform de `comparable_goal` | TO_INVENTORY — sem patch de schema |
| D-07 | Ícone condicional | DEFER |
| D-08 | Multi-linha segue agregação já persistida; default `first` do owner. Não rejeitar `first`. | Contrato vigente |
| D-09 | Período automático | STOP até binding explícito de contexto |
| D-10 | Campos opcionais; cliente antigo ignora `targetDisplay`/`showTarget`. | ADDITIVE |

**Fora desta entrega (PENDING):** RQ-04 misto 2+ campos na mesma string de parte KPI, RQ-08 ícone, RQ-12 período=filtro, pixel editor≡TV, VISTA live, MDD apply isolado.

**Nesta entrega:** `targetDisplay` no enrich e pintura somente com `showTarget=true`.


## 18. Decisão de produto corrigida — Meta é um item padrão do KPI (2026-11-04)

**STATUS: TARGET / DECISÃO DE PRODUTO.** Esta seção **substitui D-01 da §17** e prevalece sobre qualquer orientação anterior que trate a meta como slot de texto especial sem edição. A §17 permanece apenas como **histórico do E0**, não como instrução vigente de implementação de autoria.

### 18.1 Problema e evidência

O primeiro incremento adicionou `kpiPresentation.targetDisplay` e o controle `kpiOptions.showTarget`. A meta visível `85,00%` foi renderizada em `.delpi-kpi-card__target` com `data-kpi-target`, **fora** do sistema de subcomponentes selecionáveis `data-kpi-part`. Em HEAD consultado em 2026-11-04, `KpiPartRef` não declarava target, `kpiPartSupportsTypography` não aceitava a meta e o texto usava CSS de tipografia fixa. O menu "Itens do KPI" oferecia Título, Subtítulo, Ícone, Comparação, Progresso, Sparkline e Layout, mas não Meta. Portanto, o usuário não consegue selecionar, mover, formatar ou administrar a meta como as demais partes.

**Causa comprovada neste snapshot:** lacuna de integração com o modelo existente de parts e authoring. Não é defeito de DataModel, `targetField` ou `targetDisplay`.

### 18.2 Regra de produto vinculante

1. **Todo item informacional do KPI é opcional, com exceção do VALOR principal, obrigatório.** O card/chrome é estrutura, não uma parte informacional a tratar como toggle opcional.
2. **Meta é item padrão do KPI**, no mesmo sistema de partes que título, subtítulo/hint, ícone, comparação, progresso e sparkline. "Opcional" significa que pode ser exibido/ocultado/removido da composição, não que tenha menos recursos de edição.
3. A meta deve aparecer no **menu Itens do KPI** da top bar/contextual e nos controles equivalentes da sidebar, seguindo o padrão de adicionar, remover, mostrar, ocultar e selecionar; não criar painel ou botão separado exclusivo da meta.
4. Quando exibida, a meta deve ser selecionável diretamente no palco e oferecer os mesmos recursos aplicáveis às demais **partes textuais**: família/tamanho/peso/cor/alinhamento, modo tipográfico, posição, move/resize, chrome de seleção e persistência. Edição de aparência não edita o valor numérico.
5. O backend continua sendo dono de `targetValue`, `targetDisplay`, `targetField`, agregação, comparação, progresso, cor e segurança. A fonte dinâmica não se transforma em literal.
6. Visibilidade da meta **não** controla existência de binding; ocultá-la não desliga comparação, cores ou progresso que usem `targetField`. Desconectar campo é uma ação distinta.
7. Valem as mesmas regras de composição e visibilidade das partes existentes, inclusive compatibilidade, desfazer/refazer, save, reabrir/F5, editor≡preview≡TV e MDD.

### 18.3 Implementação-alvo mínima (condicionada ao inventário E0)

**EXISTING_EQUIVALENT = YES** para o sistema de partes e seleção; **REUSE_DECISION = EXTEND** para incluir meta como parte padrão no mesmo sistema, preferindo os mecanismos que já existem:

- Estender o vocabulário canônico existente de `KpiPartRef`, `KpiPartsMap`, capabilities, parse/serialize, hit-test/selection, visibilidade, layout/frame, tipografia, rich editing quando semanticamente aplicável e transformação de estado da UI **sem criar engine paralela**.
- Integrar a meta ao `DelpiKpiCard` por `KPI_PART_DATA_ATTR`, `bindKpiPartPointer`, `KpiPartResizeHandles`, `kpiPartSupportsTypography`, `resolveKpiPartTypographyStyle` e equivalentes vigentes. Remover dependência de fonte fixa como controle de tipografia autoral.
- Integrar o novo item à **mesma seção Itens do KPI**, top bar e sidebar, com o mesmo menu de ações, atalhos e inspector contextual. Usar nomenclatura amigável "Meta".
- Definir uma **única precedência canônica de visibilidade** entre o estado de parts existente e `showTarget` legado. Sem duplicação permanente de source of truth. Manter slides gravados com `showTarget=true` mostrando a meta e `showTarget` ausente/false mantendo a aparência anterior, salvo mudança explícita do autor.
- Respeitar variações hero, standard, compact, scorecard, sem overflow e com contraste adequado para 1080p. **Não transformar a meta em valor fixo** nem duplicar seu formatter.
- Tratar o VALOR principal como obrigatório no novo modelo de autoria sem quebrar snapshots legados; inventariar e preservar compatibilidade antes de endurecer regra.

**Não decidido sem inventário:** nome final da part (`target` é candidato coerente com o domínio atual), regra de leitura de `showTarget` e defaults/seed de layout. Fechar contrato explicitamente em E0/E1; não inventar uma nova propriedade se a atual puder ser adaptada.

### 18.4 Critérios de aceite específicos

- [ ] Selecionar o KPI apresenta "Meta" ao lado dos demais **Itens do KPI**, na top bar e sidebar.
- [ ] Usuário consegue adicionar, mostrar, ocultar, remover da composição e restaurar a meta usando os fluxos padrão.
- [ ] Clicar no número `85,00%` seleciona **a própria parte**, não apenas o bloco/card.
- [ ] Ribbon/inspector permitem alterar tipografia, tamanho, peso, cor, alinhamento e posicionamento; mudanças sobrevivem a F5 e MDD.
- [ ] Meta dinâmica continua vinda de `comparable_goal`; mudar meta de 85→95 reflete no texto, na comparação, no tom e no progresso sem alterar o slide.
- [ ] Ocultar/remover meta visual mantém binding e cálculos de comparação/cor/progresso.
- [ ] KPIs sem `showTarget` permanecem visualmente iguais; KPIs legados com `showTarget=true` não perdem meta ao migrar.
- [ ] Valor principal continua obrigatório, sem proibir configuração de outros itens.
- [ ] Seleção com mouse, teclado, multi-select quando suportado, mover, resize, undo/redo, revisão/CAS, preview e kiosk sem regressão.
- [ ] Testes demonstram paridade editor/preview/TV (DOM e pixels), compatibilidade e ausência de segundo renderer, formatter e UI especial.

### 18.5 Impacto em tarefas e PRs em andamento

Esta decisão é **REWORK** do escopo de edição da meta. O incremento de exibição `targetDisplay` permanece útil e deve ser reutilizado. A correção tipográfica CSS isolada (ex.: PR #138) **não satisfaz este requisito**; avaliar sua necessidade/compatibilidade no conjunto de mudanças, sem aplicá-la como substituto do suporte nativo às parts.

**STOP:** não aceitar solução que apenas aumente o font-size, acrescente `showTarget` em outra tela ou crie inspector próprio da meta. Não aceitar remover `showTarget` legado sem estratégia de compatibilidade. Devemos fazer a meta passar pela mesma capacidade canônica de seleção/authoring dos demais itens.
