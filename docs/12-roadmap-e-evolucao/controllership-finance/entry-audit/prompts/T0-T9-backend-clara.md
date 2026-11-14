# Prompt para o Cursor — Entry audit, T0 a T9 (back-end + CLARA, HML e PROD)

```text
PROMPT CURSOR — ENTRY AUDIT · Trilha T0 → T9 (back-end, CLARA, HML e PROD), execução contínua

CONTEXTO
Vamos levar a auditoria de entradas (Protheus × XML de NF-e e CT-e), hoje feita pela skill
`auditoria-entradas-nfe-protheus` + planilhas + painel Raio-X, para o Portal Controladoria & Finanças
e para a CLARA. O usuário — ou a CLARA, num comando — escolhe período (De/Até livre) e tipo de
documento (NF-e = espécie SPED, CT-e = espécie CTE); a BFF lê o Protheus pela api-delpi e o XML pelo
Questor via financial-api, roda o motor de regras e guarda o resultado.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/
  track.md       ← TRILHA (ordem, protocolo, paradas, rollback, etapas). Siga-a à risca.
  plan.md        ← objetivo, decisões D1–D14, arquitetura
  backend/       ← rotas, camadas, dados, persistência, evidência da amostra (§3.9)
  mcp/           ← catálogo, fichas AE-00..AE-15, diretivas da CLARA
  reference/     ← cópia da skill (regras e scripts) para o porte e a paridade
  frontend/      ← NÃO executar agora (T10–T13 vêm depois da verificação do owner)
Autoridade: instruções oficiais do arquiteto e .cursor aplicáveis > ADR-003 (você cria na T1) > track.md > demais docs.

MISSÃO
Executar a trilha de T0 até T9, SEM PARAR entre etapas, corrigindo problemas de forma autônoma,
documentando cada etapa no mesmo commit, publicando em HML e testando, e por fim publicando em PROD
com a funcionalidade ligada. Parar SOMENTE:
  - numa regra de parada X1–X8 (track.md Parte 4), ou
  - ao concluir a T9 (PARADA DE VERIFICAÇÃO do owner pela CLARA).

REGRAS INEGOCIÁVEIS
1. main, sem branch, sem stash/reset/clean; commits só com arquivos da etapa; push a cada etapa
   (se o push for recusado por fast-forward: fetch --depth=80 + rebase em origin/main + push).
2. Protocolo P1–P9 em cada etapa (track.md Parte 3). Quadro de status e registro atualizados a cada etapa.
3. Correção autônoma: até 3 ciclos por problema (diagnóstico com evidência → correção mínima → teste).
   No 4º ciclo: BLOCKED X1.
4. Somente leitura no Protheus, no Questor e nos dados do LNF (X4).
5. CLARA: NÃO criar tool nova nem mudar as seis tools semânticas (get_context, read, analyze,
   knowledge, execute, delete). Só catálogo, analysis_type, conhecimento e diretivas (X5).
6. Permissão única: controllership-finance.access (manage herda). Nenhuma permission nova.
7. Repositório público: nenhum dado real (CNPJ completo, nomes de fornecedor, valores, chaves) em
   código, fixture, doc ou commit (X6). Fixtures sintéticas. Evidência real só resumida no report.
8. Testes: suíte de cada serviço tocado comparada ao commit pai; só falhas pré-existentes são aceitas (X2).
9. Funcionalidade nova atrás de ENTRY_AUDIT_ENABLED (padrão false); ligada em HML na T6 e em PROD na T9.
10. Evidência PROVEN | TO_INVENTORY | INCONCLUSIVE com arquivo:linha; PASS | FAIL | TEST_NOT_RUN.
    Smoke não executado = INCONCLUSIVE.

ETAPAS (detalhe completo em track.md Parte 6)
T0  Inventário somente leitura: mapa coluna da skill × campo Protheus × tabela; Questor (filtro por data,
    CT-e, busca pela chave, sessão da filial 02); consulta do LNF por nota; padrões da BFF
    (job no lifespan, migrations V023, catálogo semântico, corpus, branding, testes MCP); volume.
T1  Contrato completo (payloads, erros, paginação, schema V023, chave estável, ids estáveis de regra,
    configuração D12, flag D13), catálogo final da CLARA, ADR-003 ACCEPTED.
T2  api-delpi: /financeiro/entry-audit/{documents,items,fiscal-book,tes,branches} (só leitura).
T3  financial-api: listagem do Questor por emissão/tipo/filial; XML pela chave; download padronizado.
T4  BFF: motor de regras no domain (Python puro) + leitor de XML + TESTE DE PARIDADE POR CONSTRUÇÃO
    com reference/.../scripts/auditoria.py (mesma entrada nas duas vias; melhorias D11 desligadas).
T5  BFF: V023, análise idempotente, worker no lifespan, execução por filial, reexecução com status
    preservado, D11 (XML pela chave, listagem com folga, cruzamento com o LNF, em trânsito),
    rotas /entry-audit/* (inclui options, summary, daily, breakdowns, facets, trend, abas, detalhe,
    resolve/reopen, export xlsx no layout da skill).
T6  HML: publicar api-delpi, financial-api e BFF (projetos-teste/delpi-central, usuário operador;
    backup + --ff-only se houver alterações locais alheias); ENTRY_AUDIT_ENABLED=true; ensaio com
    um dia e um mês reais por filial; paridade com dado real (skill de referência sobre as mesmas
    entradas); D11; reexecução; resolver/reabrir; export; 403 sem access; logs sem token; tempo de execução.
T7  CLARA: entradas no catálogo (read entry_audit.*, analyze entry_audit_findings com compare_to,
    execute direto run/rerun/resolve/reopen), schemas; fichas AE-00..AE-14 em
    fichas/auditoria-entradas/ registradas no corpus_manifest.py (domínio controllership);
    diretivas no branding.py; testes (catálogo/schema, execução direta e idempotência, gate por
    permission, corpus parity, fluxo MCP ponta a ponta run → analysis → analyze → occurrence → resolve).
T8  HML: BFF com T7; testes MCP contra o endpoint MCP de HML se existir (senão in-process PASS e
    registrar a verificação funcional no PROD); ingestão do corpus e knowledge(search) com citação.
T9  PROD: linha de base; tags rollback-entry-audit-<serviço>; publicar api-delpi → financial-api → BFF,
    um por vez (OK do owner dado para esta trilha); ENTRY_AUDIT_ENABLED=true; publicação governada do
    corpus; verificação técnica (health, rotas com credencial, uma análise real concluída, catálogo
    da CLARA com as entradas para quem tem access, LNF e Central de Fechamento sem regressão,
    logs sem token). Falha → rollback do serviço e BLOCKED X7.
    Ao concluir: PARAR e entregar o report com o roteiro da Parte 7 pronto.

NÃO FAZER AGORA
T10–T13 (plugin-ui e MFE). Nenhuma alteração em plugins/plugin-ui nem em plugins/controllership-finance.

REPORT (ao parar)
Formato da track.md Parte 9, um bloco por etapa executada, mais:
- tabela coluna da skill × campo Protheus (T0);
- resultado da paridade (T4 sintética, T6 com dado real) — contagens e diferenças explicadas;
- tempos de execução em HML e PROD;
- quadro de status final;
- pendências do owner (perguntas abertas do mcp §7).
```
