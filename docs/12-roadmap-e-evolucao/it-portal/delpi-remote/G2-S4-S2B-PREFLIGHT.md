# G2-S4-S2b-P0 | Preflight offline para bootstrap seguro

**Data:** 2026-11-14. **Estado:** EM REVISAO, sem homologacao e sem habilitacao operacional.
**Escopo:** primeira entrega preparatoria do G2-S4-S2b, exclusivamente verificacao offline, regressao de seguranca e desenho do protocolo. Nao existe ainda endpoint de bootstrap, segredo emitido, aprovacao automatica, deploy ou agente ativado.

## O que foi implementado

- Novo validador Python em it_portal_app/domain/workstation_bootstrap_readiness.py. Ele verifica exclusivamente arquivos versionados: Compose com flags de ingestao/provisionamento/binding/revogacao false por padrao; cliente Keycloak disabled, sem grants e com leitura de verificacao; V013 sem grant automatico; status sem anuncio de credenciais emitidas ou controle remoto; ordem de revogacao DB antes de Keycloak; instalador Windows em modo PLAN por padrao e tarefa disabled; ausencia de rotas de ativacao/bootstrap.
- Testes negativos isolados em tests/test_workstation_bootstrap_readiness.py para mudancas perigosas, incluindo rotas e migration.
- Etapa dedicada de CI com resultado esperado G2-S4-S2b BLOCKED. BLOCKED e o estado correto mesmo com CI verde. INVALID implica regressao e falha o pipeline.
- Nenhuma modificacao operacional em Windows, Keycloak, Postgres, RBAC, manifesto do MFE ou motor remoto.

## Protocolo necessario na proxima implementacao

1. Em HML privado, a TI seleciona um computador de laboratorio ja cadastrado e usa autenticao humana + MFA recente + RBAC fresh; registrar aceite e motivo. Nao confiar em IP, MAC ou hostname como prova do dispositivo.
2. Um agente Windows corporativo assinado e verificado, instalado por operador autorizado no equipamento, estabelece canal TLS autenticado ao backend. Exigir prova de dispositivo avaliada por seguranca (preferir TPM/mTLS e vinculacao demonstravel), nao uma declaracao arbitraria do host.
3. Um desafio aleatorio de alta entropia, com validade curta, uso unico e escopo de equipamento, deve ter apenas hash/estado guardados no backend; o segredo nao pode aparecer em browser, URL, logs, ticket ou repositorio. Consumo deve ser atomico no PostgreSQL com controle de expiracao, concorrencia e replay.
4. Somente depois de verificar o dispositivo e o desafio, o backend habilita a identidade individual Keycloak com escopo estrito de inventario e leitura de confirmacao. Credencial chega apenas ao canal do agente protegido; armazenamento local protegido (DPAPI/TPM), com estrategia de rotacao e revogacao.
5. O grant ingest_authorized permanece FALSE em qualquer falha. Habilitacao exige verificacao Keycloak, reconciliacao do DB, auditoria e permissao da TI; falhas parciais nao autorizam retry silencioso. Revogacao precisa ser exercitada com token antigo e nova solicitacao.
6. O caminho de inventario nao autoriza desktop remoto, terminal, clipboard nem transferencia de arquivos. G0-SEC continua gate independente para o motor remoto.

## Como validar esta entrega

- API unitario: python -m pytest -q tests/test_workstation_bootstrap_readiness.py
- Gate offline: python -m it_portal_app.domain.workstation_bootstrap_readiness --repo-root ..
- Pipeline: Portal de TI - API, incluindo regressao geral, testes HTTP/Postgres e architecture gate.
- O resultado esperado do validador e G2-S4-S2b BLOCKED com exit code 0; nao ha segredo, agendamento ou efeito colateral.

## Limites, risco e retorno

Este preflight e estatico e nao prova seguranca criptografica, ligacao fisica, permissao real no Keycloak, rede, backup, Windows 11 ou legitimidade de um dispositivo. Nao autoriza producao e nao substitui avaliacao de seguranca. Sem estado operacional, rollback e a reversao do commit caso o gate cause regressao; preservar V009..V013 e todas as identidades existentes. Para avancar: aprovar protocolo de attestation e HML, implementar circuito completo e testes transacionais sem entregar segredo ao frontend.

Referencias: [Roadmap](README.md), [S2a](G2-S4-S2A-DYNAMIC-BINDINGS-REVOCATION.md), [Seguranca](SECURITY-GATES.md), [Diario](EXECUTION-LOG.md), [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179).
