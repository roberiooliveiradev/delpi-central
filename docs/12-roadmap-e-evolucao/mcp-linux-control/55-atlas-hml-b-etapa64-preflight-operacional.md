# ATLAS | Etapa 64: contrato pré-operacional e handoff HML (source-only)

**17/11/2026 BRT** | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | PR #270 integrada e DELPI Verifier `ACCEPT_WITH_RESIDUAL` (rodada 1, sem OC).

**NÃO INSTALAR / NÃO EXECUTAR NO srv-api.** Esta entrega não contém serviço operacional, criação de usuário, chave privada, script de instalação, cópia para `/etc/systemd` ou permissão para deploy. Status BLOCKED, quatro MCP READ, PREPARE/ACT OFF. Progresso de referência: 58%.

## 1. Responsabilidades e fronteiras

| Processo futuro | Identidade proposta | Acesso permitido | Negado |
| --- | --- | --- | --- |
| Produtor one-shot | root | Docker Engine compartilhado, exclusivamente GET allowlisted do `delpi-hml-public-hub` | Chave privada e operações Docker administrativas |
| Ponte | atlas-hml-bridge | Snapshot HML 0640 via grupo atlas-hml e UDS do signer | docker.sock, Docker TCP, chave privada, UID 0 |
| Signer | atlas-hml-signer | Chave 0600, estado de geração persistente, UDS prebound | Docker, snapshots arbitrários, API de assinatura genérica |
| Presenter | atlas-hml | Envelope HML e chave pública | Chave privada, Docker, ACT/PREPARE |

**Advertência:** root no mesmo host pode subverter o isolamento de dados e chave. A integridade local Ed25519 não equivale a autenticidade independente. Não alegar SEC-01..10 atestados antes de provas reais e governança.

## 2. Bootstrap do contador: gate de desenho, não implementação operacional

O signer da Etapa 63 **recusa** checkout sem checkpoint; `disposable_genesis=True` é exclusivo de fixtures. Antes da primeira emissão em HML, especificar e revisar procedimento separado que inclua:

1. Registro de mudança identificado, assinado/ratificado pelo owner via identidade verificável, HML exato, SHA imutável, janela, responsáveis e autorização restrita a bootstrap; aceite de risco anterior não substitui aprovação desta ação.
2. Evidência ancorada **fora do diretório local do signer** da ausência de estado anterior, não apenas `file not found`; evidência do contador/último envelope e backup custodiado. Se não houver prova confiável de primeiro uso, **STOP: RECOVERY_BLOCKED**, nunca inferir geração 1.
3. Formação e inspeção humana do primeiro registro (alvo, geração, fingerprint `key_id`, container/image, digest e data), formato `HMLContinuityRecord`; a escrita por `HMLContinuityStore` só em mudança futura autorizada, com UID/ACL/FD/fdatasync/fsync e sem atalhos.
4. Guarda de emissão: geração próxima = checkpoint+1; após reserva sem envelope, preservar evidência e reconciliar manualmente. Não reutilizar geração, não limpar diretório, não usar `disposable_genesis` no host.
5. Backup e restauração testados em ambiente isolado; **restore não pode retroceder a geração mais alta já emitida**. Corrupção, ausência, rollback ou discrepância do anchor externo exigem bloqueio e mudança específica. Não automatizar recovery.

A PR **não cria** um inicializador de checkpoint. A primeira operação depende de desenho técnico adicional, verificação independente e autorização explícita; não fazer "bootstrap" manual usando fixture.

## 3. Revisão de unidades systemd antes de torná-las instaláveis

Os oito blueprints em `linux-ops-mcp/review-only/` são sentinelas `.review`, incluem `ExecStart=/usr/bin/false`, condição deliberadamente inexistente e nenhuma instalação. Nunca os renomear ou copiar para `/etc/systemd`.

Para uma **PR futura**, após o parecer operacional: comandos reais fixados a SHA, caminhos mínimos e ownership de binários; usuário/grupo distintos do signer e bridge; `NoNewPrivileges`, capabilities vazias, `RestrictAddressFamilies=AF_UNIX`, limites de FS/FD e `SO_PEERCRED`; socket pai do signer e herança de FD/symlinks; leitura do Docker somente pelo produtor, acesso alternativo `DOCKER_HOST`/TCP/FD negado aos demais; `systemd-analyze security` e revisão das unidades efetivas após instalação autorizada. `ProtectSystem` sozinho não restringe o Engine.

**Escopo do piloto:** `delpi-hml-public-hub` / compose project `delpi-hml` / service `public-hub`; `delpi-public-hub` de produção fora de escopo. Não mudar `docker.service`, `containerd.service`, compose PROD nem aliases.

## 4. Preflight somente leitura, com evidência sanitizada

Capturar com autorização de leitura e operador identificado: commit e hash do artefato planejado; `systemctl show/cat` apenas das unidades ATLAS se presentes; UID/GID/grupos/capabilities/NNP/seccomp/LSM/namespaces; verificação de permissões de diretórios/sockets/ACL; FDs e endpoints Docker alternativos sem expor segredos; baseline dos dois containers HML/PROD e saúde de Docker/containerd. Não colher `/proc/*/environ` indiscriminadamente, tokens, segredo GLPI ou chave PEM.

O novo módulo `atlas_hml_b_stage64_review.py` só analisa índice JSON passado em memória com escopo fixo, SHA e 13 categorias; cada categoria aceita `missing` ou `declared_present_untrusted`. Mesmo 13/13 **NÃO** prova SEC nem autoriza operação. Não abre host, Docker, sockets, arquivos ou DB. Evidência deve ser conferida manualmente contra fontes externas e vinculada à issue #232, com conteúdo sanitizado.

## 5. Janela, STOP e rollback futuro (somente ATLAS)

Antes de execução: registrar horário, responsável, snapshot de estado anterior, nomes exatos das novas unidades ATLAS, hash dos artefatos e evidência de PROD saudável. Medir saúde HML e latência sem tocar outros serviços.

**STOP imediato**: qualquer acesso Docker indevido por bridge/signer/presenter; falha de UID/FD/ACL/LSM/peer; assinatura inválida, replay, corrupção ou lacuna de geração; referência PROD no payload; degradação do Public Hub de produção ou Docker compartilhado; desvio entre SHA auditado e binário no host.

**Rollback proposto (não executar nesta etapa):** desativar exclusivamente timer/socket/services **novos do ATLAS** identificados no plano aprovado, preservar logs/evidências e checkpoint para reconciliação, revogar o acesso HML específico se aplicável e verificar saúde/identidade de PROD e HML. Não executar `docker restart`, `docker compose down`, restart de daemon, apagar volumes, restaurar checkpoint antigo, reativar `disposable_genesis`, ou modificar `delpi-public-hub`. Rollback real somente em mudança isolada autorizada, com lista exata de comandos revisada pelo owner.

## 6. Gates restantes e próximo pacote

- SEC-01 / exceção formal compatível com governança, especialmente risco root + chave no mesmo host.
- Concluir desenho e revisão do bootstrap sem fallback inseguro; chave real/GLPI somente depois de autorização específica de geração.
- PR futura para entrypoints/unidades **realmente operacionais** após revisão externa e ensaio com UID/GID distintos em runner isolado; CI não substitui medição do PID real.
- Inventário de aliases Docker/FDs e isolamento real do `srv-api`, change control, plano de rollback e janela autorizada.
- Primeiro piloto exclusivamente READ em HML após decisão explícita separada. Quatro MCP READ; PREPARE/ACT OFF.

**Pull/deploy:** NÃO. Nenhuma ação no host realizada por esta PR.
