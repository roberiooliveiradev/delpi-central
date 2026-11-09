# PROC-0072 — Plano de assimilação de evidências pós-demonstração (cinco etapas)

**Status:** PLANNED / DOCUMENTATION_ONLY / NO_RUNTIME / NO_DATA_CHANGE  
**Data do inventário:** 2026-11-09  
**Branch documental:** `docs/proc0072-post-demo-five-stage-inventory-20261109`  
**Base GitHub observada via connector:** `0270440585dbdd9aa7367acfe3f493f1e95271c9` (branch principal, leitura em 2026-11-09).  
**Limitação:** ferramenta GitHub disponibilizada não fornece `git status` da área de trabalho local. O status do checkout local é **INCONCLUSIVE**, não assumido limpo. Nenhum resultado de teste/runtime foi produzido neste pacote.

## 1. Objetivo e limites

Consolidar o levantamento operacional posterior à apresentação da Central de Fechamento em cinco gates sequenciais, para **inventariar, confrontar com contratos canônicos e preparar decisões antes de modificar cadastros, dados, contratos ou runtime**. O plano não autoriza execução de suas etapas. Cada slice exige rebaseline de HEAD, git status local por executor, authorities, producers/consumers, RQ/AC, segurança, aceite e evidência de postcondition.

**Política de publicação (repositório potencialmente público):** não incluir nomes de participantes, ata/transcrição integral, imagens de reunião, documentação financeira anexada, extratos bancários, contas, identificadores corporativos pessoais, valores operacionais privados ou planilhas de negócio. Preservar artefatos originais apenas em ambiente autorizado fora do GitHub; neste repositório registrar somente metadados abstratos, regras, fluxos, contracts e referências à authority. Fontes TOTVS/Protheus somente após inspeção de segurança, licença, autorização de versionamento e diretório canônico, nunca pelo simples fato de terem sido recebidos.

## 2. Authorities e documentos de reuso (não substituir)

- Authority superior: `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`; carregar regras `.cursor` aplicáveis a cada gate.
- Processo AS-IS/proveniência: TÉO/Transformômetro, ata do PROC-0072 da demonstração de novembro de 2026 (**rascunho; assinatura/finalização não comprovadas**); transcrição e anexos são evidência de trabalho **não publicada**.
- TARGET/requisitos/código: `docs/12-roadmap-e-evolucao/controllership-finance/README.md`.
- Base de conhecimento: `118-base-canonica-processo-fechamento-mensal-proc0072.md` (ponto de entrada canônico; não duplicar R01–R15).
- Fluxo documental e público DRE: `113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md`; `09-p2-checklist-e-documentos.md` e documentos P5 relacionados.
- Contrato documental: `114-contrato-proposto-document-config-dr1-dr2-gate013.md`; conferir implementação da operação transacional, vigência, OCC/idempotência e snapshots no HEAD antes de qualquer uso.
- Evidência/ledger: `23-ledger-rq-ac-testes.md`; conciliação e fontes: `83-ciclo2-crosswalk-evidencias-r01-r15.md`, `84-ciclo2-paridade-monetaria-relatorios-oficiais.md`, `15.1-p3-criterios-paridade-monetaria.md`.
- Acervo técnico já citado no projeto: `docs/13-fontes-totvs-protheus/`. Inventariar árvore e regras antes de propor inclusão de qualquer fonte.
- Segurança: somente `controllership-finance.access` e `controllership-finance.manage` como modelo de produto congelado; efetivas via Core + scope/ownership + business rule; não criar permissões por banco, documento, filial, página ou DRE por conveniência.

**Conflito potencial a verificar:** o doc 118 descreve runtime com um código de permissão especializado para DRE, enquanto a governança de produto congela apenas ACCESS/MANAGE. Não suprimir evidência histórica nem alterar código/permission silenciosamente. Conferir manifesto, contratos de segurança, producers/consumers e ADRs no HEAD e elevar `DECISION_REQUIRED` ou `EXECUTION_DRIFT` conforme autoridade e evidência.

## 3. Registro sanitizado de evidências recebidas

| ID | Fonte privada recebida/referida | Informação aproveitável para o inventário | Estado |
|---|---|---|---|
| EV-NEW-01 | Ata do processo no Transformômetro | Segregação por filial, conciliação estoque, relatórios de mão de obra/faturamento, centros de custo, custo zerado, duas unidades fabris, entregáveis DRE e acessos | PROVEN como registro AS-IS, não como paridade de runtime; ata em rascunho |
| EV-NEW-02 | Transcrição bruta de reunião (arquivo de trabalho DOCX) | Trechos a conferir sobre extratos, documentação de envio, relatório interno, rotina do DRE e exceções | OBSERVED/TO_INVENTORY: reconhecimento de texto automático não equivale a aprovação de regra |
| EV-NEW-03 | Imagem da relação de arquivos de extratos | 11 entradas de arquivos em 4 instituições aparentes, com categorias conta corrente, investimento/aplicação/cotas; três arquivos aparentes do mesmo banco **não comprovam** três contas | OBSERVED; cadastro físico/conta/obrigatoriedade não validado |
| EV-NEW-04 | Captura de tela de cadastro de produto ERP | Campos de classificação de despesa e flags de obrigatoriedade de centro de custo; exigem crosswalk de negócio com owner da origem | OBSERVED; não é contrato |
| EV-NEW-05 | Imagens de colaboração de reunião | Existência de compartilhamento de arquivos-fonte de relatórios e lista de extratos; sem evidência de aplicação/versão do runtime | OBSERVED |
| EV-NEW-06 | Arquivos-fonte de relatórios Protheus (.ch/.prx/.tres) | Candidatos ao inventário de parâmetros e filtros de MATR320 e MATR989; nenhum fonte será publicado nesta etapa | TO_INVENTORY; autoria/licença/segredos/versão não revisados |
| EV-NEW-07 | Planilhas, PDFs e vídeo operacionais da competência de referência | Corpus privado de conferência; utilizar apenas para provar cálculos com ambiente e autorizacão adequados; não publicar amostras financeiras | TO_INVENTORY; parte dos anexos pode estar indisponível/expirada |

**Observação:** a lista de nomes dos extratos, bem como nomes de pessoas, contas, valores, imagens, anotações ou transcrição, permanece deliberadamente fora do GitHub. O inventário acima não representa arquivo original anexado ao commit.

## 4. Ordem de execução e gates

### Etapa 1 — Catálogo de extratos bancários (PRIORIDADE 1)

**GOAL:** descobrir a estrutura governada existente de exigências documentais e preparar o diff de cadastro de bancos/tipos de extrato, sem inserir registros até autorização específica.

**Inventário:** ler `113`, `114`, `118`, `23` e HEAD da BFF/admin/CLARA; identificar templates, `document requirement`, vínculo por filial/competência, tipo de instrumento (conta corrente, aplicação, investimento, cotas), nomes de exibição, vigência, histórico e snapshots; comparar com o conjunto privado EV-NEW-03. Não deduzir número de contas por número de arquivos (duplicidades/sufixos de download). Não armazenar número de conta no GitHub.

**Owner:** BFF do Portal para configuração documental autorizada; Core para effective permissions; CLARA somente como interface de operação governada se a capability real comprovar write, read-back, auditoria e fail-closed. Ausência de capability não autoriza usar canal paralelo.

**Aceite para próximo gate:** matriz de `existing / missing / ambiguous / retired`; catálogo, contratos e owner confirmados; diff proposto com vigência; autorização de alteração separada; testes planejados de OCC/idempotência, lifecycle, snapshot imutável, permissões ACCESS sem MANAGE, falha do Core, concorrência e read-back. **Sem escrever dados neste plano.**

**STOP:** mudança de schema, nova entidade de conta financeira, alteração de permission ou semântica de documento, catálogo não encontrado, ou assinatura/publicação com efeito retroativo -> `DECISION_REQUIRED`.

### Etapa 2 — Revisão do conjunto documental e envio contábil

**GOAL:** crosswalk com finalidades `INTERNAL_ANALYSIS` vs `DOCUMENT_TO_DELIVER` (rótulos conceituais, NÃO novos enums autorizados). Distinguir documento exigido, arquivo anexado, validado, liberado, enviado e pacote versionado.

**Inventário:** relação por competência/filial do que é (a) entregue à DRE/contabilidade, (b) apenas utilizado em análise interna e (c) pendente de confirmação; extratos separados por instrumento; títulos pagos por data/natureza, recebidos, contas a pagar/receber, inventário e materiais auxiliares. A demonstração relatou relatório de entradas/saídas e estoque completo como conferência interna, mas verificar variantes de inventário, documentos e exceções nos critérios do owner. Transcrição automática não consolida decisão.

**Aceite:** tabela documento × finalidade × owner × fonte × filial × vigência × audiência × RQ/AC; diff proposto sem apagar histórico; versão/histórico e Help previstos; não enviar relatórios R01–R15 automaticamente ao DRE; não assumir que anexado equivale a validado.

**STOP:** divergência sobre público DRE/Questor, lifecycle de pacote, existência de documentos em competência aberta ou contrato breaking -> `DECISION_REQUIRED`.

### Etapa 3 — Relatórios TOTVS, extração e paridade

**GOAL:** investigar discrepâncias sem mudar fórmula canônica e sem editar fonte proprietário automaticamente.

**Inventário:** MATR320, MATR989, MATR460/P7, DLP204, MOD, CPV e segregação de matriz/filial; identificar versão, parâmetros de ordens de produção, materiais de terceiros, escopo do P7 completo vs recortado, `as_of`/cutoff, origem de duas operações fabris; comparar com docs 83/84/118, acervo TOTVS e produtores reais no HEAD. O grupo de produto citado na conversa não constitui segregação suficiente; confirmar via centros de trabalho/recursos produtivos.

**Regra invariável:** `DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02`; `PARIDADE_OK` somente quando `R$ 0,00`. Falha ou ausência de origem não vira zero. Não inferir a causa da divergência de H02.

**Aceite:** matriz relatório × produtor × contrato × filtros × granularidade × filial × referência temporal × expected/outcome; testes centavo-exato, positive/sibling/negative e crosscheck de fontes. Somente após gate próprio discutir implementação mínima na `api-delpi` e consumidores BFF/MFE.

### Etapa 4 — Classificações/centro de custo, SB1 e autorização

**GOAL:** especificar regras operacionais e exceções sem replicar regras ERP no Portal nem transformar campos de uma captura em authority.

**Inventário:** cadastro SB1 (classificação de despesa e flags de CC), momento da apropriação (compra vs consumo/baixa), despesas produtivas/fixas, operações excepcionais, notas fiscais sem movimento de estoque, CPV/custo zerado justificável, recursos fabris, autorização do público contábil. Separar `suggested finding` de correção ERP e ação humana.

**Aceite:** decisões funcionais com owner, RQ/AC, predicados e exemplos positivos/negativos; security matrix (effective permissions Core + scope/ownership + business rule, fail-closed). Mudança de cadastro ERP, novo público ou regra de classificação -> `DECISION_REQUIRED`, não alteração direta.

### Etapa 5 — Documentação técnica, QA e aceite por slice

**GOAL:** alinhar only-approved changes com as autoridades já existentes, sem duplicar fontes canônicas.

**Inventário:** para cada slice, localizar seção da doc 118, ledger 23, docs P2/P3/P5/P6, contratos e `docs/13-fontes-totvs-protheus/`; registrar decisão, RQ/AC, contrato, producer/consumer, postcondition, testes, residual search, Help e SHA. Não reescrever docs históricas para fazer parecer que runtime já existe. Testes não executados = `TEST_NOT_RUN`; smoke não realizado = `INCONCLUSIVE`.

**Aceite:** revisão GPT `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`, evidências correspondentes ao HEAD correto, gates e autorização explícita antes do próximo slice.

## 5. Handoff operacional para o próximo chat / Cursor

```text
TASK: CF-PROC0072-POST-DEMO-INVENTORY-STAGE-01
GOAL: Inventariar catálogo atual de extratos e exigências documentais e propor diff sem escrita
PRODUCT STEP: Central de Fechamento / Administração de documentos / P2-P5
AUTHORITIES: instruções oficiais; .cursor aplicável; ADRs; docs 113/114/118/23; contracts/código HEAD; TÉO AS-IS
OWNER: controllership-finance-api (configuração); Core (AuthZ); CLARA apenas se contrato real suportar
CURRENT_STATE: nome de 11 arquivos observados em fonte privada; não equivale a 11 registros
EVIDENCE_REQUIRED: BASE HEAD, git status, paths, produtor/consumidor, catálogo atual, RQ/AC, relatório de diff com ambiguidade e idempotência
ALLOWED_SCOPE: READ ONLY; proposta documental sanitizada
FORBIDDEN_SCOPE: criar/publicar/alterar cadastro, mexer em competência, anexar documentos reais, modificar runtime, alterar permissions, versionar arquivos privados ou fontes TOTVS
SECURITY: ACCESS != MANAGE; Core effective permission; fail-closed
TESTS: TEST_NOT_RUN nesta etapa; desenhar positive/sibling/negative
STOP_CONDITION: contrato ausente, alteração de modelo, novo permission, viés de retroatividade, ambiguidade de número de contas -> DECISION_REQUIRED
```

## 6. Ledger de bloqueios e próximos passos

| Tema | Situação | Ação de descoberta |
|---|---|---|
| Listagem de arquivos vs contas bancárias reais | TO_INVENTORY | Confirmar identidade dos instrumentos, sem dados de conta em GitHub |
| Cadastro atual e capability CLARA | TO_INVENTORY | Ler BFF/CLARA e contratos reais, provar read-back antes do uso |
| Documento interno vs entregue à DRE | TO_INVENTORY | Conferir transcrição e baseline docs 113/118; validar com negócio |
| Fontes `.ch/.prx/.tres` | TO_INVENTORY | Verificar sensibilidade, versão, licença, source owner e acervo atual |
| Material em processo por OP | TO_INVENTORY | Verificar filtros, dados e time reference nos produtores |
| Segregação de operações fabris | TO_INVENTORY | Confirmar cadastros de recursos e contrato de origem |
| Permission especializada DRE relatada no doc 118 | POTENTIAL_DRIFT | Confrontar com authority superior, manifesto, Core e runtime |
| Checkout local, CI, smoke, dados alterados | INCONCLUSIVE / TEST_NOT_RUN | Não inferir resultado sem execução |

**NO CHANGE APPLIED** a serviços, dados, cadastros, contratos, permission model, HELP, deploy ou fontes ERP. Este registro é um plano sequencial com trilha de proveniência abstrata, não autorização para executar etapas.
