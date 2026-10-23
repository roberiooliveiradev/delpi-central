# X4.UX-R1.S8.D1 — Deploy federado + runtime gate da conferência de cadastros por CNPJ

**Data:** 2026-10-23
**Autoridade:** autorização explícita do Product Owner («PORTAL SUPRIMENTOS — X4.UX-R1.S8.D1»)
**Escopo:** somente `supplies-api` + `plugins/supplies` (MFE). api-delpi, external-data-api, Core, Keycloak — **não redeployados**.

## Baseline

- **BASE HEAD:** `a172180890` (commit S8) → rebase sobre `origin/main` `c87dad7f00`.
- **SOURCE S8 SHA:** `a17218089073922178d84fd84ac990dc598dd1c4` — ancestralidade S1/S2/R1/R2/S7 confirmada no HEAD.
- **PRODUCTION CHECKOUT:** `srv-api` (`operador@192.168.1.237`), `~/projetos/delpi-central` → pull ff-only até `9281aa9f0955` (contém S8; commits supervenientes eram docs/outros produtos — zero mudança em `supplies-api`, `plugins/supplies`, `api-delpi`).

## Gate de segurança (pré-deploy)

| Condição | Evidência |
|---|---|
| ERP write gate OFF | `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — `infra/.env` e env do container |
| Rollback definido | imagens anteriores `infra-supplies-api:84d02964a88f`, `infra-supplies:6b3130be529f`; SHA prod anterior `6c5bae9568` |
| Migrations no range | nenhuma (range docs-only no escopo) |
| Nova permission | nenhuma — mesma `can_use_operations` |
| Containers | todos healthy/up antes do deploy |

## Deploy sequencial (script oficial `infra/scripts/up-prod-sequential.sh`)

| Serviço | Imagem antes → depois | Container |
|---|---|---|
| `delpi-supplies-api` | `84d02964a88f` → `acc772fa65fa` | Up/healthy |
| `delpi-supplies` | `6b3130be529f` → `37dee5f0450d` | Up |
| api-delpi | `c04762910d62` (inalterado) | SKIPPED — sem mudança S8 |
| external-data-api | inalterado | SKIPPED |
| gateway/core/keycloak | inalterados | SKIPPED |

Rollback **não executado** (não necessário). Reversão conjunta (BFF+MFE) documentada: o endpoint novo é aditivo; se o BFF for revertido com o frontend S8, a lista ficaria sem fonte — reverter os dois juntos.

## Runtime gate — supplies-api (read-only)

Dentro do container, token usuário real via Keycloak interno (`delpi` realm, client `delpi-central`):

| Caso | Resultado |
|---|---|
| Sem token | **401** |
| `tax_id` inválido (`123`) | **422** |
| `page` não inteiro | **422** |
| CNPJ real existente, `page=1&page_size=10` | **200**, `total=1`, `items=1`, chaves `[blocked,state,supplier_code,supplier_name,supplier_store]`, `002012/01` |
| `page=99` além do total | **200** `items=[]` (página vazia honesta) |
| Via gateway `/apps/supplies-api/...` | 401 sem token; **200** com token, `total=1` |
| BrasilAPI durante paginação | **0** ocorrências nos logs do supplies-api |
| Escrita supplier (POST/PUT api-delpi) | **0** nos logs; `write_enabled=false` |

`POST /suppliers/creation-preview` via gateway: `200 POSSIBLE_MATCH`, `total=1`, `matches=1`, 8 sugestões com proveniência, `write_enabled=false` — contrato S8 **aditivo confirmado**.

## MFE federado

- `remoteEntry.js` → `__federation_expose_App-CHykQmuO.js` → `./App-CwatapS_.js` (cadeia verificada; asset público **200**, 268 502 bytes — mesmo hash do build local).
- Marcadores S8 no bundle real: `existing-suppliers`, `duplicate_check`, `creation-preview`, `CompactPagination`, «Conferir cadastro», «Este CNPJ já possui», «continuar o preenchimento», `noopener`.
- Proibidos ausentes: `api-delpi`, `brasilapi.com.br`, `Service-Authorization`, `s2s_`, `client_secret` — **BFF-only**.

## Regressão

- E13 list `200` (5 itens) · E14 detail `002012/01` `200` · E14 `enrichment-reviews` `200`.
- 0 containers unhealthy/restarting; ~107 containers preservados.

## Dados reais por cenário (§9)

| Cenário | Resultado |
|---|---|
| CNPJ com um registro | PASS (total=1, uma linha) |
| CNPJ sem registro | coberto por teste unitário (zero registros → `total=0`) |
| Duas lojas / códigos diferentes / >10 registros | **TEST_NOT_RUN** em produção (não havia documento autorizado conhecido nesses volumes); coberto por testes `TestExistingSuppliers` |
| Consulta indisponível → INCONCLUSIVE | preservado (teste unitário + contrato `total:null`) |

## Visual / acessibilidade

- **V1–V8 (desktop/mobile/temas/teclado/F5): `INCONCLUSIVE`** — sem browser autenticado nesta sessão.
- Não foi declarado PASS por inspeção de bundle.

## Auditoria (RQ-07) — residual

Contrato de auditoria de visualização permanece `TO_INVENTORY` (owner: Core/segurança). Nenhum evento/log improvisado criado; nenhum CNPJ bruto ou payload externo em logs comuns.

## AC coverage

AC-01–17, AC-20 `PASS` · AC-18/19 `INCONCLUSIVE` (sem browser).

## Pós-condição

Produção serve o fluxo: consulta CNPJ → aviso informativo não bloqueante → lista completa paginada (total real) → «Conferir cadastro» abre E14 em nova aba → rascunho preservado. Sem bloqueio por CNPJ repetido, sem permission nova, sem escrita ERP, sem alteração na api-delpi.


## Revisão GPT — aceite arquitetural D1 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para deploy e runtime HTTP** com base nas evidências registradas no GitHub e no relatório Cursor (`SOURCE S8 a172180890`, relatório de deploy `1c7a96ce33`). A revisão documental não equivale à repetição independente dos comandos SSH, testes ou validação em browser.

**PROVEN por evidência reportada:** imagens BFF/MFE atualizadas, health, endpoint paginado respondendo `200 total=1`, preview aditivo com `total`, bundle federado S8, regressão E13/E14, flags ERP OFF e nenhuma escrita identificada na janela de smoke. Logs com zero POST/PUT não constituem prova exaustiva fora da janela observada.

**Limites:** paginação com dois ou mais registros/mais de dez e navegação nova aba/retorno do draft **não foram exercitados em produção via navegador**. Portanto AC-18/19 e V1–V8 `INCONCLUSIVE`, cenários multi-registro de runtime `TEST_NOT_RUN`. A pós-condição "lista completa paginada → E14 → rascunho preservado" é **capacidade comprovada por código/contrato e bundle**, e não fluxo visual já validado. `GATE-FEATURE S8 = INCONCLUSIVE` até evidência interativa ou aceite formal de residual pelo PO.

**Auditoria de visualização:** `TO_INVENTORY`, sem contrato aprovado; não introduzir eventos ou armazenamento por inferência. Próxima fatia restrita a validação autenticada de UX (sem novo deploy nem escrita Protheus), com capturas e provas de multi-loja quando houver dados autorizados. R1.S3 permanece bloqueado; R1.S4–S6 não autorizados.


## Evidência visual adicional do Product Owner — S8.V1 (2026-10-23)

**Fonte:** três capturas de tela compartilhadas pelo Product Owner nesta conversa, obtidas no Portal autenticado em produção. **Limite da evidência:** imagens foram examinadas visualmente, mas seus arquivos não foram incorporados a este repositório; esta seção é um registro textual, não um anexo de screenshots. Não reproduzir credenciais ou dados adicionais dos prints.

**Cenário real:** CNPJ consultado `00.428.307/0006-00`, fornecedor **EXPRESSO SÃO MIGUEL LTDA**, retornou **dois cadastros distintos** com o mesmo código `000905` e lojas `01` e `04`. A captura do fluxo de criação mostra aviso informativo **«Este CNPJ já possui cadastro no Protheus»**, ambos os registros na lista, situação de bloqueio indicada para a loja 04, ações **«Conferir cadastro»** para cada linha e continuidade do preenchimento sem bloqueio. Sugestões externas com fonte/data também estão visíveis.

Capturas adicionais mostram a ficha E14 individual aberta para:
- `/apps/supplies/suppliers/000905/04` — código/loja correspondentes, endereço `RODOVIA RSC 453 KM 74,2 Nº38500`, CEP `95058001`;
- `/apps/supplies/suppliers/000905/01` — código/loja correspondentes, endereço `ROD RSC 453, 38500`, CEP `85032000`.

Essas diferenças visíveis corroboram a utilidade da conferência **por código + loja**, sem deduzir irregularidade cadastral nem decidir qual registro deve ser utilizado. Os valores acima são transcrição pontual do que consta nas capturas, não uma nova consulta à api-delpi.

| Verificação | Novo status | Limite |
|---|---|---|
| Consulta de CNPJ com dois cadastros distintos, mesmo código/lojas 01 e 04 | **PASS (visual)** | Cenário específico de dois registros; não comprova paginação >10 |
| Aviso informativo e continuidade não bloqueada | **PASS (visual)** | Não prova comportamento de todas as regras futuras de POST |
| Código/loja e ação de conferir para os dois registros | **PASS (visual)** | Teste com dois registros |
| Abertura da ficha E14 de `000905/04` e `000905/01` | **PASS (visual)** | URLs e identificação de loja conferidas |
| Dados distintos em fichas individuais | **PASS (visual)** | Endereço/CEP visivelmente diferentes |
| Nova aba preserva rascunho **preenchido** ao retornar | **INCONCLUSIVE** | Capturas não demonstram retorno à aba original com draft preenchido |
| Paginação >10, carga da página 2, erros e race conditions em navegador | **TEST_NOT_RUN** | Cobertura de código/testes prévia, não runtime visual |
| Mobile, tema claro, teclado/foco, F5 | **INCONCLUSIVE / TEST_NOT_RUN** | Não comprovados pelas capturas |
| Auditoria de visualização | **TO_INVENTORY** | Sem contrato canônico aprovado |

**Reclassificação:** o cenário **multiloja com dois registros**, antes `TEST_NOT_RUN` em produção, passa a **`PASS (visual, neste caso)`**; **não** atualizar a classificação do cenário `>10` ou da paginação real entre páginas. O registro anterior de ausência de navegador refere-se à execução automatizada de D1; esta é **evidência posterior fornecida pelo PO**, sem reexecução de deploy ou smoke pelo GPT.

**Parecer:** `ACCEPT_WITH_RESIDUAL` para deploy S8 + fluxo principal de conferência por loja; **GATE-FEATURE integral = INCONCLUSIVE** até fechamento explícito dos residuais ou aceite formal do PO conforme authority aplicável. ERP write gate permanece OFF; auditoria `TO_INVENTORY`; R1.S3 bloqueada e R1.S4–S6 não autorizadas.


## S8.V1 — Retorno de testes manuais do Product Owner (2026-10-23)

**Origem da evidência:** resultado informado expressamente pelo PO nesta conversa após execução em navegador no Portal publicado. **Não foram anexados screenshots, HAR, logs de console, viewport, URLs de cada etapa, CNPJ usado no cenário >10 nem resultados de automação para estes nove testes.** Portanto, `PASS (PO-reported, manual)` significa **declaração de execução e aprovação pelo PO**, não verificação independente via navegador/CI/SSH pelo GPT. Os três prints anteriores continuam evidência visual direta somente do fluxo com duas lojas.

| Cenário manual | Resultado declarado pelo PO | Evidência adicional para auditabilidade, se necessária |
|---|---|---|
| 1. Preservação do rascunho | **PASS (PO-reported)** | Registro antes/depois com campos de teste não sensíveis, aba original mantida |
| 2. Mudança de CNPJ | **PASS (PO-reported)** | CNPJ mascarado e estados antes/depois, ausência de dados obsoletos |
| 3. Cancelamento de substituição | **PASS (PO-reported)** | Draft antes/depois, confirmação cancelada e sugestões bloqueadas |
| 4. Paginação com mais de 10 registros | **PASS (PO-reported)** | Total observado, página 1 e página 2, IDs código/loja mascarados ou autorizados; CNPJ não fornecido |
| 5. Navegação e F5 | **PASS (PO-reported)** | URL/ficha por código+loja e refresh sem erro |
| 6. Layout mobile | **PASS (PO-reported)** | Viewport e captura sem corte/overflow |
| 7. Tema claro e escuro | **PASS (PO-reported)** | Capturas de ambos os temas |
| 8. Teclado e foco | **PASS (PO-reported)** | Sequência Tab/Shift+Tab/Enter e foco visível |
| 9. Estados de erro | **PASS (PO-reported)** | Erro testado (ex.: CNPJ com DV inválido), mensagem e ausência de POST |

**Classificação de S8.V1:** `9/9 PASS (testes manuais declarados pelo PO)`; **independent verification = TEST_NOT_RUN** para estes nove testes. Os testes não geram prova de auditoria formal, de AuthZ negativo (403), rate limiting (429), falha upstream, integridade/ordenação em todas as páginas, nem de ausência de escrita fora da janela de smoke anterior. Especialmente, `paginação >10` está **declarada PASS pelo PO**, mas sem total/identificadores/prints para reprodução e correlação com o runtime documentado em D1 (`total=1` em outro CNPJ); não afirmar `PROVEN` por instrumentação ou verificação independente.

**Evidências complementares recomendadas, sem exigir refazer deploy:** captura sanitizada da contagem + páginas 1/2 do cenário >10; antes/depois do rascunho preservado; confirmação cancelada/bloqueio; captura mobile e claro/escuro; registrar versão do bundle, data/hora e perfil autorizado. Podem ser anexadas posteriormente a um repositório de evidências aprovado, sem expor tokens ou dados pessoais. Não solicitar execução disruptiva em produção.

**Decisão de revisão:** `ACCEPT_WITH_RESIDUAL` permanece válida. O PO reportou sucesso para todos os cenários manuais; o gate visual manual está **PASS por declaração do PO**, porém o `GATE-FEATURE` integral não recebe `PASS` automático enquanto os critérios de evidência formal/auditoria e demais testes não demonstrados não forem explicitamente reconciliados com as authorities. Auditoria de visualização: `TO_INVENTORY`. Escrita Protheus: OFF; sem feature ou deploy adicional.
