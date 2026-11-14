# G0-SEC-S1 | Admissao de motor remoto em laboratorio (intake OFFLINE)

**Data:** 2026-11-13
**Estado:** **EM REVISAO / BLOQUEADO**. Nao e implantacao de MeshCentral, nao e habilitacao de agente e nao aprova G3-ENGINE.
**Projeto:** Delpi Remote, issue #179.

## O que este incremento faz

O G0-SEC-S0 ja verifica no CI que o Portal nao recebeu rota, permissao ou servico remoto prematuro. O G0-SEC-S1 complementa o processo com **registro estrito da release candidata e dos riscos conhecidos**, sem criar runtime remoto.

- `G3-LAB-CANDIDATE.json`: registro publico minimizado de release, commit upstream completo, digest de artefato **ainda ausente**, controles de ambiente isolado e riscos abertos.
- `it-portal-api/it_portal_app/domain/remote_engine_lab_intake.py`: avalia o registro sem rede. Versao 1.3.1 fixa ao commit `f436143527458d56da0336ea3047c006703fb4e4`, confirmado via tag oficial em 13/11/2026. Trocar release exige revisao do codigo e dos testes, sem baixar automaticamente nada.
- `it-portal-api/tests/test_remote_engine_lab_intake.py`: testes negativos de URLs falsas, tag/commit divergente, SHA-256 invalido, tentativa de marcar `approved`, flags de exposicao publica, credenciais ou agentes de producao, dados sigilosos e registros incompletos.
- CI API: executa esta validacao antes dos testes `pytest`. Esperado: `G3-LAB BLOCKED` + exit 0, pois o estado seguro e **impedir instalacao**. Qualquer violacao estrutural retorna `INVALID` e CI falha.

Nenhum operador, IP, usuario, credencial, token, host real ou topologia interna pode entrar no repositorio publico.

## Fontes consultadas em 13/11/2026

1. <https://github.com/Ylianst/MeshCentral/releases/tag/1.3.1> publica a versao 1.3.1 em 23/10/2026 e alerta urgencia por exploit ativo; os mantenedores dizem que a correcao **esperam** que resolva a exploracao. Isto **nao e comprovacao de mitigacao**.
2. <https://github.com/Ylianst/MeshCentral/tree/f436143527458d56da0336ea3047c006703fb4e4> e o commit indicado pela tag oficial.
3. <https://github.com/Ylianst/MeshCentral/issues/8269>: problema aberto em 13/11/2026, reporta que agentes Windows 1.3.1 podem ficar conectados mas sem o core de escritorio/terminal/arquivos. Relato de usuario, exige reproducao em lab, nao conclusao sobre toda instalacao.
4. <https://github.com/Ylianst/MeshCentral/security/advisories>: advisories oficiais; consulta publica nao substitui investigacao de incidente nem revisao de supply chain.
5. <https://docs.meshcentral.com/meshcentral/security/>: documentacao de seguranca e configuracoes a avaliar.

**Decisao de engenharia:** release 1.3.1 e apenas **candidata sob risco**. Nao promover a artefato confiavel nem recomendar copiar `meshcore.js` de versoes anteriores como solucao, pois mistura releases sem validacao. Sem mitigacao verificavel, escolher outra release/solucao apos novo ADR.

## Os bloqueios antes de QUALQUER laboratorio

| Item | Exigencia | Evidencia ainda ausente |
|---|---|---|
| Vulnerabilidade/emergencia | Confirmar exploit, causa, patches e ausencia de comprometimento em fontes oficiais | parecer tecnico de Seguranca/TI |
| Windows agents | Testar desktop, agente, arquivos e UAC usando build unica e verificavel | resultado de Windows piloto |
| Supply chain | Selecionar artefato exato com SHA-256 e procedencia, licencas/SBOM e auditoria de dependencias | artefato pinado assinado/validado |
| Identidade | Conta humana Keycloak/MFA recente, broker isolado, revogacao e kill switch | testes negativos e trilha de auditoria |
| Rede e recuperacao | VM/projeto temporario sem roteamento a producao, inbound publico negado, sem credenciais/produtivos | diagrama privado, teste de isolamento e restore |

Essas evidencias devem ser aprovadas em sistema **privado** de change/seguranca. A estrutura publica `G3-LAB-CANDIDATE.json` nao aceita campo `approved` nem transforma CI verde em autorizacao.

## Verificacao local, sem instalar nada

```bash
cd /home/operador/projetos/delpi-central/it-portal-api
python3 -m it_portal_app.domain.remote_engine_lab_intake --repo-root ..
python3 -m pytest -q tests/test_remote_engine_lab_intake.py
```

Saida esperada do CLI: `G3-LAB BLOCKED`, informando pendencias, e exit 0 para que a validacao da ausencia de autorizacao fique verde. Se `INVALID`, nao corrigir alterando controles para `true`: revisar esquema e risco.

**Nao executar npm install, docker run, instalar MeshCentral, adicionar Docker Compose/portas, baixar agents ou testar acesso grafico neste incremento.**

## Proximo incremento proposto

**G0-SEC-S2:** preparar minutas de politica para TI/RH/LGPD, plano de rede privada e roteiro de backup/restauracao e revogacao, com aprovacao humana pendente. Quando houver liberacao **formal e ambiente isolado**, planejar teste G3 em laboratorio sem acesso a maquinas reais; teste G2-S1..S3 no Windows continua presencial.

**Rollback:** esta entrega so cria arquivos Python, testes, CI e documentos; nenhuma migration, deploy da API, manifesto, container, credencial ou maquina alterada. Corrigir em novo commit auditavel, sem remover preflight de seguranca existente.

## Evidencia de CI (13/11/2026)

- [API: test-it-portal-api SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542553147/job/132286203346), commit `b74c12e94bc4`. Passou gate esperado `G3-LAB BLOCKED`, preflight G0-SEC-S0, pytest, integracao PostgreSQL V001..V011.
- [Architecture gate SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542552950/job/132286202669) e [Auditoria SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542552981/job/132286202676).
- Testes automatizados nao autorizam release, rede, agente, controle remoto ou qualquer acesso em producao.
