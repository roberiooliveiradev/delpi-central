# Entry audit (doc 168) — Auditoria de entradas (Protheus × XML de NF-e e CT-e) no Portal e na CLARA

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** |
| Data | 2026-11-13 |
| Decisor | owner do produto |
| Baseline | HEAD `08825074` (somente leitura) |
| Origem | skill `auditoria-entradas-nfe-protheus` + painel «Raio-X das Entradas» (artifact no claude.ai) |
| Pasta | `docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/` — plano (este arquivo), [backend](./backend/README.md), [frontend](./frontend/README.md), [mcp](./mcp/README.md), [reference](./reference/skill-auditoria-entradas-nfe-protheus/) (cópia da skill, sem a SF4), [planning](./planning/planejamento-auditoria-entradas.xlsx) |

Este documento consolida o plano. Ele é discutido no chat e atualizado aqui a cada decisão. Nada de runtime começa antes do gate da fase E1 (contrato).

---

## 1. Objetivo

Levar para o Portal Controladoria & Finanças e para a CLARA a auditoria das notas de entrada, **sob demanda, em qualquer dia que o usuário precisar**,: o confronto do que foi escriturado no Protheus (SF1, SD1, SF4, SFT) com o XML do fornecedor (NF-e e CT-e). O foco é o mesmo da skill: pegar, antes da contabilidade, os erros que ela devolve todo mês (CT-e com crédito indevido ou não tomado, CFOP, CST e origem, base de ICMS/IPI, chave de acesso, CNPJ do fornecedor, espécie, série e data, Simples e crédito presumido de SC).

Resultado esperado:

1. **Página «Auditoria de entradas»** no Portal: escolher o período (De/Até) e as filiais, executar a auditoria, acompanhar o resultado num dashboard (o conteúdo do Raio-X) e marcar ocorrências como resolvidas.
2. **CLARA**: ler o resultado, analisar («o que pede ação em outubro na matriz?»), executar a auditoria e marcar resolvido, ampliando só o catálogo das tools semânticas existentes.

## 2. Situação atual (AS-IS)

| Etapa | Como é hoje |
|---|---|
| Dados do Protheus | exportação manual de SF1, SD1 (e às vezes SFT) em xlsx; SF4 guardada dentro da skill, com aviso quando passa de 90 dias |
| XML | download manual do ZIP de NF-e e CT-e |
| Regras | `scripts/regras.py` da skill (≈ 60 KB); catálogo em `references/regras.md` |
| Saída | planilha `cruzamento_entradas_filial<FF>_<mmmAAAA>.xlsx` |
| Acompanhamento | painel Raio-X: lê a planilha, guarda o histórico **por pessoa**, compara com o mês anterior, marca «resolvido» só para quem marcou |

Limites do AS-IS: trabalho manual a cada execução; SF4 pode estar desatualizada; sem SFT o crédito fica «Depende da TES»; o status de resolvido não é compartilhado pela equipe; a CLARA não enxerga nada disso.

## 3. Decisões

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D1 | Onde fica o motor de regras | **controllership-finance-api (BFF)**, em Clean Architecture: regras puras no domain, fontes por adapters HTTP (api-delpi e financial-api) | recomendação — confirmar |
| D2 | Entrada dos dados | **Automática**: período + tipos de nota + filiais → a BFF busca Protheus (api-delpi) e XML (financial-api/Questor). Upload de arquivos só como alternativa se a listagem do Questor por período não for viável (ver E0) | recomendação — confirmar |
| D3 | Visual | conteúdo do Raio-X no **padrão visual do Portal** (`@delpi/plugin-ui`, claro/escuro); sem copiar o HTML | **DECIDIDO** (owner, 2026-11-13) |
| D4 | Permissões | **`controllership-finance.access`** para tudo desta funcionalidade: ver, executar/reexecutar e marcar resolvido. `manage` herda `access`. Nenhuma permission nova | **DECIDIDO** (owner, 2026-11-13) |
| D5 | Navegação | página própria **«Auditoria de entradas»**, com atalho a partir do Fechamento mensal (abre já com o mês da competência) | recomendação — confirmar |
| D6 | CLARA executa a auditoria | a CLARA tem acesso a todas as funcionalidades e audita as notas **num comando do usuário**; `entry_audit.run`, `resolve` e `reopen` são diretos (sem prepare/confirmação) | **DECIDIDO** (owner, 2026-11-13); execução direta proposta — confirmar |
| D10 | Frequência | auditoria **sob demanda, em qualquer dia**; sem rotina mensal fixa nem agendamento | **DECIDIDO** (owner, 2026-11-13) |
| D8 | Filtros da execução | os **mesmos dois filtros de hoje**: **período De/Até livre** (nenhuma data fixada nem sugerida; pela data de recebimento, como na exportação da SF1) e **tipos de nota** (hoje filtrado no Excel), mais as filiais. Os demais (severidade, tema, fornecedor…) são filtros da análise, sobre o resultado | **DECIDIDO** (owner, 2026-11-13) |
| D9 | Componentes | dashboard com `@delpi/plugin-ui`; primitivos novos criados no plugin-ui e importados pelo Portal; o HTML do Raio-X não é copiado | **DECIDIDO** (owner, 2026-11-13) |
| D7 | Execução | assíncrona, por um worker dentro da BFF (padrão do job de notificações no `lifespan`), uma análise por período com uma execução por filial | recomendação — confirmar |

## 4. Arquitetura (TARGET)

```
Protheus (SF1/SD1/SF4/SFT) ──► api-delpi (SQL canônico TOTVS, só leitura)
                                         │ HTTP
Questor (XML NF-e/CT-e) ──► financial-api ─┤
                                         ▼
     controllership-finance-api
       domain:       motor de regras (porte de regras.py), sem framework/HTTP/DB
       application:  executar auditoria (período, filiais), reexecutar, resolver/reabrir
       adapters:     api-delpi (entradas e TES), financial-api (XML), Postgres (resultado)
                 │                                   │
     MFE controllership-finance              CLARA (read / analyze / execute)
     «Auditoria de entradas»
```

Regras de fronteira (instruções do projeto):

- O MFE só fala com a BFF. A BFF fala com a api-delpi e a financial-api por HTTP; nunca acessa o banco do Protheus nem o banco vizinho.
- O SQL do Protheus fica na api-delpi (owner canônico TOTVS). A busca de XML fica na financial-api (owner do Questor).
- O motor de regras é domínio puro: recebe documentos normalizados (cabeçalho, itens, livro, TES, XML) e devolve ocorrências. Isso permite o teste de paridade com a skill sem rede.

## 4A. Back-end, front-end e MCP

| Parte | Documento |
|---|---|
| Back-end — fluxo, rotas da api-delpi, da financial-api e da BFF, camadas, worker, dados, persistência | [backend/README.md](./backend/README.md) |
| Front-end — dashboard, páginas, dimensionamento, componentes do `@delpi/plugin-ui` e wireframes | [frontend/README.md](./frontend/README.md) |
| MCP (CLARA) — capacidades, conhecimento (fichas AE-00 a AE-15) e diretivas | [mcp/README.md](./mcp/README.md) |
| Referência — cópia da skill `auditoria-entradas-nfe-protheus` | [reference/](./reference/skill-auditoria-entradas-nfe-protheus/) |
| Planejamento — tarefas, dependências e datas | [planning/planejamento-auditoria-entradas.xlsx](./planning/planejamento-auditoria-entradas.xlsx) |

## 5. Ganhos em relação à skill

| Hoje | Com a plataforma |
|---|---|
| SF4 copiada na skill | SF4 lida ao vivo a cada execução |
| SFT quase nunca vem; muito «Depende da TES» | SFT lida ao vivo; o livro fiscal decide o crédito |
| ZIP de XML baixado à mão | XML buscado no Questor pela financial-api |
| Resolvido por pessoa, no navegador | Resolvido compartilhado, com quem resolveu e quando, preservado entre reexecuções |
| CLARA sem acesso | CLARA lê, analisa, executa e resolve |

## 6. Fases

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
| E7 | Ensaio HML com período real (outubro/2026, filiais 01 e 02) → PROD | paridade em HML + publicação |

## 7. Critério central de aceite: paridade

Para a mesma filial e período, com os mesmos dados de entrada, o motor da BFF produz **as mesmas ocorrências** que a skill: mesma nota, item, ocorrência, campo e severidade, e os mesmos valores (tolerância de R$ 0,05).

Diferenças só são aceitas quando explicadas pela fonte ao vivo e documentadas, por exemplo: SF4 mais nova que a cópia da skill; SFT presente decidindo um «Depende da TES».

## 8. Riscos

| Risco | Mitigação |
|---|---|
| Questor sem listagem por período | E0 prova; alternativa de upload (D2) |
| Volume (centenas de XML por mês) e tempo de execução | execução assíncrona com andamento; cache de XML por chave |
| Mapeamento da SFT nunca validado com dado real (aviso da própria skill) | E0/E2 com SFT real da Delpi |
| Regras da empresa («não apontado») se perderem no porte | paridade E2 inclui o bloco «Não apontado» do Resumo |
| Repositório público | o anexo traz só regras e scripts; a cópia da SF4 (cadastro de TES) não foi versionada |

## 9. Fora do escopo

Lançar ou corrigir notas no Protheus; alterar TES ou cadastro de fornecedor; substituir a contabilidade. A auditoria aponta e explica; a correção continua no ERP.

## 10. Registro

| Data | Evento |
|---|---|
| 2026-11-13 | Owner: como na skill e no painel, nada de período fixado — o período é De/Até livre; o segundo filtro de execução é o **tipo de nota**. Removidos os atalhos de período (`PeriodRangeFilter` e a evolução do util de períodos saíram do plano: usa-se `DateField` ×2) e os «parâmetros avançados» da tela (viram configuração da BFF). Tipos de nota a confirmar com os exemplos do Gustavo. |
| 2026-11-13 | Plano reorganizado na pasta `entry-audit/` (plan, backend, frontend, mcp, reference, planning). |
| 2026-11-13 | Plano criado. D4 decidida pelo owner (tudo com `controllership-finance.access`). D1, D2, D3 e D5 com recomendação, aguardando confirmação. Skill anexada como referência para o porte. |
| 2026-11-13 | Conhecimento e capacidades da CLARA organizados em [mcp/README.md](./mcp/README.md): domínio `controllership`, 16 fichas, catálogo, diretivas e 7 perguntas ao owner. |
| 2026-11-13 | Detalhamento das páginas em `frontend/` (README e 01 a 04): dimensionamento, componentes do plugin-ui com props, dados e estados; especificação dos 3 primitivos novos e das 4 evoluções aditivas (inclui `ComparativeAreaChart` com clique no dia). Rota nova `GET /entry-audit/analyses/options`. |
| 2026-11-13 | Dashboard: período livre (D8), plugin-ui com primitivos novos no kit (D9), D3 decidida. Rotas da BFF refeitas em torno da análise por período (backend §3.3) e rotas do dashboard; persistência ajustada (§7); wireframes (§8 e anexo HTML); CLARA explica o dashboard e sugere direcionamentos. |
| 2026-11-13 | Estrutura do back-end (backend): rotas da api-delpi, da financial-api e da BFF; organização em camadas; worker; cache de XML; CLARA executando a auditoria num comando (D6). Visual da página fica para a próxima rodada. Planejamento em tabela à parte (`planejamento-auditoria-entradas.xlsx`). |
