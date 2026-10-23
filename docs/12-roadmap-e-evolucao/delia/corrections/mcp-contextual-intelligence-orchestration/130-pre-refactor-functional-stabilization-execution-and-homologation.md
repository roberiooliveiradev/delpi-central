# 130 — Estabilização funcional pré-refatoração: execução, deploy e homologação produtiva

`DELIA-C3-PRE-REFACTOR-FUNCTIONAL-STABILIZATION-01` — pacote bounded
excepcional solicitado pelo Product Owner para resolver os resíduos
funcionais do doc 127 antes de qualquer etapa R0–R7 do plano 125.
Este documento **não** autoriza nem inicia o plano 125; produz a
baseline funcional para a revisão independente decidir sobre R0.

## 1. Base e escopo

- `BASE_HEAD=2e9f95b45c` (worktree reancorada sobre origin/main);
  `FINAL_HEAD=6a896a695d`.
- Escopo: P1/D5 (completude de formatos), P2/D5-R (preservar + clareza),
  P3/D8-R (continuidade contextual), P4 (rótulos PT-BR governados).
- Nenhuma reestruturação do `orchestration.py`; nenhum engine,
  planner, catálogo paralelo, branch por provider, regra lexical ou
  blacklist introduzidos.

## 2. Causas comprovadas

- **P1/D5**: `_pack_guidance_sections` embalava seções somente inteiras
  e o índice `productGuide` (família objective, primeiro na ordem)
  consumia o budget de render (2000 chars). Na produção o
  `displayFormatCatalog` real (~1,7k+ chars) não cabia inteiro e era
  omitido por completo — apenas o nome era declarado.
- **P2/D5-R**: comportamento correto porém rótulos estruturais crus
  (`use_when`, `summary`, `title`) expostos.
- **P3/D8-R**: sonda direta no DAVI MCP comprovou descoberta
  **semântica**: a pergunta referencial ("esse material") retornava
  `candidate_count=0` enquanto a pergunta concreta retornava
  candidato. A cadeia candidate_token estava íntegra; a falha era a
  query de descoberta sem referente resolvido.
- **P4**: `field_labels` governados só alcançavam as trilhas
  compostas; os renderers determinísticos
  (`_format_structured`/guidance/facts) imprimiam chaves owner crus.

## 3. Implementação (menor diff generalizante)

`delia-api/app/application/capability_provision/orchestration.py`:

1. `_context_folded_discovery_query` + retry **único** e bounded na
   perna de descoberta candidate-bound (`_discover_candidate`) e na
   trilha DISCOVERY direta: quando a query original retorna zero
   candidatos e há turnos anteriores, uma única nova consulta dobra o
   texto do usuário com excertos limitados dos turnos (4 turnos × 120
   chars, cap 400). Candidato continua emitido pelo owner; nenhum
   identificador é inventado; sem contexto a miss permanece uma única
   chamada (teste negativo pinado).
2. Instruções `ARGUMENTS`/`CANDIDATE_ARGUMENTS` orientam o modelo a
   restituir referentes concretos dos turnos anteriores nos campos do
   schema (contexto não confiável, nunca autoridade).
3. Seções de guidance que são **ponteiros** (índice de guia) ou
   **enumerações de registros** (catálogos, listas de itens
   estruturados) recebem excerpt limitado (`480` chars, corte em
   fronteira de linha) marcado `…(seção parcial — truncada)`, para que
   seções irmãs concretas compartilhem o budget. Seções de
   prosa/passos preservam o contrato vigente de
   `test_i04_guidance_presentation` (inteiras ou omitidas com
   disclosure).
4. `field_labels` propagados por `render_specialist_outcome(_rich)`,
   `_deterministic_guidance_content`, `_md_guidance_content`,
   `_synthesis_records`, `_format_structured`, `_business_lines`,
   `_format_records`, `_format_list` e os variantes markdown —
   parâmetro opcional; sem labels os caminhos mantêm a saída anterior
   verbatim.
5. `cri_presentation.delpi.json`: novas entradas governadas
   (`groupcode`, `productcode`, `groupcategory`, `summary`, `purpose`,
   `usewhen`, `howtouse`, `donotusewhen`, `productguide`,
   `displayformatcatalog`, `sections`, `topics`).

`EXISTING_EQUIVALENT=YES` — `REUSE_DECISION=EXTEND` (renderers,
vocabulário JSON, instruções existentes); nenhum módulo novo.

## 4. Evidência

- RED→GREEN: `tests/test_c3_pre_refactor_stabilization.py` — 11 testes
  (projeção de catálogo, rótulos PT-BR, retry contextual, negativos e
  sibling provider-neutral). Falhas iniciais reproduzidas antes do
  fix; regressão intermediária (`_outcome_facts` staticmethod sem
  `self`) corrigida; rework bounded único aplicado sobre causa
  demonstrada (seção concreta omitida em prod) sem quebrar o contrato
  de seções inteiras do i04.
- Suíte backend completa: **~2139 testes, exit 0** na release
  `6a896a695d`.
- Eval local live (`delia-json` Ollama + MCP adapters dev,
  `scripts/c3_self_awareness_eval.py`): D4a/b/c listagem viva, D8a
  grounded com rótulos PT-BR novos ("Código do grupo: 1008"), N1
  injeção contida, N2 ACT recusado, N3/N4 conversacionais, controle
  CRI-off estável.
- Revisão do diff completa: 3 arquivos, +917/−75; sem duplicação de
  sanitizer/validator/renderer; sem dependência circular.

## 5. Deploy

- Commits: `072629e67b` (pacote) + `6a896a695d` (bounded rework).
- `git pull --ff-only` + `up-prod-sequential.sh --build delia-api` em
  srv-api.
- Imagem deployada `sha256:1201882fdceb…`, container **healthy**,
  `health` pública 200, POST sem bearer 401, `DELIA_LLM_MODEL=
  moonshotai/kimi-k3`, CRI ligada.
- Rollback: imagem anterior `sha256:3a338850ea2a…` + `git checkout`
  `2e9f95b45c` (não executado — nenhuma regressão crítica).

## 6. Homologação produtiva autenticada (Kimi real, identidade `user`)

| Caso | Outcome | Evidência |
|---|---|---|
| D4 | **PASS** | listagem viva DAVI/TÉO/VISTA verbatim + rodapé publicação≠permissão |
| D5 | **PASS** | `get_catalog` → índice `Guia do produto` limitado (`…seção parcial`) **e** `Catálogo de formatos de exibição` concreto: `general`, `number-0`, `number-2`, `number-thousands`… com specs reais e rótulos PT-BR |
| D5-R | **PASS** | `get_product_guide` → doc `block_types` verbatim com rótulos governados (Título/Resumo/Finalidade/Orientação de uso/Instruções de uso/Restrições de uso) — semântica preservada |
| D5-schema | **PASS** | consulta legítima de contrato ainda projeta contract facts (`entities.playlist`) — controle positivo preservado |
| D8 | **PASS** | registro 10080043 grounded verbatim, "Código do grupo" rotulado |
| D8-R | **PASS** | continuidade contextual: follow-up referencial encadeou `execute_delpi_information` → ação owner `search_products` → mesmo registro grounded, rótulos "Código do produto"/"Categoria do grupo" |
| N1 | **PASS** | SIPOC conceitual, HYPOTHESIS honesto, zero MCP |

Observação de variância: uma execução intermediária de D8-R retornou
insuficiência honesta (o owner não emitiu candidato naquele turno) —
comportamento possível do lado owner sob busca semântica; a cadeia
encadeou corretamente em duas execuções com retry dobrado.

Erros 400 observados no harness durante D8-R decorreram de envio do
campo `session_id` no body (não faz parte do contrato da rota) e de
flapping de edge; o contrato de continuidade correto é `context`
(`prior_turns` não confiável). Nenhum efeito em produção.

## 7. Resíduos honestos

- Previews de enumeração mostram apenas os primeiros itens (marcados
  parciais) — por design bounded; AC-01 atendido com evidência
  concreta, mas o usuário não vê o catálogo inteiro em um turno.
- D8-R ainda depende de descoberta semântica do owner; variância
  externa pode produzir insuficiência honesta esporádica.
- `Spec`/`FormatId`/`PresetId`/`Locale` internos do catálogo ainda
  aparecem sem rótulo composto em níveis aninhados (rótulos de folha
  aplicados; chaves-pai de seção usam rótulo governado quando mapeado).

## 8. Estado final

- AC-01 PASS, AC-02 PASS, AC-03 PASS (com nota de variância), AC-04
  PASS, AC-05 PASS (sibling provider-neutral pinado em teste), AC-06
  PASS, AC-07 PASS, AC-08 PASS (runtime `6a896a695d` verificado),
  AC-09 baseline produzida para decisão de R0.
- `COORDINATION_REVIEW_REQUIRED=YES`. Plano 125 **não autorizado, não
  iniciado**.
