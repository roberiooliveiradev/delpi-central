# Documento 109 — GO do PO: última rodada E2E em jornada real do usuário, G2 e G3

**Data da manifestação:** 2026-10-26. **Solicitante:** PO do Portal Controladoria & Finanças. **Execução:** CF-PROC0072-USER-JOURNEY-G2-G3-FINAL-001. **Referências:** [Documento 108 — matriz e evidências G2/G3](./108-homologacao-guiada-g2-g3-2026-10-26.md), [Documento 104 — critérios G2/G3](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), [Documento 107 — deploy e ChatGPT](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), [Ledger 23](./23-ledger-rq-ac-testes.md).

## Decisão expressa

O PO declara: **"vamos solicitar ao Devin uma última rodada; ele deve fazer o fluxo que os usuários fazem, end-to-end. Eu autorizo G2 e G3."**

**Interpretação operacional autorizada:** GO do PO para executar imediatamente, numa única rodada consolidada, a homologação de usuário final e coordenar fechamento G2 e G3, com demonstração e evidência. Não multiplicar prompts nem utilizar somente testes HTTP para afirmar E2E. Permite ao PO registrar a própria decisão de aceite G2 **após** visualizar resultados, escopo e residuais. Não significa que outro owner, revisor designado, IAM ou Operador SSH assinou automaticamente seu gate. A autorização operacional G3 da pessoa efetivamente habilitada e os preflights continuam obrigatórios antes de novas alterações produtivas. Não registrar signoff retroativo fictício do deploy já ocorrido.

## Requisitos não negociáveis da última rodada

1. HEAD, worktrees/status, documentação canônica, .cursor pertinente e padrões do Portal.
2. **Uma única stack local coerente ponta a ponta:** navegador real/Playwright, Keycloak, Core, MFE, BFF, PG de homologação, corpus. O BFF realmente atendido pelo navegador deve ser o mesmo que passa nas verificações HTTP; não aceitar Admin renderizando erro 404 como fluxo funcional.
3. **/ready íntegro:** no último relatório, `status=degraded` por falta de configuração `CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN` foi rotulado incorretamente PASS. Corrigir configuração local sem expor segredo; provar `ready` e authorization fail-closed.
4. **Jornadas completas de usuário:** login; Home/Busca; P6 revisão e publicação em cenário local; P2 abrir competência/snapshot/documentos/validação; P3 cutoff/conciliação; P4 pendências; P5 pacote/áreas/clarificação/decisão e C2; P1 cockpit, relatórios e help; contas ACCESS/MANAGE/reviewer/denied; mobile/teclado/foco e navegação/F5. Testes positivos, negativos e pós-condições UI/BFF/DB; registrar todos com ID do Ledger 23.
5. **CLARA:** discovery OAuth/MCP, corpus/citações, dois/cinco/vinte ops, consentimento único no Portal e READ-back; usar cenário isolado local. ChatGPT real e Keycloak produtivo somente após autorização IAM/G3 e com conexão efetiva documentada, sem segredos.
6. **Tratar residuais existentes:** `P5-02b`, `MCP-21`, `E-05` inconclusivos; contrato de notificações HTTP 400; mensagem 409 com título "Falha de comunicação"; relatório R01–R15 **não** homologado oficialmente sem G5/G6; clarificação aberta bloqueia C2; higiene das evidências JSONL (não publicar handles, challenge IDs ou dados pessoais).
7. **G2:** PO/Controladoria assinam somente após demo dos outcomes reais, com `ACCEPT` ou `ACCEPT_WITH_RESIDUAL` se elegível e sem defeitos críticos. Explicitar qualquer G1 pendente (T03/T05/R04+, seeds, fontes). Caso contrário `REWORK` focalizado ou `INCONCLUSIVE`.
8. **G3:** recuperar evidências contemporâneas de autorização do deploy já reportado sem retrodatação; Operador autorizado faz preflight somente leitura, SHA/image, backup/restore, migrations, rollback, Keycloak `--check` com credencial vigente e diff transversal; só depois de autorização específica pode aplicar mudanças em produção. Não usar senha administrativa fora do cofre.
9. **Publicação:** atualizar Documento 108 com Rodada 4, matriz RQ/AC e status de cada finding; Documento 107 para deployment/Keycloak/ChatGPT; commits/SHAs e links de evidência higienizada. Diferenciar docs, teste local, homologação humana e smoke de produção.
10. **Escopo:** Sala de interação, expansão de Minhas tarefas e DRE permanecem fora do GO. Nenhuma permission além de `controllership-finance.access` e `controllership-finance.manage`.

**Estado na data desta decisão:** autorização do PO expressa; G2 outcome/signoff ainda não demonstrado nesta mensagem; G3 operator signoff e Keycloak produtivo seguem pendentes de evidência. Não mudar status para PASS sem teste real.

**Próximo passo:** uma última execução E2E integrada por Devin, demo/aceite G2 explícito, reunião operacional G3 com owner, configuração autorizada IAM e conexão real CLARA→ChatGPT.
