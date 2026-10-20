# I04 — revisão independente de inteligência contextual

**TASK:** `DELIA-C3-I04-INDEPENDENT-FUNCTIONAL-ACCEPTANCE-REVIEW-01`  
**DATA:** 2026-10-20  
**BASE_HEAD:** `d7c10a44061db5ca5f79017c097fce6545f801ac`  
**VERDICT:** `INCONCLUSIVE`  
**I04_ACCEPTED:** `NO` — este parecer não promove o gate.

## Autoridade do requisito

O README da trilha define I04 como especialização contextual provider-neutral: testes bounded com TÉO, VISTA, DAVI e um sibling sintético ou renomeado; orientação que leva à capability seguinte só quando necessária; contexto de conversa, fail-closed, 30 s e ACT=0 em READ. A seção 4 exige outcome real de K1/K2 (TÉO), K3 (VISTA), K4 (DAVI) e generalização. Teste de fixture não substitui o modelo.

O plano 16 vigente antes desta revisão mantinha `I04_ACCEPTED=NO`. Q03 encerrou a refatoração semântica com residual e não aceitou I04. `delia-api` não mudou desde `a9f5f8d3c2`.

## Matriz

| Dimensão | Fonte | SHA avaliado | Status | Outcome | Lacuna |
|---|---|---|---|---|---|
| Interpretação conversacional | docs 63 e 66 | host `a9c3df812d`, modelo `moonshotai/kimi-k3` | PASS | SIPOC e hipóteses úteis, sem owner | amostra única de SIPOC; estágio acima de 12 s não exercido |
| Seleção de owner | doc 63 T05 | mesmo host, imagem 16:28Z | PARTIAL | `delpi.search_products` GROUNDED | DAVI/TÉO/VISTA não selecionados nessa bateria |
| Consulta OpenAPI | doc 63 T05 | mesmo | PASS | READ com quatro registros compatíveis com o termo | uma paráfrase, um owner |
| DAVI | histórico anterior à refatoração | SHA antigo | STALE_EVIDENCE | não reavaliado | uso contextual no runtime atual `TEST_NOT_RUN` |
| TÉO | histórico; contagem pessoal bloqueada por vínculo GLPI | SHA antigo | STALE_EVIDENCE | não reavaliado | metodologia e follow-up no runtime atual `TEST_NOT_RUN` |
| VISTA | doc 61 C02 em SHA antigo; doc 63 T02 no runtime do smoke | C02 antigo FAIL; T02 não é guia VISTA | TEST_NOT_RUN | T02 foi limitação honesta de catálogo, sem owner | orientação VISTA no código atual não medida |
| Continuidade | doc 63 T04; testes B2 | T04 no smoke; B2 em suíte | PARTIAL | comparação de hipóteses PASS | comparação tipada de dois registros de owner `NOT_EXERCISED` |
| Generalização | suíte e ADR 58 | fonte `a9f5f8d3c2` | PARTIAL | fixtures e um READ OpenAPI | sibling renomeado ao vivo `TEST_NOT_RUN` |
| Segurança | smoke 63/66; contratos vigentes | mesmos | PASS no observado | ACT=0; identificador sintético não virou registro | matriz negativa completa não reexecutada |
| Outcome útil | 63 e 66 | mesmos | PARTIAL | cenários conversacionais e um READ passaram | o conjunto TÉO/VISTA/DAVI do gate I04 não tem outcome atual |

## O que está comprovado

- O LLM admite conversa e explica SIPOC em 13412 ms, com admissão em 2289 ms, sem teto de 12 s e sem owner.
- Três hipóteses e a comparação entre a primeira e a segunda permanecem conceituais.
- A paráfrase de produto executa READ OpenAPI, com síntese GROUNDED.
- Formatos indisponíveis no catálogo observado não são inventados.
- O identificador sintético não cria registro. A projeção de HTTP 404 está no código e na suíte; ao vivo, na build nova, `TEST_NOT_RUN`.
- Orçamento global 30 s e fallback pós-orquestração de 12 s permanecem. Retry automático não foi implementado.
- B1 continua atalho lexical de um único READ/QUERY de chamados. Risco não crítico. Decisão arquitetural aberta. Código intocado.

## O que impede o aceite

O requisito material de I04 é a generalização observada em TÉO, VISTA, DAVI e sibling renomeado. Essa observação não existe para o orquestrador atual. Evidência antiga fica `STALE_EVIDENCE` porque o código de seleção, admissão e orçamento mudou depois. Não há falha nova comprovada nesse runtime, então o parecer não é `REWORK`. Também não há divergência de autoridade: a exceção que executou Q01–Q03 com `I04_ACCEPTED=NO` está no plano 16. Falta a evidência do próprio gate.

```text
REQUIREMENTS_TOTAL=10
REQUIREMENTS_PROVEN=3
REQUIREMENTS_PARTIAL=4
REQUIREMENTS_NOT_PROVEN=3
CRITICAL_BLOCKERS=NONE
MATERIAL_BLOCKERS=I04_SPECIALIST_LIVE_SET_NOT_OBSERVED
```

As três dimensões não comprovadas são DAVI, TÉO e VISTA no runtime atual.

## Testes não executados

Nenhuma pergunta nova. O menor conjunto que esclareceria o gate, se a coordenação autorizar ambiente e sujeito:

1. Um uso contextual real de capability DAVI ou TÉO, com outcome do owner.
2. Um uso contextual real de catálogo ou guia VISTA.
3. Uma comparação de dois registros autoritativos, se o contrato selection-only continuar suficiente.

Ausência de dado de owner não é defeito do modelo. Vínculo GLPI ausente continua bloqueio externo, não patch da DÉLIA.

## Decisão para a coordenação

Aceitar I04 agora encobriria requisitos não demonstrados. O passo é autorizar as três observações acima no runtime que já contém a correção, ou registrar um estreitamento explícito do gate. Este executor não altera `I04_ACCEPTED`.
