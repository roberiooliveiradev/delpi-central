# Entry audit · MCP (CLARA) — conhecimento e capacidades

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** |
| Data | 2026-11-13 |
| Plano | [../plan.md](../plan.md) · back-end [../backend/README.md](../backend/README.md) · front-end [../frontend/README.md](../frontend/README.md) |
| Origem do conhecimento | skill `auditoria-entradas-nfe-protheus` ([reference](../reference/skill-auditoria-entradas-nfe-protheus/)) + regras ditas pelo owner + este plano |
| Baseline | HEAD `08825074` |

Este documento organiza **o que a CLARA precisa saber e poder fazer** para auditar as entradas num comando, explicar o dashboard e sugerir direcionamentos. Ele separa três coisas que vivem em lugares diferentes no código:

| Camada | O que é | Onde vive hoje (PROVEN) |
|---|---|---|
| **Capacidades** | o que ela pode fazer (ler, analisar, executar, resolver) | catálogo semântico em `controllership-finance-api/…/interface/mcp/semantic_bridge.py` (+ bridges) |
| **Conhecimento citável** | o que ela consulta e cita com fonte | corpus governado: manifestos `application/clara/corpus_manifest.py` (domínio `controllership`) e `corpus_manifest_lnf.py` (domínio `lancamento-notas-fiscais`); ingestão em `corpus_ingestion.py`, que corta o markdown por título (até 6.000 caracteres por trecho) e grava cada trecho com fonte, localizador, classificação de evidência, `access_scope` e `domain_scope` |
| **Diretivas de conduta** | como ela conduz a conversa | instruções do servidor MCP em `interface/mcp/branding.py` e as descrições do catálogo. O perfil da personagem (`content/clara_agent_intelligence.json`) é identidade e não concede regra nem capacidade |

Regra do corpus já vigente: a ficha **interpreta**; o dado vem sempre de `read`/`analyze`. A CLARA nunca afirma como fato o que está `TO_INVENTORY`/`PENDING`.

## 1. Domínio do conhecimento

O conhecimento da auditoria entra no domínio **`controllership`**, liberado por `controllership-finance.access` — a mesma permissão das funcionalidades (D4). Não é preciso um domínio novo nem mudar a restrição criada na `V022`. Quem só tem permissões do LNF não vê esse conhecimento, como hoje.

## 2. Conhecimento a passar — inventário

Formato: **fichas** em markdown, no mesmo padrão das fichas R01–R15 (`fichas/`): cabeçalho com versão, títulos curtos (cada título vira um trecho citável) e classificação de evidência por afirmação. Pasta proposta: `docs/12-roadmap-e-evolucao/controllership-finance/fichas/auditoria-entradas/`, registrada no `corpus_manifest.py`.

| ID | Ficha | Conteúdo | Fonte | Classificação inicial → após E7 |
|---|---|---|---|---|
| **AE-00** | Visão geral da auditoria de entradas | finalidade (pegar antes da contabilidade os erros que ela devolve); o que é comparado (SF1 × totais do XML, SD1 × itens, CT-e, chave/espécie/fornecedor, livro fiscal); fontes ao vivo; eixo do período (recebimento na SF1, emissão no XML, com folga); casamento pela chave e troca de chave; tolerância de R$ 0,05; severidades; temas; o que sai (abas); resolvido por chave estável; limites (não lança nem corrige no ERP) | SKILL.md, regras.md, plano 168 | `OWNER_REPORTED_VIA_PO` / `TARGET` → `CURRENT_IMPLEMENTATION` |
| **AE-01** | Regras do cabeçalho | uma seção por ocorrência (ver §3) | regras.md «Cabeçalho» + regras.py | `OWNER_REPORTED_VIA_PO` → `CURRENT_IMPLEMENTATION` |
| **AE-02** | Regras dos itens | idem | regras.md «Itens» | idem |
| **AE-03** | Coerência interna (vale sem XML) | CFOP × UF, IPI em consumo, ICMS em CFOP de consumo, CST sem tributação | regras.md «Coerência interna» | idem |
| **AE-04** | Simples Nacional e crédito presumido de SC | teto do pCredSN, sublimite, CSOSN sem alíquota, TES 004, cadastro no Configurador de Tributos | regras.md + SKILL.md + owner | idem |
| **AE-05** | CT-e (frete) | direito ao crédito pelo `infDoc`, CFOP esperado (1/2/3 + 352), tomador, CST 090, TES de frete com e sem crédito | regras.md «CT-e» + SKILL.md | idem |
| **AE-06** | Chave, espécie, série e fornecedor | troca de chave, DV, modelo × espécie, CNPJ do fornecedor | regras.md | idem |
| **AE-07** | Livro fiscal (SFT) | as quatro conferências do livro; o livro decide o crédito | regras.md + SKILL.md | idem; mapeamento da SFT `TO_INVENTORY` até a E0/E2 |
| **AE-08** | Notas sem par | só no XML / só no Protheus, motivos e situação (Info por período, saída própria, cancelada) | regras.md «Notas sem par» | idem |
| **AE-09** | Regras da empresa — o que não se aponta | ICMS/IPI em TES de consumo/insumo que não credita; CST 090 em TES sem crédito; CST 060 em combustível e ST; o bloco «Não apontado» do resumo | SKILL.md + owner | `APPROVED_RULE` (decisão do owner) |
| **AE-10** | Crédito: TES × livro fiscal | `D1_VALICM` não é crédito; ordem de decisão (SFT → TES coerente → «Depende da TES»); SPED lê o livro (C190/E110); nunca afirmar crédito indevido sem SF4/SFT | SKILL.md | `APPROVED_RULE` |
| **AE-11** | Base legal citada | LC 123 (teto do pCredSN: Anexo II 3,944%, Anexo I 3,978% — cálculo); RICMS/SC Anexo 2 art. 15 XXVI (presumido 7%) e § 25; COPAT 84/2025 e 75/2022 | SKILL.md | **`TO_INVENTORY`** até anexar o texto oficial vigente de cada norma como fonte |
| **AE-12** | Glossário fiscal e do Protheus | SF1, SD1, SF4 (campos que importam), SFT, SA2; TES; grupos de CFOP (insumo/revenda, consumo, ativo, frete, ST); CST, CSOSN, CRT, origem; estrutura da chave (modelo 21–22, série 23–25, número 26–34, DV módulo 11); espécies; tomador do CT-e; eventos de cancelamento | regras.md + SKILL.md | `APPROVED_RULE` |
| **AE-13** | Como ler o dashboard | os 4 KPIs e a conta de cada um; conformidade (4 grupos); temas e severidades; comparação com o período anterior; filtros da execução × da análise; resolvido por chave estável; reexecução | front-end README e páginas 01–03 | `TARGET` → `CURRENT_IMPLEMENTATION` após E5/E7 |
| **AE-14** | Como a CLARA conduz a auditoria | roteiro do §5, em forma citável (o mesmo texto, resumido, vai para as diretivas) | SKILL.md «Como apresentar» + plano | `APPROVED_RULE` |
| **AE-15** | Casos reais | exemplos de ocorrências típicas da Delpi com a correção feita (fornecedor, NF, o que estava errado, como foi corrigido) | **owner + primeira execução real** | `TO_INVENTORY` |

## 3. Formato de cada regra (AE-01 a AE-08)

Cada ocorrência vira uma seção própria, com o **nome exatamente igual ao que o motor grava** (a CLARA casa a ocorrência lida com a regra pelo nome):

```markdown
### CT-e: crédito de ICMS em frete sem direito

- Severidade padrão: Alta
- Quando aparece: a TES (ou o livro fiscal) credita ICMS e o frete não dá direito (NF transportadas só de uso e consumo/ativo, transportadora do Simples ou CT-e sem ICMS).
- Por quê importa: o crédito vai para a apuração (SPED) sem direito; é crédito indevido a estornar.
- O que fazer: lançar o CT-e na TES de frete sem crédito, com CST 090.
- Quem corrige: Fiscal (lançamento) — confirmar com o owner (§7).
- Como a CLARA explica: citar as NF transportadas e o CFOP delas; dizer se foi decidido pela TES ou pelo livro.
- Evidência: OWNER_REPORTED_VIA_PO (skill) · após a paridade E2/E7: CURRENT_IMPLEMENTATION.
```

O catálogo da skill tem cerca de 67 linhas de regra em `regras.md`. Os textos de «o que fazer» que o motor gera hoje estão em `scripts/regras.py` e são a fonte do campo «O que fazer». Na E2 (porte do motor), cada regra ganha um identificador estável (ex.: `cte.credit_without_right`) que aparece na ocorrência, na ficha e no detalhe da página 03.

## 4. Capacidades (catálogo semântico)

Mesmas seis tools; só entradas novas no catálogo, todas com gate `controllership-finance.access`:

| Tool | `entity.action` | Modo | Parâmetros | Para quê |
|---|---|---|---|---|
| `read` | `entry_audit.options` | — | — | filiais permitidas e tipos de nota (com o padrão) |
| `read` | `entry_audit.analysis` | — | `ref` (id) ou filtros `date_from`, `date_to`, `branch`, `status` | histórico; status e andamento de uma análise |
| `read` | `entry_audit.summary` | — | `ref` + filtros da análise | os KPIs e a conformidade do dashboard |
| `read` | `entry_audit.daily` | — | idem | divergências por dia × período anterior |
| `read` | `entry_audit.breakdowns` | — | idem | severidade, tema, fornecedores, TES |
| `read` | `entry_audit.trend` | — | `branch`, `date_from`, `date_to` | evolução entre análises |
| `read` | `entry_audit.occurrences` | — | `ref` + filtros + `page` | lista de ocorrências |
| `read` | `entry_audit.occurrence` | — | `ref` (análise) + `key` | detalhe com por quê, o que fazer, regra e histórico |
| `read` | `entry_audit.documents` / `entry_audit.unmatched` / `entry_audit.cte` / `entry_audit.tes` | — | `ref` + filtros | as demais abas |
| `analyze` | `analysis_type=entry_audit_findings` | — | `ref`, filtros, `compare_to` (outra análise, opcional) | achados FACT/RECOMMENDATION agrupados por causa (TES, cadastro, fornecedor), no formato da skill, com direcionamentos e comparação |
| `execute` | `entry_audit.run` | **direto** (D6) | `date_from`, `date_to`, `note_types` (padrão: os da página), `branches` (padrão: todas permitidas) | executa a auditoria; idempotente |
| `execute` | `entry_audit.rerun` | **direto** | `ref`, `branches` | reexecuta, inclusive só a filial que falhou |
| `execute` | `entry_audit.resolve` / `entry_audit.reopen` | **direto** | `key`, `kind` (`occurrence`\|`unmatched`) | status compartilhado |
| `knowledge` | domínio `controllership` | — | `query` | fichas AE-00 a AE-15 |

Cada entrada tem `description` curta no catálogo e contrato em `get_context(topic='schema')`, como as do LNF.

## 5. Diretivas de conduta (texto para `branding.py`)

Proposta de bloco a acrescentar às instruções do servidor (PT-BR na conversa; o texto técnico do bloco segue o idioma atual das instruções):

1. **Pedido de auditoria** («audita as entradas», «confere as notas de outubro»): a auditoria é **sob demanda, em qualquer dia** (decisão do owner): chamar `execute entry_audit.run` com o período pedido e todas as filiais permitidas; usar **o período (De/Até) e os tipos de nota que o usuário disser** — os mesmos dois filtros que ele aplica hoje na exportação e no Excel; converter expressões como «ontem» ou «outubro» em datas no fuso `America/Sao_Paulo` e repetir as datas na resposta; se faltar o período, **perguntar** («de que data até que data?») em vez de supor; sem tipos de nota ditos, usar o padrão da página e dizer quais foram. Dizer que a execução começou; acompanhar com `read entry_audit.analysis` até `done`/`failed`; não inventar resultado parcial.
2. **Apresentar o resultado** (formato da skill): uma linha com o casamento (notas e CT-e casados, quantas sem divergência, filiais, período) → **o que pede ação** (Alta), agrupado **pela causa** (a TES ou o cadastro que gera o erro), com fornecedor, NF e valor → **corrigir/verificar** (Média) → **sem impacto** (Baixa) numa frase → notas sem par só as que não se explicam por período. O bloco «Não apontado» só se o usuário perguntar.
3. **Explicar o dashboard**: usar `summary`, `daily` e `breakdowns` da mesma análise e filtros que o usuário está vendo; dizer o que cada número conta (ficha AE-13).
4. **Direcionamentos**: sugerir a correção certa para cada causa (ex.: cadastrar o fornecedor no Configurador de Tributos; corrigir a TES X; pedir o XML que falta), citando a ficha da regra. Recomendação é RECOMMENDATION, nunca fato.
5. **Honestidade específica**:
   - `D1_VALICM` preenchido não é crédito; sem SF4/SFT, falar em «ICMS calculado» e «depende da TES»;
   - filial que falhou é **indisponível**, não zero;
   - análise em andamento não tem resultado;
   - diferença de período é normal (SF1 por recebimento, XML por emissão);
   - a CLARA aponta e explica; quem corrige é o usuário no Protheus.
6. **Resolver**: marcar como resolvida só quando o usuário pedir, citando a ocorrência exata; nunca resolver em lote por inferência.

## 6. O que muda em cada fase

| Fase | Conhecimento e capacidades |
|---|---|
| E1 (contrato) | este documento aceito; lista final das entradas do catálogo e do texto das diretivas |
| E2 (motor) | identificador estável por regra; textos de «por quê» e «o que fazer» saem do motor e alimentam as fichas |
| E6 (CLARA) | fichas AE-00 a AE-14 escritas e registradas no `corpus_manifest.py` (domínio `controllership`); catálogo e diretivas implementados; testes MCP |
| E7 (HML → PROD) | publicação governada do corpus; classificações sobem para `CURRENT_IMPLEMENTATION` onde a paridade passou; AE-15 recebe os primeiros casos reais |

## 7. O que precisa vir do owner (conhecimento que só você tem)

| # | Pergunta | Onde entra |
|---|---|---|
| P1 | ~~Período padrão~~ — **respondido** (2026-11-13): sob demanda, em qualquer dia, e o usuário escolhe o período (hoje, ontem, semana, mês ou datas livres). Sem período dito, a CLARA pergunta. | diretiva 1 |
| P2 | Quem corrige cada tipo de erro na Delpi (lançamento fiscal, cadastro de fornecedor, cadastro de TES, compras)? | campo «Quem corrige» das regras |
| P3 | ~~Prazo fixo no mês~~ — **respondido**: não há rotina fixa; a auditoria roda quando o usuário precisar. | AE-00 |
| P4 | Há outras regras da empresa que a skill ainda não tem (casos que a contabilidade aponta e que não são erro, ou o contrário)? | AE-09 |
| P5 | Quais são as TES de frete com e sem crédito usadas hoje (a skill deduz pela SF4, CFOP x352)? Confirmar a TES 036 (crédito com livro Outros). | AE-05 |
| P6 | Exemplos reais recentes (de preferência a lista que a contabilidade mandou de outubro) para semear os casos | AE-15 |
| P7 | Textos oficiais das normas (LC 123, RICMS/SC, COPAT) ou o link interno que a contabilidade usa | AE-11 |
| P8 | Os exemplos do Gustavo: qual coluna ele filtra como «tipo de nota» no Excel (`Tipo da Nota` = F1_TIPO ou `Espec.Docum.` = F1_ESPECIE) e quais valores ficam marcados | filtro de execução (front-end 01, back-end §3.8), diretiva 1 |

## 8. Registro

| Data | Evento |
|---|---|
| 2026-11-13 | Owner: período De/Até livre e tipos de nota, como hoje; a CLARA usa o que o usuário disser e pergunta o período quando faltar (P1 respondida). P8 aberta: tipos de nota. |
| 2026-11-13 | Owner: auditoria sob demanda, qualquer dia (P3 respondida; P1 parcial). Movido para `entry-audit/mcp/`. |
| 2026-11-13 | Organização inicial do conhecimento e das capacidades da CLARA para a auditoria de entradas. |
