# ADR-002 | Avaliacao preliminar do MeshCentral como motor isolado

**Data da consulta:** 2026-11-13
**Decisao:** **PENDENTE**. Nenhum motor remoto escolhido como aprovado, instalado, publicado ou conectado ao Portal do TI.

## Situacao e fontes

O roadmap ADR-001 sugere MeshCentral self-hosted, sem assumir que autenticação OIDC, embed ou revogacao atendam automaticamente aos requisitos da DELPI.

| Verificacao | Evidencia em fonte oficial | Impacto |
|---|---|---|
| Licenciamento | Documentacao e repositorio MeshCentral apresentam Apache-2.0 | Viavel para avaliacao, mas validar licencas de dependencias/artefato escolhido |
| Release candidato | Release oficial 1.3.1 publicada 23/10/2026, commit indicado `f436143` | **Candidato sob revisao**, nao versao aprovada nem hash imutavel fixado |
| Alerta de seguranca | Mantenedores publicaram aviso de exploracao ativa e atualizacao emergencial 1.3.1 | **BLOQUEIO** de qualquer exposicao/instalacao antes de triagem e mitigacao documentadas |
| Capacidades | Documentacao cobre desktop remoto, usuarios/grupos, proxy, TLS, MFA, SSO, embedding | Funcionalidade descrita NAO equivale a atendimento dos controles de identidade e privacidade da DELPI |
| Historico de advisories | GitHub Security Advisories do mantenedor | Consultar novamente imediatamente antes de testar/implantar |
| Supply chain | Repositorio possui releases e artefatos Windows/Node | Exigir digest SHA-256, lock de dependencias, SBOM e assinatura antes de pilotar |

Referencias oficiais:
- https://github.com/Ylianst/MeshCentral/releases/tag/1.3.1
- https://github.com/Ylianst/MeshCentral/security/advisories
- https://github.com/Ylianst/MeshCentral/security
- https://github.com/Ylianst/MeshCentral
- https://docs.meshcentral.com/meshcentral/
- https://docs.meshcentral.com/meshcentral/security/

## Riscos que devem ter prova pratica, nao suposicao

- **Servidor comprometido:** uma instancia de suporte remoto e um ponto de controle de todas as estacoes nela inscritas. Pior impacto do que um monitor de inventario. Nao compartilhar credencial, token, segredo ou permissao com G2-S2.
- **SSO/OIDC:** identificar se login MeshCentral pode ser federado com Keycloak sem criar sessao paralela e sem usar credencial de admin de longa duracao no navegador. Revalidar MFA recente antes da conexao.
- **Embed:** negar uso direto de iframes/tokens privilegiados enquanto nao for provado CSP/frame-ancestors/CSRF/cookies/Origin/WebSocket e revogacao. Plano alternativo: broker backend isolado.
- **Segregacao:** sem publicar WebSocket/admin APIs na internet; rede privada/VPN e autenticação forte no acesso.
- **Permissoes do dispositivo:** permitir somente computadores corporativos explicitamente inscritos, nunca usar IP/hostname/serial do G2 como comprovacao de controle remoto.
- **Revogacao:** cortar novas sessoes e encerrar ativas em prazo mensurado (Kill Switch global e por maquina). Desconexao da rede, falha de SSO ou troca de permissoes devem falhar fechado.
- **DLP:** telas, clipboard e arquivos em etapas separadas, desativadas por padrao. Auditar metadata de sessao, nao conteudo da tela/arquivos.
- **Operacao:** provar backup/restauracao do banco/config/certificados em maquina de laboratorio com versao fixa, cronograma de patches e rollback.

## Proposta de gate de decisao

1. Infra/Sec verifica a release **na data do piloto**, detalhes do aviso emergencial de outubro, changelog completo e eventuais advisories posteriores; selecionar versao imutavel, digest e politica de atualizacao. Se nao houver evidencia confiavel de mitigacao do ataque, **NO-GO**.
2. Responsavel de TI aprova arquitetura de rede e workstation laboratorio dedicada, sem producao TOTVS.
3. Provar isolamento e falha fechada em laboratorio sem habilitar nem cadastrar permissoes remotas no Portal produtivo.
4. Revisar politica do RH/Juridico para acesso nao assistido, ciencia dos colaboradores e retencao de auditoria.
5. Se a avaliacao falhar, registrar ADR de alternativa ao MeshCentral antes de qualquer broker ou agente remoto.
6. Com evidencia e aceite **privado** de seguranca, registrar apenas referencia sanitizada no GitHub e atualizar G0-SEC; somente entao o desenvolvimento G3-ENGINE e G4-AUTH podera prosseguir em um laboratorio segregado.

**Resultado em 13/11/2026:** nao ha provas de ambiente isolado, assinatura, revogacao, SSO/broker seguro ou mitigacao demonstrada da exploracao emergencial de 1.3.1. **G3-ENGINE BLOQUEADO.** Nenhuma infraestrutura foi instalada por esta analise.

## Atualizacao G0-SEC-S1 (13/11/2026)

- **Release upstream verificada:** `1.3.1` publicada em 23/10/2026; tag `refs/tags/1.3.1` aponta para commit completo `f436143527458d56da0336ea3047c006703fb4e4`. Ver [release oficial](https://github.com/Ylianst/MeshCentral/releases/tag/1.3.1) e [commit](https://github.com/Ylianst/MeshCentral/commit/f436143527458d56da0336ea3047c006703fb4e4). **Isto fixa codigo-fonte, NAO digest de artefato, imagem Docker ou versao de agente.**
- **Regressao reportada:** [issue #8269](https://github.com/Ylianst/MeshCentral/issues/8269) permaneceu **aberta** na consulta (13/11), descrevendo agente Windows conectado sem core grafico/arquivos/terminal apos 1.3.1. Exige reprodutibilidade independente em lab; nao voltar para versao anterior nem misturar binarios como contorno sem analise.
- **Exploit/emergencia:** avisos na release sao graves e usam linguagem cautelosa quanto a correcao. Nao ha atestado de mitigacao, pentest, assinatura, rollback ou verificacao de clean install neste projeto.
- **Candidato:** [G3-LAB-CANDIDATE.json](G3-LAB-CANDIDATE.json) registra fonte/commit/riscos, `artifact_sha256=null` e flags negativas. O verificador `remote_engine_lab_intake.py` impede declarar `approved` no codigo publico, recusa mismatch de commit e falha se configurar exposicao externa/credenciais/dispositivos de producao.
- **Decisao inalterada:** G3-ENGINE BLOQUEADO ate aprovacao formal de G0-SEC em canal privado e laboratorio isolado demonstrado. Ver [G0-SEC-S1](G0-SEC-S1-ENGINE-INTAKE.md).
