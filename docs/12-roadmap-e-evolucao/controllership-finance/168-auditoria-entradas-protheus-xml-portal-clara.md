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
| `execute` | `entry_audit.run` | executar/reexecutar (governado: prepare → confirmação → commit) |
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
