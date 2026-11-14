# 168 — Auditoria de entradas (Protheus × XML de NF-e e CT-e) no Portal e na CLARA

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** |
| Data | 2026-11-13 |
| Decisor | owner do produto |
| Baseline | HEAD `08825074` (somente leitura) |
| Origem | skill `auditoria-entradas-nfe-protheus` + painel «Raio-X das Entradas» (artifact no claude.ai) |
| Anexo | [168-anexos/skill-auditoria-entradas-nfe-protheus](./168-anexos/skill-auditoria-entradas-nfe-protheus/) — cópia da skill (SKILL.md, `references/regras.md`, `scripts/*.py`), sem a cópia da SF4 |

Este documento consolida o plano. Ele é discutido no chat e atualizado aqui a cada decisão. Nada de runtime começa antes do gate da fase E1 (contrato).

---

## 1. Objetivo

Levar para o Portal Controladoria & Finanças e para a CLARA a auditoria mensal das notas de entrada: o confronto do que foi escriturado no Protheus (SF1, SD1, SF4, SFT) com o XML do fornecedor (NF-e e CT-e). O foco é o mesmo da skill: pegar, antes da contabilidade, os erros que ela devolve todo mês (CT-e com crédito indevido ou não tomado, CFOP, CST e origem, base de ICMS/IPI, chave de acesso, CNPJ do fornecedor, espécie, série e data, Simples e crédito presumido de SC).

Resultado esperado:

1. **Página «Auditoria de entradas»** no Portal: escolher filial e competência, executar a auditoria, ver o resultado (o conteúdo do Raio-X) e marcar ocorrências como resolvidas.
2. **CLARA**: ler o resultado, analisar («o que pede ação em outubro na matriz?»), executar a auditoria e marcar resolvido, ampliando só o catálogo das tools semânticas existentes.

## 2. Situação atual (AS-IS)

| Etapa | Como é hoje |
|---|---|
| Dados do Protheus | exportação manual de SF1, SD1 (e às vezes SFT) em xlsx; SF4 guardada dentro da skill, com aviso quando passa de 90 dias |
| XML | download manual do ZIP de NF-e e CT-e |
| Regras | `scripts/regras.py` da skill (≈ 60 KB); catálogo em `references/regras.md` |
| Saída | planilha `cruzamento_entradas_filial<FF>_<mmmAAAA>.xlsx` |
| Acompanhamento | painel Raio-X: lê a planilha, guarda o histórico **por pessoa**, compara com o mês anterior, marca «resolvido» só para quem marcou |

Limites do AS-IS: trabalho manual a cada mês; SF4 pode estar desatualizada; sem SFT o crédito fica «Depende da TES»; o status de resolvido não é compartilhado pela equipe; a CLARA não enxerga nada disso.

## 3. Decisões

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D1 | Onde fica o motor de regras | **controllership-finance-api (BFF)**, em Clean Architecture: regras puras no domain, fontes por adapters HTTP (api-delpi e financial-api) | recomendação — confirmar |
| D2 | Entrada dos dados | **Automática**: filial + competência → a BFF busca Protheus (api-delpi) e XML (financial-api/Questor). Upload de arquivos só como alternativa se a listagem do Questor por período não for viável (ver E0) | recomendação — confirmar |
| D3 | Visual | conteúdo do Raio-X no **padrão visual do Portal** (`@delpi/plugin-ui`, claro/escuro), tons de verde nos gráficos; sem o fundo animado | recomendação — confirmar |
| D4 | Permissões | **`controllership-finance.access`** para tudo desta funcionalidade: ver, executar/reexecutar e marcar resolvido. `manage` herda `access`. Nenhuma permission nova | **DECIDIDO** (owner, 2026-11-13) |
| D5 | Navegação | página própria **«Auditoria de entradas»**, com atalho a partir do Fechamento mensal da competência | recomendação — confirmar |
| D6 | CLARA executa a auditoria | a CLARA tem acesso a todas as funcionalidades e audita as notas **num comando do usuário**; `entry_audit.run`, `resolve` e `reopen` são diretos (sem prepare/confirmação) | **DECIDIDO** (owner, 2026-11-13); execução direta proposta — confirmar |
| D7 | Execução | assíncrona, por um worker dentro da BFF (padrão do job de notificações no `lifespan`), uma execução por filial e competência | recomendação — confirmar |

## 4. Arquitetura (TARGET)

```
Protheus (SF1/SD1/SF4/SFT) ──► api-delpi (SQL canônico TOTVS, só leitura)
                                         │ HTTP
Questor (XML NF-e/CT-e) ──► financial-api ─┤
                                         ▼
     controllership-finance-api
       domain:       motor de regras (porte de regras.py), sem framework/HTTP/DB
       application:  executar auditoria (filial, competência), reexecutar, resolver/reabrir
       adapters:     api-delpi (entradas e TES), financial-api (XML), Postgres (resultado)
                 │                                   │
     MFE controllership-finance              CLARA (read / analyze / execute)
     «Auditoria de entradas»
```

Regras de fronteira (instruções do projeto):

- O MFE só fala com a BFF. A BFF fala com a api-delpi e a financial-api por HTTP; nunca acessa o banco do Protheus nem o banco vizinho.
- O SQL do Protheus fica na api-delpi (owner canônico TOTVS). A busca de XML fica na financial-api (owner do Questor).
- O motor de regras é domínio puro: recebe documentos normalizados (cabeçalho, itens, livro, TES, XML) e devolve ocorrências. Isso permite o teste de paridade com a skill sem rede.

## 4A. Estrutura do back-end (TARGET — revisar na E1)

### 4A.1 Fluxo de uma auditoria

1. Alguém pede a auditoria: botão na página **ou** um comando à CLARA («audita as entradas de outubro»).
2. A BFF cria uma **execução** por filial (`entry_audit_run`, status `queued`) e responde na hora com o identificador. Se já existe uma execução em andamento para a mesma filial e competência, devolve a mesma (idempotente).
3. Um **worker dentro da BFF** pega a execução. É o mesmo padrão do job de notificações que já roda no `lifespan` da BFF (`startup/notification_dispatch_job`).
4. O worker busca as fontes:
   - Protheus pela api-delpi: SF1, SD1, SF4, SFT e fornecedores (SA2) da filial no período de recebimento;
   - XML pela financial-api: NF-e e CT-e recebidos da filial no período, com eventos de cancelamento. XML já baixado antes é reaproveitado do cache por chave de acesso, porque XML não muda.
5. O worker roda o **motor de regras** (domínio puro) e grava o resultado: notas casadas, ocorrências, notas sem par, CT-e, TES usadas.
6. O status de «resolvido» das ocorrências que continuam existindo é mantido pela **chave estável**.
7. A execução termina como `done` (ou `failed`, com o motivo). A página acompanha o andamento; a CLARA consulta o status e, ao terminar, apresenta o resultado.

### 4A.2 api-delpi — leitura do Protheus (owner TOTVS)

Prefixo no padrão dos relatórios financeiros: `/financeiro/entry-audit`. Só leitura, paginado, sem regra fiscal (a regra fica no motor da BFF).

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /financeiro/entry-audit/documents` | `branch`, `received_from`, `received_to`, `page`, `page_size` | cabeçalhos SF1 + CNPJ/UF do fornecedor (SA2) |
| `GET /financeiro/entry-audit/items` | mesmos filtros | itens SD1 dos mesmos documentos |
| `GET /financeiro/entry-audit/fiscal-book` | mesmos filtros | itens do livro fiscal (SFT) dos mesmos documentos |
| `GET /financeiro/entry-audit/tes` | — | cadastro de TES (SF4) inteiro |
| `GET /financeiro/entry-audit/branches` | — | filiais com CNPJ e UF |

A E0 confirma se já existe SQL reaproveitável para algum destes (há consultas de SF1/SD1 em compras e estoque).

### 4A.3 financial-api — XML do Questor (owner)

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /invoices/received/export` | `branch`, `type` (`nfe` \| `cte`), `issued_from`, `issued_to`, `page`, `page_size` | lista com chave, número, série, emitente, emissão, valor, situação e os ids do provedor para baixar o XML |
| `GET /invoices/received/{id}/xml/original` | `branch`, `type` | XML original (já existe para CT-e e NFS-e; a NF-e usa `download_nfe_xml`) |

**Lacuna:** a listagem atual do Questor (`/cliente/nfe/listagem`) não recebe data. Ela vem ordenada por emissão (`orderGroup=Emission`) e só com entradas (`Entry=True`). A E0 prova se aceita filtro de data; se não aceitar, a financial-api pagina pela emissão e para quando passar do início do período. A entrada automática continua viável nos dois casos.

### 4A.4 controllership-finance-api — rotas da BFF

Prefixo `/entry-audit`. Todas exigem `controllership-finance.access` (D4). `branch=all` vale nas leituras (consolidado) e, no POST, cria uma execução por filial.

| Método e rota | Uso |
|---|---|
| `POST /entry-audit/runs` | body `{competence, branch}` → 202 com as execuções criadas (ou as que já estão em andamento) |
| `GET /entry-audit/runs` | execuções por `competence`/`branch` (histórico) |
| `GET /entry-audit/runs/{run_id}` | status, andamento (etapa, documentos lidos, XML baixados), contagens, erro |
| `GET /entry-audit/summary` | KPIs da competência (última execução concluída), comparação com o mês anterior, ocorrências por severidade e por tema, top fornecedores, divergências por dia |
| `GET /entry-audit/occurrences` | filtros `severity`, `theme`, `supplier`, `status` (`pending`\|`resolved`\|`all`), `q`, paginação |
| `GET /entry-audit/documents` | notas casadas com situação e número de ocorrências |
| `GET /entry-audit/unmatched` | notas só no XML / só no SF1, com motivo |
| `GET /entry-audit/cte` | comparativo dos CT-e (direito ao crédito, CFOP esperado, base, alíquota, ICMS, CST) |
| `GET /entry-audit/tes` | TES usadas na competência, com a configuração da SF4 e os alertas |
| `POST /entry-audit/occurrences/{key}/resolve` · `/reopen` | status compartilhado; registra quem e quando |
| `POST /entry-audit/unmatched/{key}/resolve` · `/reopen` | idem para notas sem par |
| `GET /entry-audit/export` | planilha no layout atual da skill (para a contabilidade) |

Envelope, erros e `meta` iguais aos das outras rotas da BFF.

### 4A.5 Organização do código na BFF (Clean Architecture)

| Camada | Pasta | Conteúdo |
|---|---|---|
| domain | `domain/entry_audit/` | modelos (documento, item, livro, TES, XML NF-e/CT-e, ocorrência, severidade, tema); casamento SF1×XML (inclusive troca de chave) e SD1×itens; regras separadas por grupo (cabeçalho, itens, coerência, Simples/presumido SC, CT-e, chave/espécie/fornecedor, livro fiscal, sem par, «não apontado»); motor que junta tudo |
| application | `application/entry_audit/` | executar, consultar, resolver/reabrir, exportar; portas (`ProtheusEntriesPort`, `FiscalXmlPort`, `EntryAuditRepository`) |
| infrastructure | `infrastructure/entry_audit/` | gateway api-delpi, gateway financial-api, leitura dos XML (porte de `leitura.py`), repositório Postgres, cache de XML, exportação xlsx (porte de `relatorio.py`) |
| interface | `interface/http/routes/entry_audit/` · `interface/mcp/` | rotas HTTP; entradas da CLARA no catálogo semântico |
| startup | `startup/entry_audit_worker.py` | worker no `lifespan`; ao subir, devolve para a fila as execuções que estavam rodando quando o processo parou |

### 4A.6 Persistência

Migration `V023` no schema `controllership_finance`, com as tabelas da seção 7 e mais `entry_audit_xml_cache` (chave de acesso, modelo, XML compactado, data da busca).

### 4A.7 CLARA — «audita todas as notas» num comando

| Pedido do usuário | O que a CLARA faz |
|---|---|
| «Audita as entradas de outubro» | `execute entry_audit.run {competence: 2026-10, branch: all}` → recebe as execuções; consulta `read entry_audit.run` até terminar; chama `analyze entry_audit_findings`; responde no formato da skill: o que pede ação, o que corrigir, o que não tem impacto |
| «O que ainda está pendente na matriz?» | `read entry_audit.occurrences {branch: 01, status: pending}` |
| «Por que essa CT-e deu alta?» | `read` da ocorrência + `knowledge` com a regra citada |
| «Marca a NF 123 da WEG como resolvida» | `execute entry_audit.resolve` |

A execução é **direta**, sem prepare/confirmação: não altera dado de negócio (só cria o resultado da auditoria), é idempotente por filial e competência e o owner quer que a CLARA faça o trabalho num comando só (D6). Resolver e reabrir também são diretos.

## 5. Ganhos em relação à skill

| Hoje | Com a plataforma |
|---|---|
| SF4 copiada na skill | SF4 lida ao vivo a cada execução |
| SFT quase nunca vem; muito «Depende da TES» | SFT lida ao vivo; o livro fiscal decide o crédito |
| ZIP de XML baixado à mão | XML buscado no Questor pela financial-api |
| Resolvido por pessoa, no navegador | Resolvido compartilhado, com quem resolveu e quando, preservado entre reexecuções |
| CLARA sem acesso | CLARA lê, analisa, executa e resolve |

## 6. Dados necessários (a confirmar na E0)

| Fonte | Campos usados pelo motor (ver `scripts/regras.py`) | Owner |
|---|---|---|
| SF1 | filial, documento, série, fornecedor/loja, espécie, chave, emissão, recebimento, valores (bruto, mercadorias, ICMS, base, IPI, ST, frete, despesa, desconto) | api-delpi |
| SD1 | item, produto, CFOP, CST/`D1_CLASFIS`, TES, quantidade, total, ICMS/base/alíquota, IPI/base, ICMS ST, desconto | api-delpi |
| SF4 | código, crédito ICMS, livro ICMS, crédito IPI, livro IPI, material de consumo, cálculo de ICMS/IPI | api-delpi |
| SFT | documento, série, fornecedor/loja, item, valor ICMS/IPI creditado | api-delpi |
| SA2 | CNPJ e UF do fornecedor por código/loja | api-delpi |
| XML NF-e e CT-e | todos os documentos recebidos da competência por CNPJ destinatário/tomador, com eventos de cancelamento | financial-api |
| Empresa | CNPJ e UF de cada filial (01, 02) | a inventariar |

**Lacuna conhecida:** a listagem atual de notas recebidas da financial-api (`ReceivedInvoiceQuery`) filtra por número, CNPJ do fornecedor e valor, **não por período**. A E0 precisa provar se o Questor permite listar por data de emissão/recebimento e CNPJ do destinatário. Se não permitir, D2 cai para upload do ZIP.

## 7. Persistência (TARGET, schema `controllership_finance`)

| Tabela | Conteúdo |
|---|---|
| `entry_audit_run` | filial, competência, status (`running`/`done`/`failed`), início/fim, quem executou, contagens, versão do motor, hash das fontes |
| `entry_audit_document` | notas casadas (cabeçalho comparado), situação |
| `entry_audit_occurrence` | ocorrência: chave estável, severidade, tema, ocorrência, NF, fornecedor, item, campo, valor Protheus, valor XML, diferença, TES, ação sugerida |
| `entry_audit_unmatched` | notas só no XML / só no SF1, com motivo e situação |
| `entry_audit_occurrence_status` | resolvido/reaberto por **chave estável** (filial + competência + documento + ocorrência + campo + item), quem e quando |

A chave estável é a mesma ideia do painel atual: uma reexecução substitui o resultado, mas a ocorrência que continua existindo mantém o status de resolvida.

## 8. Página «Auditoria de entradas» (conteúdo do Raio-X)

- Filtros: filial (01, 02, consolidado), competência, severidade.
- Ação: **Executar auditoria** / **Reexecutar**, com andamento e data da última execução.
- KPIs: valor conferido, notas sem divergência, ocorrências pendentes, diferença nas altas; comparação com o mês anterior.
- Gráficos: notas com divergência por dia de emissão; conformidade (sem divergência, com divergência, sem par a resolver, sem par explicadas); top fornecedores; ocorrências por tema (ICMS, IPI, CFOP, CST e origem, Simples e presumido, Valores e datas, Livro fiscal). Clique filtra a página inteira.
- Tabela: Ocorrências (pendentes/resolvidas/todas), Notas casadas, Notas sem par; busca; ordenação; **Resolver / Reabrir**.
- Novidade em relação ao painel: aba **CT-e** (hoje o painel não lê o CT-e Comparativo) e aba **TES usadas** (configuração da SF4 do período).
- Exportar a planilha no layout atual (para a contabilidade).
- Ajuda no mesmo gate: o que cada severidade significa e o «não apontado» da regra da empresa.

## 9. CLARA (só catálogo; sem tools novas)

| Tool | Entrada | Uso |
|---|---|---|
| `read` | `entry_audit.summary` | resumo da competência por filial |
| `read` | `entry_audit.occurrences` | ocorrências com filtros (severidade, tema, fornecedor, status) |
| `read` | `entry_audit.unmatched` | notas sem par |
| `analyze` | `analysis_type=entry_audit_findings` | FACT/RECOMMENDATION agrupado por causa (TES, cadastro, fornecedor), no formato «o que pede ação / corrigir / sem impacto» da skill |
| `read` | `entry_audit.run` | status e andamento de uma execução |
| `execute` | `entry_audit.run` | executar/reexecutar a auditoria de uma competência (uma filial ou todas), **direto** (D6) |
| `execute` | `entry_audit.resolve` / `entry_audit.reopen` | marcar status (direto, baixo impacto) |
| `knowledge` | domínio Controladoria | catálogo de regras (`references/regras.md`) como conhecimento citável |

Gate de todas as entradas: `controllership-finance.access` (D4).

## 10. Fases

Regra de trabalho: teste de comportamento em HML; passou tudo, vai para PROD. Funcionalidade entra desligada por flag e é ligada depois do ensaio HML.

| Fase | Entrega | Saída |
|---|---|---|
| E0 | Inventário somente leitura: SQL existente na api-delpi para SF1/SD1/SF4/SFT/SA2; capacidade do Questor de listar por período e destinatário; CNPJ/UF das filiais; volume mensal por filial | lacuna do Questor resolvida ou D2 revista |
| E1 | Contrato: endpoints novos (api-delpi, financial-api, BFF), schema, catálogo CLARA, rotas do MFE | doc 168 com contrato `ACCEPTED` |
| E2 | Motor de regras no domain da BFF + **teste de paridade** com a skill sobre arquivos reais de um mês | paridade PASS |
| E3 | Fontes: endpoints de leitura na api-delpi; listagem por período na financial-api | testes de contrato PASS |
| E4 | Execução, persistência, reexecução com status preservado, exportação xlsx | testes PASS |
| E5 | Página no MFE + Ajuda | testes e build PASS |
| E6 | CLARA: catálogo, analyze, conhecimento | testes PASS |
| E7 | Ensaio HML com competência real (outubro/2026, filiais 01 e 02) → PROD | paridade em HML + publicação |

## 11. Critério central de aceite: paridade

Para a mesma filial e competência, com os mesmos dados de entrada, o motor da BFF produz **as mesmas ocorrências** que a skill: mesma nota, item, ocorrência, campo e severidade, e os mesmos valores (tolerância de R$ 0,05).

Diferenças só são aceitas quando explicadas pela fonte ao vivo e documentadas, por exemplo: SF4 mais nova que a cópia da skill; SFT presente decidindo um «Depende da TES».

## 12. Riscos

| Risco | Mitigação |
|---|---|
| Questor sem listagem por período | E0 prova; alternativa de upload (D2) |
| Volume (centenas de XML por mês) e tempo de execução | execução assíncrona com andamento; cache de XML por chave |
| Mapeamento da SFT nunca validado com dado real (aviso da própria skill) | E0/E2 com SFT real da Delpi |
| Regras da empresa («não apontado») se perderem no porte | paridade E2 inclui o bloco «Não apontado» do Resumo |
| Repositório público | o anexo traz só regras e scripts; a cópia da SF4 (cadastro de TES) não foi versionada |

## 13. Fora do escopo

Lançar ou corrigir notas no Protheus; alterar TES ou cadastro de fornecedor; substituir a contabilidade. A auditoria aponta e explica; a correção continua no ERP.

## 14. Registro

| Data | Evento |
|---|---|
| 2026-11-13 | Plano criado. D4 decidida pelo owner (tudo com `controllership-finance.access`). D1, D2, D3 e D5 com recomendação, aguardando confirmação. Skill anexada como referência para o porte. |
| 2026-11-13 | Estrutura do back-end (§4A): rotas da api-delpi, da financial-api e da BFF; organização em camadas; worker; cache de XML; CLARA executando a auditoria num comando (D6). Visual da página fica para a próxima rodada. Planejamento em tabela à parte (`planejamento-auditoria-entradas.xlsx`). |
