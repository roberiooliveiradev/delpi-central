# Delpi Remote | Gates de seguranca e protocolo de homologacao

**Estado:** controles especificados; **NENHUM gate de infraestrutura ou acesso remoto aprovado nesta etapa**.

## Incremento G0-SEC-S0 (13/11/2026)

**Aprovacao formal:** ainda AUSENTE. O CI utiliza [preflight G0-SEC](G0-SEC-S0-AUTOMATED-PREFLIGHT.md) + [12 checkpoints](G0-SEC-CHECKPOINTS.json) para flagrar superficies de controle remoto introduzidas sem revisao. Resultado `BLOCKED` e **o estado seguro esperado**, nao uma autorizacao.

**Risco externo atualizado:** [release MeshCentral 1.3.1 (23/10/2026)](https://github.com/Ylianst/MeshCentral/releases/tag/1.3.1) inclui aviso emergencial de exploracao ativa e controle indevido de servidores e clientes. Nao presumir mitigacao comprovada. A decisao, versao, artefato fixado, SSO e isolamento dependem de [ADR-002](G3-ADR-002-MESHCENTRAL-SECURITY.md) e aceite de Seguranca/TI. **G3-ENGINE BLOQUEADO**, sem deploy nem endpoints remotos.

O checklist tecnicamente documentado no repositorio publico nao pode autorizar sessoes de controle. Evidencias nominais, topologia, credenciais, logs e aprovacao devem ficar em sistema privado acessivel aos responsaveis.

## G0-SEC-S1 (13/11/2026) | Admitir somente risco documentado

O [intake offline da release](G0-SEC-S1-ENGINE-INTAKE.md) agora valida release MeshCentral 1.3.1 fixada ao commit upstream, riscos registrados, formato de evidencias e proibe `approved` no repositorio publico. A [regressao Windows #8269](https://github.com/Ylianst/MeshCentral/issues/8269) estava **aberta** no momento da consulta em 13/11. O SHA-256 do artefato **nao foi obtido/verificado**. A emergencia de seguranca continua sem mitigacao comprovada.

CI verde com `G3-LAB BLOCKED` significa somente que o projeto nao tentou liberar MeshCentral por declaracao documental. O aceite de TI/Seguranca e o teste em laboratorio separado permanecem obrigatorios. Nao habilitar rede, escopo remoto, broker, agentes ou motor por este incremento.

## G0-SEC-S2 (13/11/2026) | Governanca e recuperacao em minuta

As propostas de [uso e privacidade](G0-SEC-S2-POLICY-PRIVACY.md), [rede isolada](G0-SEC-S2-NETWORK-ISOLATION.md) e [incidente/recuperacao/revogacao](G0-SEC-S2-RECOVERY-AND-REVOCATION.md) foram preparadas para **revisao privada**, nao como politica aprovada. O [registro publico](G0-SEC-S2-REVIEW-REGISTER.json) tem 10 checkpoints ainda pendentes, sem nomes, topologia, evidencias privadas, token, retencao, RPO ou RTO inventados. Ver [runbook](G0-SEC-S2-REVIEW-RUNBOOK.md).

O validador `remote_policy_review.py` deve retornar `G0-SEC-S2 BLOCKED`; CI verde significa apenas que o pacote e uma MINUTA completa com proibições ativas de autorizacao. O aceite formal e os testes de rede, Keycloak, restore e kill switch ainda nao foram feitos. Acesso remoto e G3-ENGINE continuam **BLOQUEADOS**.

## Modelo de ameacas inicial

| Ameaça | Controle obrigatorio | Teste/evidencia |
|---|---|---|
| Conta do operador comprometida | Keycloak + MFA recente + autorizacao por dispositivo, sessao curta, limite de sessoes | Login sem MFA/usuario sem role recebe negacao |
| Senha mestre vazada | **Proibida senha mestre universal**; acesso privilegiado exige identidade individual | Revisao de codigo/config e tentativa de acesso sem sessao |
| Agente clonado em outra maquina | Identidade propria atrelada ao enrolment do dispositivo; revogacao | Copia de token/cert para outro host falha |
| Controle pela permissão generica de servidor | Escopos separados de `servers.manage` e `host-services.control` | Usuario com permissao de servidores mas sem remote recebe 403 |
| Sessao nao encerrada apos revogacao | Revalidacao e revogacao no broker, TTL, kill switch, heartbeat | Revogar no Core durante sessao e verificar encerramento |
| Cliente adulterado | Instalador assinado ou checksum de release verificado; atualizacoes governadas | Substituir artefato: instalacao barrada |
| Dispositivo acessado sem politica | Allowlist do dispositivo, modo nao assistido autorizado e indicador visivel de sessao | Equipamento nao inscrito e modo proibido falham |
| Clipboard ou arquivos exfiltrados | Scopes separados, deny-by-default, limite de tamanho e tipo, auditoria; sem copiar segredos para logs | Tentar copiar/transferir com flag desligada |
| Token reutilizado ou redirecionado | One-time, curta duracao, vinculado a usuario+dispositivo+origem, nao em URL persistente | Replay e uso em outro destino falham |
| Exposicao do motor remoto a Internet | Rede privada/VPN, firewall deny-by-default, proxy/TLS revisados | Varredura de exposicao realizada pela Infra |
| Acesso por operador revogado / SSO indisponivel | Falha fechada; sem credencial persistente no browser | Keycloak ou Core indisponivel -> negacao |
| Fraude em trilha de auditoria | Eventos append-only, hora confiavel, retencao e acesso restrito | Comparar session ID, usuario, recurso, inicio/fim |
| Queda de servico / agente offline | Timeouts e estados precisos; nenhuma confirmacao ficticia | Simular desconexao no piloto |
| Software vulneravel ou comprometido | Versao fixa, SBOM, CVE review, backup/restauracao e plano de patch | Evidencia de versao e rollback |
| Vazamento do inventario | ACL de leitura por perfil, minimizacao e sanitizacao | Usuario sem `computers.view` recebe 403 |

## Permissoes planejadas (separadas; ainda NAO cadastradas)
- `it-portal.computers.view`
- `it-portal.computers.manage`
- `it-portal.remote.connect`
- `it-portal.remote.unattended`
- `it-portal.remote.clipboard`
- `it-portal.remote.files`
- Escopo tecnico S2S de inventario, **separado** da identidade humana.
- Identidade tecnica do motor remoto, **separada** do agente de inventario.

## Politica de usuario/privacidade a confirmar
- Equipamentos de propriedade e gestao DELPI, com uso profissional autorizado.
- Politica de TI/RH avisando que suporte remoto pode ocorrer em maquina gerenciada.
- Indicador visivel de sessao e encerramento imediato pelo operador; modalidades excepcionais com aceite formal e controle.
- Registro de metadados: usuario, estacao, unidade, finalidade/chamado, IP de origem, tipo de sessao, timestamps e resultado. Nao coletar clipboard, documentos ou conteudos da tela por padrao.
- Definir com juridico/RH periodo de retencao e quem pode consultar historico.

## Condicoes de PARADA
- Administrador precisa de senha mestre, bypass de MFA ou executavel nao verificavel.
- O modo nao assistido permite maquina nao inventariada/nao autorizada.
- Revogacao ou kill switch nao conseguem impedir novas sessoes.
- Plugin passa token privilegiado MeshCentral para qualquer navegador sem escopo limitado.
- Necessidade de expor API/motor publicamente sem revisao de rede.
- Impossivel produzir log confiavel de sessao.
- Falta de inventario do agente e desinstalacao/rollback testados.

## Checklist de aprovacao do piloto remoto
- [ ] Responsavel de seguranca/TI revisou arquitetura e ameacas
- [ ] Compatibilidade/licenca e versao do motor verificadas com fontes oficiais
- [ ] Windows piloto definido sem dados/sistemas criticos
- [ ] Politica de acesso/consentimento e avisos ao usuario aprovada
- [ ] Operador e dispositivo autorizados nominalmente **em configuracao privada**
- [ ] MFA e RBAC fresh testados
- [ ] VPN/rede/TLS e cofre de segredos revisados
- [ ] Backup/restauracao e rollback verificados
- [ ] Logs e retencao acordados
- [ ] Kill switch global e por maquina demonstrados
- [ ] Testes de nao assistido, UAC, clipboard, arquivos, simultaneidade, falhas e revogacao feitos
- [ ] Homologacao do responsavel registrada no diario com evidencias

**Nao confundir** essa lista com autorizacao: cada quadrado permanece vazio ate existir evidencia real.
