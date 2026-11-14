# Entry audit — TRILHA DE EXECUÇÃO (back-end → MCP → front-end)

| Campo | Valor |
|---|---|
| Status | **READY** (trilha aprovada pelo owner em 2026-11-13) |
| Plano | [plan.md](./plan.md) · [backend](./backend/README.md) · [mcp](./mcp/README.md) · [frontend](./frontend/README.md) · [reference](./reference/skill-auditoria-entradas-nfe-protheus/) |
| Autoridade | instruções oficiais do arquiteto e `.cursor` aplicáveis > ADR-003 (criado em T1) > **esta trilha (ordem de execução)** > plan/backend/mcp/frontend > reference |
| Ordem | T0 → T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → **PARADA para verificação do owner pela CLARA** → T10 → T11 → T12 → T13 |

---

## PARTE 0 — Como o Cursor executa esta trilha

1. Execute a partir da primeira etapa do QUADRO DE STATUS (Parte 2) que não esteja DONE. Siga a ordem; não pule etapa nem antecipe a seguinte.
2. Trabalhe **direto na `main`**, sem criar branch; não faça stash, reset ou clean; preserve o trabalho de outros agentes; commits só com os arquivos da etapa.
3. Cada etapa segue o PROTOCOLO (Parte 3). Ao terminar uma etapa, atualize o QUADRO e o REGISTRO (Parte 8) neste arquivo, faça commit e push, e siga para a próxima **sem esperar o owner**, exceto nas paradas da Parte 4 e na PARADA DE VERIFICAÇÃO após a T9.
4. **Correção autônoma:** teste falhou → diagnostique com evidência (arquivo:linha, log), corrija com diff mínimo, rode de novo. Até **3 ciclos** por problema. No 4º, BLOCKED (Parte 4).
5. **Documentação técnica dentro da etapa:** cada etapa atualiza os documentos que ela muda (contrato, rotas, schema, catálogo, fichas, decisões), no mesmo commit. Documento desatualizado = etapa não está DONE.
6. Evidência: `PROVEN | TO_INVENTORY | INCONCLUSIVE` com arquivo:linha; teste `PASS | FAIL | TEST_NOT_RUN`. Smoke não executado é INCONCLUSIVE, nunca PASS.
7. Nunca imprimir token, senha, secret, CNPJ completo de fornecedor ou valores de notas reais em commit, log ou documento do repositório (ele é **público**). Evidência com dado real vai para o report no chat, de forma resumida.
8. Regra de publicação do owner: teste de comportamento em HML; passou tudo, publica em PROD. Funcionalidade nova entra **desligada por flag** e é ligada após o ensaio HML PASS.
9. **Autorização permanente para HML (owner, 2026-11-14):** quando faltar em HML um container de que a trilha precisa (ex.: financial-api), o Cursor **sobe o container** pelo procedimento vigente (`projetos-teste/delpi-central`, usuário operador, `up-hml-sequential.sh`), **registra o manifesto da aplicação no Core HML** quando faltar, cria ou usa usuários de teste de HML com as permissões necessárias e **segue com os testes**, sem parar para pedir. Limites: só HML; nunca PROD; nenhum token, senha ou secret em log, commit ou report; registrar no Registro (Parte 8) o que foi subido, registrado e criado. Para registrar manifesto, usar um usuário de teste de HML com `apps.manage` (criar pelo bootstrap do Keycloak/Core de HML se não houver).

---

## PARTE 1 — Decisões consolidadas (não reabrir)

| ID | Decisão |
|---|---|
| D1 | Motor de regras na **controllership-finance-api (BFF)**, domain puro (sem framework, HTTP, banco ou SDK). Fontes por adapters HTTP. |
| D2 | Dados **automáticos**: Protheus (SF1, SD1, SF4, SFT, SA2, filiais) pela **api-delpi**; XML de NF-e e CT-e pelo **Questor** via **financial-api** (a mesma integração que o LNF usa). Sem upload de planilha. |
| D3 | Front-end no padrão visual dos Portais com **`@delpi/plugin-ui`**; nada copiado do HTML do Raio-X; componente novo nasce no plugin-ui. |
| D4 | Tudo com **`controllership-finance.access`** (ver, executar, reexecutar, resolver, reabrir). `manage` herda. Nenhuma permission nova. |
| D5 | Página própria «Auditoria de entradas», com atalho a partir do Fechamento mensal. |
| D6 | A CLARA audita **num comando**; `entry_audit.run`, `rerun`, `resolve`, `reopen` são **diretos** (sem prepare/confirmação). **As seis tools semânticas não mudam**: só o catálogo, a análise e o conhecimento crescem. |
| D7 | Execução **assíncrona** por um worker no `lifespan` da BFF (padrão do job de notificações), uma análise por filtros, uma execução por filial. |
| D8 | Filtros da execução = os dois de hoje: **período De/Até livre** (data de recebimento; nenhuma data fixada ou sugerida) e **tipo de documento** (NF-e = espécie SPED, CT-e = espécie CTE), mais filiais. |
| D9 | Primitivos novos no plugin-ui: `DistributionDonut`, `ResolutionStatusCell`; evoluções aditivas: `ScopeChipBar`, `SemicircleProgressGauge`, `HorizontalValueBars`, `ComparativeAreaChart`. |
| D10 | Auditoria **sob demanda, em qualquer dia**; sem agendamento. |
| D11 | **Melhorias sobre a skill** (evidência da amostra de 12/11): XML buscado **pela chave** para toda nota da SF1; listagem do Questor por emissão (com folga) só para achar o que não foi lançado; nota só no XML com solicitação aberta no **LNF** recebe a situação «Em lançamento (LNF)». |
| D12 | Parâmetros fixos da skill viram **configuração da BFF**: `ENTRY_AUDIT_PRESUMED_CREDIT_TES=004`, `ENTRY_AUDIT_FREIGHT_CFOP_SUFFIX=352`, `ENTRY_AUDIT_XML_LOOKBACK_DAYS=30`, `ENTRY_AUDIT_UNMATCHED_GRACE_DAYS=3`, `ENTRY_AUDIT_TOLERANCE=0.05`. Cada análise grava a configuração usada. |
| D13 | Flag `ENTRY_AUDIT_ENABLED` (BFF; padrão `false`) controla rotas `/entry-audit/*`, worker e entradas da CLARA. Rotas novas de leitura da api-delpi e da financial-api não precisam de flag (só leitura, sem consumidor até a flag ligar). |
| D14 | O conhecimento da auditoria entra no domínio **`controllership`** do corpus da CLARA (fichas AE-00 a AE-15). |
| D15 | HML: o Cursor pode subir containers que faltarem, registrar manifestos no Core HML e criar usuários de teste para continuar os testes (Parte 0, regra 9). |
| D16 | Futuro, **fora desta trilha**: o Portal Financeiro será fundido ao Portal Controladoria & Finanças, permanecendo as permissões `controllership-finance.access`/`.manage`. Esta trilha não antecipa a fusão: usa a financial-api como fonte do Questor e não muda o Portal Financeiro. |

---

## PARTE 2 — QUADRO DE STATUS (o Cursor atualiza a cada etapa)

| Etapa | Nome | Status | Ambiente | SHA(s) | Data | Evidência |
|---|---|---|---|---|---|---|
| T0 | Rebaseline e inventário (somente leitura) | DONE | leitura PROD (Questor) e banco DELPI | 19b026cef6 | 2026-11-14 | inventário em backend §4; Questor por data PROVEN; HML financial-api ausente |
| T1 | Contrato completo + ADR-003 | DONE | docs | 14da947e67 | 2026-11-14 | backend §6 ACCEPTED; ADR-003; catálogo MCP aceito |
| T2 | api-delpi — leitura do Protheus | DONE | DEV (banco DELPI) | 85276cc429 | 2026-11-14 | 12 testes PASS; filial 01 em 12/11/2026 = 19 (12 SPED + 7 CTE), igual ao SQL direto |
| T3 | financial-api — Questor por período, por chave e CT-e | DONE | leitura PROD (HML sem financial-api) | af72c82f2b | 2026-11-14 | 75 testes PASS; 12/11/2026 NF-e 10 e 20, CT-e 1 e 1; KeyCte devolve a mesma linha |
| T4 | BFF — motor de regras + paridade com a skill | TODO | | | | |
| T5 | BFF — análise, worker, persistência, rotas, LNF, exportação | TODO | | | | |
| T6 | Back-end em HML | TODO | | | | |
| T7 | CLARA — catálogo, análise, conhecimento, diretivas | TODO | | | | |
| T8 | CLARA em HML (testes MCP) | TODO | | | | |
| T9 | PROD — back-end + CLARA, flag ligada | TODO | | | | |
| — | **PARADA: verificação do owner pela CLARA** | — | PROD | | | |
| T10 | plugin-ui — caracterização, evoluções, primitivos | TODO | | | | |
| T11 | MFE — páginas 01, 02, 03 + Ajuda | TODO | | | | |
| T12 | Front-end em HML | TODO | | | | |
| T13 | PROD — front-end | TODO | | | | |

Status: TODO · IN_PROGRESS · BLOCKED · DONE.

---

## PARTE 3 — Protocolo de cada etapa

```
P1 REBASELINE   git rev-parse HEAD; git status --short; ler esta trilha e o Registro.
P2 INVENTÁRIO   confirmar no código o que a etapa assume (arquivo:linha). Premissa falsa = EXECUTION_DRIFT registrado; adaptar dentro do contrato ou BLOCKED.
P3 IMPLEMENTAR  diff mínimo, Clean Architecture, padrões vigentes do serviço.
P4 TESTAR       testes novos da etapa + suíte do serviço + regressão dos consumidores afetados (comparar falhas com o commit pai: só pré-existentes são aceitas).
P5 CORRIGIR     falhou → diagnosticar → corrigir → P4 (até 3 ciclos).
P6 DOCUMENTAR   atualizar plan/backend/mcp/frontend/contrato/fichas/ADR e esta trilha.
P7 COMMIT/PUSH  só arquivos da etapa; mensagem "feat|fix|docs(entry-audit): <etapa> — <resumo>".
P8 AMBIENTE     só nas etapas de HML/PROD (T6, T8, T9, T12, T13), pelo procedimento vigente.
P9 REGISTRAR    quadro + registro (Parte 8).
```

---

## PARTE 4 — Paradas (status BLOCKED, reportar, não contornar)

| ID | Quando |
|---|---|
| X1 | Problema sem solução após 3 ciclos de correção. |
| X2 | Regressão em suíte existente de qualquer serviço (falha nova em relação ao commit pai). |
| X3 | Paridade com a skill (T4) não fecha e a diferença não se explica por regra documentada. |
| X4 | Qualquer escrita no Protheus, no Questor ou em dados do LNF — a auditoria é **somente leitura** nessas fontes. |
| X5 | Algo exigiria nova permission, nova tool MCP, mudar as seis tools, ou mudar `delpi_auth`/Core. |
| X6 | Dado real (CNPJ completo, valores, nomes de fornecedor) iria para o repositório. |
| X7 | Verificação pós-deploy em PROD falha → rollback do serviço pela imagem preservada e parar. |
| X8 | Checkout de HML com alterações locais de outra frente que se sobreponham aos arquivos a atualizar (sem sobreposição: backup + `--ff-only`, como no ALINHAMENTO-01). |

---

## PARTE 5 — Rollback

| Escopo | Como |
|---|---|
| Funcionalidade | `ENTRY_AUDIT_ENABLED=false` na BFF + recreate: rotas, worker e entradas da CLARA somem; nada mais muda. |
| Serviço | imagem anterior preservada com tag `rollback-entry-audit-<serviço>` (criada antes de cada deploy em PROD) + recreate sem `--build`. |
| Banco | migration `V023` só cria tabelas novas; rollback de código não exige remover tabelas. |

---

## PARTE 6 — Etapas

### T0 — Rebaseline e inventário (somente leitura)

Responder com arquivo:linha e registrar no [backend §4](./backend/README.md):

1. **Protheus/api-delpi:** SQL existente reaproveitável de SF1, SD1, SF4, SFT, SA2 e filiais (SM0); nomes físicos dos campos usados pelo motor (mapear cada coluna que `reference/.../scripts/regras.py` e `leitura.py` leem — ex.: `Chave NFe`→`F1_CHVNFE`, `Espec.Docum.`→`F1_ESPECIE`, `Dt. Receb.`→`F1_RECBMTO`, `Tipo Entrada`→`D1_TES`, `Sit.Tribut.`→`D1_CLASFIS`, `Cred. ICMS ?`→`F4_CREDICM`, `L.Fisc. ICMS`→`F4_LFICM`, `FT_VALICM`…). Tabela completa coluna da skill × campo Protheus × tabela física.
2. **Questor/financial-api:** a listagem `/cliente/nfe/listagem` aceita filtro de data e de destinatário? Como listar CT-e recebidos? Como achar um XML **pela chave** (número + CNPJ do emitente, que estão dentro da chave)? Sessão por filial: existe para a filial 02? Prova com chamada real em HML (sem tokens no log).
3. **LNF:** consulta da BFF que diga, por chave ou número+fornecedor, se há solicitação aberta e o status (para D11).
4. **BFF:** padrão do job no `lifespan`, do runner de migrations (próximo número: `V023`), do catálogo semântico (`semantic_bridge.py`), do corpus (`corpus_manifest.py`), das instruções (`branding.py`) e dos testes MCP (`tests/test_clara_*`).
5. **Volume:** notas por dia e por mês por filial (HML/PROD, só leitura).

Saída: inventário registrado; premissas confirmadas ou EXECUTION_DRIFT com a adaptação proposta.

### T1 — Contrato completo + ADR-003

1. Fechar o contrato no [backend](./backend/README.md): payloads de cada rota (api-delpi, financial-api, BFF), envelope, erros, paginação, filtros, `meta`; schema `V023` (colunas e índices); chave estável da ocorrência; configuração D12; flag D13.
2. Identificador estável por regra (ex.: `cte.credit_without_right`) para cada linha de `reference/.../references/regras.md`, numa tabela no backend.
3. Catálogo da CLARA final no [mcp](./mcp/README.md) (entradas, parâmetros, gate, direto/governado, `get_context(topic='schema')`).
4. `adr/ADR-003-entry-audit.md` (ACCEPTED, decisões D1–D14), na pasta de ADRs da controladoria.

Saída: contrato `ACCEPTED` nos documentos; ADR criado.

### T2 — api-delpi: leitura do Protheus

Rotas (prefixo `/financeiro/entry-audit`, só leitura, paginadas, sem regra fiscal): `documents` (SF1 + SA2: CNPJ/UF; filtros `branch`, `received_from`, `received_to`, `species`), `items` (SD1 dos mesmos documentos), `fiscal-book` (SFT dos mesmos documentos), `tes` (SF4 inteira), `branches` (filial, CNPJ, UF). Autorização: o mesmo padrão das rotas `/financeiro/*` consumidas pela BFF (service token).

Testes: contrato de cada rota; filtros; paginação; uma filial e um dia reais em DEV/HML batendo com a contagem do SQL direto.

### T3 — financial-api: Questor

1. Listagem por **período de emissão**, **tipo** (`nfe`, `cte`) e **filial** (destinatário/tomador), com os ids para baixar o XML: `GET /invoices/received/export`.
2. Busca **pela chave** (resolve número + CNPJ do emitente da chave; devolve o XML original): `GET /invoices/received/by-key/{access_key}/xml`.
3. Download do XML de CT-e e de NF-e (já existe para CT-e; padronizar).
4. Se a listagem não aceitar data, paginar pela emissão (`orderGroup=Emission`) e parar ao passar do início do período (registrar como decisão por evidência).

Testes: contrato; um dia real em HML: contagem igual ao download manual do Questor do mesmo dia.

### T4 — BFF: motor de regras + paridade

1. `domain/entry_audit/`: modelos, casamento (SF1×XML pela chave, troca de chave pelo XML de mesmo número e valor, SD1×itens), regras por grupo (cabeçalho, itens, coerência, Simples/presumido SC, CT-e, chave/espécie/fornecedor, livro fiscal, sem par, «não apontado»), severidades, temas, textos «por quê» e «o que fazer», identificador estável de regra. Python puro.
2. `infrastructure/entry_audit/xml_reader.py`: porte de `leitura.py` (NF-e, CT-e, eventos de cancelamento) para objetos do domain.
3. **Teste de paridade por construção:** para o mesmo conjunto de entrada, gerar (a) as planilhas e a pasta de XML que a skill espera e rodar `reference/.../scripts/auditoria.py`; (b) rodar o motor. Comparar ocorrências (documento, item, regra, campo, severidade, valores com tolerância de R$ 0,05), notas sem par e o bloco «não apontado». As melhorias D11 ficam **desligadas** neste teste. Fixtures sintéticas no repo (sem dado real); paridade com dado real de HML vai para o report.
4. Testes unitários por regra (positivo e negativo).

Saída: paridade PASS (X3 se não fechar).

### T5 — BFF: análise, worker, persistência, rotas

1. `V023`: `entry_audit_analysis`, `entry_audit_run`, `entry_audit_document`, `entry_audit_occurrence`, `entry_audit_unmatched`, `entry_audit_cte`, `entry_audit_tes_used`, `entry_audit_status`, `entry_audit_xml_cache`.
2. `application/entry_audit/`: criar análise (idempotente por filtros), executar por filial, reexecutar (inclusive só uma filial), consultar, resolver/reabrir, exportar. Portas: `ProtheusEntriesPort`, `FiscalXmlPort`, `InvoicePostingLookupPort` (LNF), `EntryAuditRepository`.
3. Worker no `lifespan` (pega `queued`; ao subir, devolve `running` órfãs para a fila); etapas e andamento por filial; erro por filial sem derrubar as outras.
4. D11: XML pela chave para toda nota da SF1 com chave; listagem por emissão de `date_from − ENTRY_AUDIT_XML_LOOKBACK_DAYS` até `date_to` para achar «só no XML»; cruzamento com o LNF («Em lançamento (LNF)»); «só no XML» emitida há menos de `ENTRY_AUDIT_UNMATCHED_GRACE_DAYS` = Info «em trânsito».
5. Rotas `/entry-audit/*` do [backend §3.4](./backend/README.md) (execução, histórico, `options`, `summary`, `daily`, `breakdowns`, `facets`, `trend`, abas, detalhe, `resolve`/`reopen`, `export`), todas com `controllership-finance.access`, envelope padrão, sob `ENTRY_AUDIT_ENABLED`.
6. Exportação xlsx no layout da skill (porte de `relatorio.py`).

Testes: use cases; rotas (200/403/404/409/422); autorização (sem access → 403); idempotência; reexecução preserva status por chave estável; worker com falha numa filial; flag off → rotas inexistentes; suíte inteira da BFF e contract tests do LNF (F2) sem regressão.

### T6 — Back-end em HML

1. Publicar api-delpi, financial-api e BFF em HML (`projetos-teste/delpi-central`, usuário operador; backup + `--ff-only` se houver alterações locais de outras frentes; X8 se houver sobreposição). `ENTRY_AUDIT_ENABLED=true` em HML.
2. Ensaio: análise de **um dia real** e de **um mês real** em cada filial; conferir contagens contra o SQL e o Questor; executar a skill de referência sobre as mesmas entradas e comparar (paridade com dado real); conferir D11 (XML pela chave, LNF); reexecução; resolver/reabrir; exportação; usuário sem `access` → 403; logs sem token.
3. Desempenho: tempo de uma análise de um mês por filial (registrar).

Saída: ensaio HML PASS.

### T7 — CLARA: capacidades (sem tools novas)

1. Catálogo semântico: entradas do [mcp §4](./mcp/README.md) (`entry_audit.options|analysis|summary|daily|breakdowns|trend|occurrences|occurrence|documents|unmatched|cte|tes` em `read`; `analyze` com `analysis_type=entry_audit_findings` e `compare_to`; `execute` direto `entry_audit.run|rerun|resolve|reopen`), gate `controllership-finance.access`, schemas em `get_context(topic='schema')`. **As seis tools e suas assinaturas não mudam.**
2. `entry_audit_findings`: FACT/RECOMMENDATION agrupados por causa (TES, cadastro, fornecedor), no formato da skill (o que pede ação / corrigir / sem impacto), com direcionamentos citando a regra; comparação com outra análise.
3. Conhecimento: escrever as fichas **AE-00 a AE-14** em `docs/12-roadmap-e-evolucao/controllership-finance/fichas/auditoria-entradas/` a partir de `reference/` e do contrato (uma seção por regra com o nome exato do motor e o identificador estável; perguntas abertas do owner marcadas `TO_INVENTORY`); registrar no `corpus_manifest.py` (domínio `controllership`, `PORTAL_ACCESS`). AE-15 fica para casos reais.
4. Diretivas: acrescentar ao `branding.py` o bloco do [mcp §5](./mcp/README.md) (pedido de auditoria com período e tipo ditos pelo usuário — perguntar o período se faltar; apresentação; explicação do dashboard; direcionamentos; honestidade; resolver só quando pedido).

Testes: catálogo/schema chamáveis (padrão `test_clara_catalog_schema_callable.py`); execução direta com idempotência (padrão `test_clara_direct_execution.py`); gate por permission (com e sem access; só LNF não vê); corpus parity (padrão `test_clara_corpus_parity.py`); um fluxo ponta a ponta no cliente MCP de teste: `run` → `analysis` até `done` → `analyze` → `occurrence` → `resolve`.

### T8 — CLARA em HML

Publicar a BFF com T7 em HML; rodar os testes MCP contra o endpoint MCP de HML, se existir (senão: testes in-process PASS + registrar «verificação funcional no PROD pelo owner»); ingestão do corpus em HML e `knowledge(search)` devolvendo as fichas com citação.

### T9 — PROD: back-end + CLARA

1. Linha de base (contagens do schema LNF e 5xx da BFF), digests atuais com tag `rollback-entry-audit-<serviço>`.
2. Publicar **api-delpi → financial-api → BFF**, um por vez, fora do horário comercial ou com OK do owner (**OK dado pelo owner para esta trilha**). `ENTRY_AUDIT_ENABLED=true` na BFF (ensaio HML PASS). Publicação governada do corpus.
3. Verificação técnica: health; rotas `/entry-audit/options` e `/analyses` com credencial; uma análise de um dia real concluída; catálogo da CLARA lista as entradas novas para quem tem `access`; LNF e Central de Fechamento sem regressão (contagens e 5xx); logs sem token. Falha → X7.
4. **PARAR.** Report com o roteiro da Parte 7 pronto para o owner.

### PARADA — Verificação do owner pela CLARA (fora do Cursor)

O owner (com o Claude) verifica pela CLARA em PROD, usando a amostra enviada no chat (Matriz, recebimento 12/11/2026, NF-e e CT-e), comparando com a saída da skill guardada fora do repositório. Roteiro na Parte 7. Só depois disso começa a T10.

### T10 — plugin-ui

Doc [frontend/04](./frontend/04-componentes-plugin-ui-novos-e-evolucoes.md): testes de caracterização dos 4 componentes evoluídos no código atual → evoluções aditivas (§3–§6) → primitivos novos (§1 `DistributionDonut`, §2 `ResolutionStatusCell`) com demos no catálogo → exports. Regressão: suíte do plugin-ui + build/typecheck de todos os consumidores dos componentes evoluídos.

### T11 — MFE controllership-finance

Adapters `Cf*` (frontend README, regra 3); rotas do MFE; páginas [01](./frontend/01-pagina-entrada-e-execucao.md), [02](./frontend/02-pagina-dashboard-da-analise.md), [03](./frontend/03-pagina-detalhe-da-ocorrencia.md) exatamente como especificadas (componentes, props, dimensionamento, URL, estados, acessibilidade); atalho no Fechamento mensal; Ajuda no mesmo gate. Testes de unidade/render, build, typecheck; desktop, mobile, teclado, claro/escuro.

### T12 — Front-end em HML

Publicar plugin-ui (consumidores afetados) e MFE em HML; ensaio das três páginas com a análise real da T6; filtros cruzados; resolver; mobile; usuário sem access.

### T13 — PROD: front-end

Linha de base, tags de rollback, publicação, verificação (páginas abrem, dados batem com a CLARA, consumidores do plugin-ui sem regressão). Plano e trilha → DONE.

---

## PARTE 7 — Roteiro de verificação do owner pela CLARA (após T9)

Pedidos em linguagem natural, em ordem:

1. «Audite as entradas da Matriz recebidas em 12/11/2026, NF-e e CT-e.» → a CLARA executa, acompanha e responde no formato da skill.
2. «Quantas notas casaram e quantas ficaram sem par? Por quê?» → as notas sem par devem vir explicadas (em lançamento no LNF, em trânsito, sem XML).
3. «O que pede ação?» / «Me explica o resultado.»
4. «Por que a NF da Multipar deu ocorrência?» → regra de origem da mercadoria, com a ficha citada.
5. «Marca as ocorrências da Multipar como resolvidas.» → depois «reabre uma delas».
6. «Compare com a auditoria de 11/11/2026.»

Referência (saída da skill sobre a mesma amostra, fora do repositório): 2 NF-e casadas; 3 ocorrências Média de origem da mercadoria (3 itens da mesma NF); «não apontado» com ICMS em TES sem crédito e CST 090. Esperado na plataforma: **as mesmas ocorrências** nas notas que a skill casou, **mais** as notas que a skill não conseguiu casar por data (XML pela chave), e as «só no XML» explicadas pelo LNF.

---

## PARTE 8 — Registro de execução (o Cursor preenche)

| Data | Etapa | SHA | Resultado | Evidência / observações |
|---|---|---|---|---|
| 2026-11-14 | — | — | Owner | Autorização permanente para HML (regra 9, D15) e fusão futura Financeiro → Controladoria & Finanças registrada como fora da trilha (D16). |
| 2026-11-13 | — | — | Trilha criada | plano, back-end, front-end e MCP consolidados; decisões D1–D14 |
| 2026-11-14 | T0 | 19b026cef6 | DONE | Mapa SX3×skill em backend §4. Questor: NF-e filtra emissão em dd/MM/yyyy (ISO → HTTP 500); CT-e filtra nos dois formatos; `iTotal` da NF-e não é contagem; sessão 02 PROVEN em PROD. HML sem container financial-api. LNF aberto por número+fornecedor; chave só no DANFE. Próxima migration `V023`. Volume de um mês é pequeno. Sem upload. |
| 2026-11-14 | T1 | 14da947e67 | DONE | Contrato em backend §6 (payloads, erros, paginação, `V023`, chave estável, ids de regra, D12, D13). Catálogo da CLARA aceito no mcp. ADR-003 ACCEPTED. O quadro anterior citava o pai `19b026cef6`; o commit da T1 é `14da947e67`. |
| 2026-11-14 | T2 | 85276cc429 | DONE | Cinco leituras em `/financeiro/entry-audit`. S2S reutiliza `stock-inventory.read` do client `controllership-finance-api`; sem escopo novo e sem flag. Contagem ao vivo, filial 01, recebimento 12/11/2026, SPED+CTE: 19, igual ao `COUNT` direto (12+7). Mês 01–14/11: 177. Filial 02 no mesmo dia: 19. Itens e livro do dia: 40 linhas cada. TES: 458. Filiais: empresa 01, UF SC e ES, CNPJ com 14 dígitos. Pytest `tests/test_financeiro_entry_audit.py`: 12 PASS. |
| 2026-11-14 | T3 | af72c82f2b | DONE | `GET /invoices/received/export` e `GET /invoices/received/by-key/{access_key}/xml`. NF-e em `dd/MM/yyyy`; CT-e com `KeyCte`. Página curta = fim. XML de NF-e também em `/xml/original` com `documentType=nfe`. Pytest da financial-api: 75 PASS. Leitura PROD (HML sem container): 12/11/2026 filial 01 NF-e 10 e CT-e 1; filial 02 NF-e 20 e CT-e 1. `KeyCte` da única linha da filial 01 devolve 1 linha da mesma chave. |

---

## PARTE 9 — Formato do report de cada bloco

```
ETAPAS: Tn..Tm   STATUS: DONE | BLOCKED X<n>
HEAD antes/depois · SHAs · git status
INVENTÁRIO: premissas confirmadas / EXECUTION_DRIFT
ARQUIVOS: por serviço e camada
TESTES: comando · PASS/FAIL/TEST_NOT_RUN · comparação com o commit pai
CORREÇÕES AUTÔNOMAS: problema → causa → correção → resultado
AMBIENTE: HML/PROD — publicação, verificações, digests, horários
DOCUMENTOS ATUALIZADOS
PENDÊNCIAS DO OWNER
```
