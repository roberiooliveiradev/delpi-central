# 53 — Roadmap executivo: Table UX final em no maximo 3 interacoes

Data: 2026-10-21. Produto: Portal Controladoria & Financas, Central de Fechamento, PROC-0072. Owner de aceite: PO. Executor: Devin. Estado inicial: TARGET / EXECUTION_PENDING.

## 0. Resultado contratado
Fechar os gaps reais entre as duas imagens de mockup aprovadas e o runtime das paginas R01/R02 (closing/financial-settlements) e R03 (closing/stock-inventory), evitando novas iteracoes de ajustes isolados. O commit V7 3771f83095 acrescentou somente participacao percentual nos resumos R03; nao constitui aceite visual da V7. Preservar os fixes V3-V6, inclusive o P isolado removido, e o calculo percentual V7. Imagens ilustram posicionamento, nao autorizam numeros, series, moedas ou links inventados.

Apenas tres interacoes de execucao sao permitidas. Cada interacao e uma entrega vertical FECHADA: IMPLEMENTAR -> TESTAR -> COMPARAR VISUALMENTE -> CORRIGIR -> COMMIT -> PUSH -> DEPLOY -> SMOKE -> EVIDENCIA. Nao consumir uma interacao apenas com inventario ou documento. Nao declarar PASS por HTTP 200, bundle ou testes unitarios isolados. Se houver defeito na propria interacao, corrigir ANTES de passar a proxima. Nao usar mais uma rodada cosmetica como substituto de resultado.

## 1. Autoridades, escopo e guardrails
Seguir instrucoes oficiais, .cursor aplicavel, docs 30/48/49/50/51/52, contratos e testes do HEAD. Preflight curto: origin/main HEAD, git status, worktree limpa e SHA publicado. Respeitar trabalho concorrente, sem force push. @delpi/plugin-ui first; nao construir tabela, toolbar, loading, badges ou preferencia paralelos. Sem alterar APIs, SQL, contratos, RBAC ou permissoes como parte de trabalho visual. Permissoes apenas controllership-finance.access/manage; filial somente filtro. MFE -> BFF, nunca Protheus direto.

Mockups podem incluir dados ficticios: nao usar 12.845, 1.284, R$, tendencias, grupo nominal, avatares, links de pedido/OP ou novos codigos sem fonte/contrato. Nao mascarar source_missing como zero, preservar officialP7=false e moeda 01 quando aplicavel.

## 2. INTERACAO 1/3 — Fechar R01/R02 Baixas financeiras
Meta: entregar a tabela Baixas pagar/receber visualmente proxima da referencia, sem problemas de largura, alinhamento, celular ou P solto. Escopo executavel: composicao unificada da faixa [icone + titulo contextual + pill total | itens/pagina + fonte + colunas], tipografia e header azul do kit, hierarquia da celula fornecedor/codigo, natureza/codigo, tipo movimento/codigo, documento forte, badges de lado e vinculo, coluna filial legivel, numericos tabulares a direita. Garantir linhas compactas sem perda de texto, overflow contido, foco/hover e responsividade com sidebar expandida. Reusar DataTableSection, preferencia de colunas e fonte, page-size e serverPagination; permitir resize funcional (arrastar, nao so render handle); nao recriar toolbar. O codigo cru P fica somente no metadado acessivel, jamais solto visualmente.

AC1.1 Captura autenticada lado a lado mockup/runtime, pagar E receber, dark desktop; AC1.2 codigo P ausente do fluxo visual e disponivel no tooltip/AT; AC1.3 colunas dimensionadas sem cortes, fonte/Colunas/resize/page-size/paginacao demonstrados por interacao; AC1.4 filtros automaticos preservados; AC1.5 dark/light e largura reduzida sem overflow de pagina; AC1.6 testes vitest, estruturais, lint, tsc, build verdes ou desvios classificados. Nao fingir AC por screenshot antigo.

Gate de saida: commit/push main do diff R01/R02 + docs/evidencia; deploy exclusivamente MFE via SSH operador e runbook vigente, preflight prod repo limpo e ff-only, script ./infra/scripts/up-prod-sequential.sh --fase mfe --build controllership-finance; confirmar SHA exato servido (ancestralidade so nao basta para provar novo bundle), remoteEntry 200, smoke autenticado da tabela e screenshot apos deploy. Status PASS ou REWORK; se o smoke falhar, reparar na mesma interacao.

## 3. INTERACAO 2/3 — Fechar R03 P7 e resumos
Meta: entregar painel de detalhamento R03 e resumos por tipo/armazem com fidelidade de hierarquia e uso eficiente do espaco. Prioridades: faixa da tabela equivalente a R01/R02; descricao como principal largura com wrap acessivel; produto/tipo/grupo/UM/armazem/filial compactos; numeros alinhados; badge de tipo neutro; resize e controles funcionais. Resumos lado a lado quando couber, com spacing, icones oficiais e participacao percentual V7 derivada do valor historico contratual; nao apresentar proporcao se total <=0 ou ausente. Resumo por armazem sempre identifica filial e armazem em conjunto. Hero com mensagens centralizadas, KPIs sem truncamento, filtros automaticos; preservar available/incomplete/source_missing/no_matching_items, sem tabela vazia enganosa em source_missing.

AC2.1 comparacao mockup/runtime dark/light desktop e responsivo; AC2.2 setembro 2026 partial (filial 01 ausente, 02 disponivel) com aviso correto; AC2.3 agosto 2026 available com resumo/tabela e total real, sem valores fabricados; AC2.4 controles fonte/colunas/resize/paginacao e filtro filial/armazem funcionais; AC2.5 testes completos e nao regressao R01/R02. Todas verificacoes runtime devem ser executadas ou TEST_NOT_RUN, jamais presumidas.

Gate de saida: commit/push main, deploy do MFE somente apos preflight, mesmo runbook; confirmar bundle/HEAD e executar smoke autenticado pos-deploy nas duas paginas. Se falhar, corrigir antes da interacao 3.

## 4. INTERACAO 3/3 — Fechamento integrado e homologacao final
Meta: resolver gaps visuais residuais AUTORIZADOS das duas paginas e fechar verificacao transversal com evidencia nova, nao inventariar outra vez. Homologar comparativos reais mockup/runtime lado a lado, tema claro e escuro, desktop, sidebar, <=768px mobile/tablet, zoom 200%, teclado e foco; evidenciar loading/erro/vazio/partial/source_missing, filtro auto-query e reset paginacao, colunas e preferencia de fonte, resize. Corrigir regressao de interacoes 1 ou 2 na propria interacao 3. Revisar help contextual e mapa de reuso.

Gate de saida: tests completos e prova visual; commit/push final + deploy MFE por SSH ff-only + smoke real externo e URL/hashes. Atualizar docs 30/50/51/52, esta tabela de status e README. Relatorio final unico com evidencia por AC e residuais. Resultado so ACCEPT se todos ACs autorizados foram observados PASS; caso nao haja browser autenticado para prova, INCONCLUSIVE/ACCEPT_WITH_RESIDUAL com criterios especificos nao executados, nunca PASS inferido.

## 5. Matriz de decisoes separada — NAO bloquear visual ja autorizado
Excel do universo completo, Tabela/Cards, ordenar por coluna com server pagination, links Pedido/OP/Duplicata e menu de acoes, nomes de grupo, cores semanticas MP/PI/PA, moeda BRL/R$, variacoes vs competencia anterior e filtros MP/PI/PA individuais sao DECISION_REQUIRED ou TARGET_FUTURE conforme docs 48/49/52. Para cada um, apresentar em uma UNICA secao de decisao: capacidade existente no plugin-ui, lacuna no contrato, opcoes, impacto, recomendacao; NAO implementar sem GO. O PO quer executar todos os ajustes visuais que independem desses gates em tres interacoes; ausencia de decisao nao justifica parar.

## 6. Quadro de acompanhamento por interacao
| Interacao | Meta | Codigo | Testes | Commit/SHA | Push main | Deploy SHA/artefato | Smoke autenticado | Veredito |
|---|---|---|---|---|---|---|---|---|
| 1/3 | R01/R02 fechado | DONE (V3-V7 + 811d4c7179 help-sync) | Vitest 91/91, estruturais 25/25, tsc OK, lint 0err, build OK | 3771f83095, 811d4c7179 | PUSHED | prod @ 811d4c717; bundle `App-CB__L8qt.js` com `resizableColumns`, tooltip `Código de direção` e help "redimensionar a coluna"; remoteEntry 200; container recriado Up; BFF/api-delpi/Keycloak intactos | capturas autenticadas PO 22/10/2026 (dark desktop): Baixas a pagar com pill 536, icone de tabela no titulo, header azul, badge A pagar sem P solto, Filial "Não identificada", hover de linha, banner "Qualidade dos vínculos"; P7 pill 7.929 com mesma banda | PASS_PARCIAL — AC1.2/AC1.4/AC1.6 PASS; AC1.1 falta captura receber, AC1.3 interação dos controles e AC1.5 light/mobile seguem TEST_NOT_RUN |
| 2/3 | R03 fechado | PENDING | TEST_NOT_RUN | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING |
| 3/3 | Homologacao integrada | PENDING | TEST_NOT_RUN | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING |

Atualizar a linha ao fim de cada interacao com URL de commit, comandos e resultados exatos, hash do bundle, print autenticado com timestamp, delta antes/depois e gaps corrigidos. Registrar FAIL e REWORK honestamente. Uma interacao termina somente com codigo testado, commit e push, deploy verificado e tentativa de smoke documentada; nao passar adiante escondendo falhas.

## 7. Criterios transversais e controles operacionais
Nao tocar BFF, api-delpi ou Keycloak em deploy apenas visual. Se servidor possuir diff nao commitado, divergir de main ou nao permitir pull ff-only, parar deploy e classificar EXECUTION_DRIFT, sem sobrescrever. Confirmar rollback por revert SHA + rebuild MFE. Nao gravar secretos ou dados financeiros individualizados em docs publicos. Validar CSS no DOM real (nao apenas existencia de className), foco, zoom e no-break. Cada etapa atualiza Help se interface mudar. Publicacao de artefato HTTP200 nao e prova de experiencia. Nenhuma etapa pode afirmar que screenshots anteriores comprovam codigo ainda nao deployado.

## 8. Instrucao pronta para o Devin
Executar somente INTERACAO 1/3 agora. Nao gerar novo inventario. Ler este roadmap e docs de autoridade, implementar todos os AC1, testar, comparar mockup, corrigir, commitar, push main, implantar somente MFE pelo procedimento operacional autorizado, fazer smoke e preencher a linha 1/3 deste roadmap com provas. Encerrar a resposta com veredito e proximo gate INTERACAO 2/3. Em nova interacao, executar estritamente 2/3 e depois 3/3. Nao considerar meta cumprida por iteracao cosmetica.
