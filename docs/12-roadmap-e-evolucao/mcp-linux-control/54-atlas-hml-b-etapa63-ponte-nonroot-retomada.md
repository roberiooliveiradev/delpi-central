# ATLAS | Etapa 63: ponte não-root, continuidade do assinador e pré-piloto HML

**17/11/2026 BRT · Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) · arquitetura B · SOURCE-ONLY**

**Progresso de referência:** 58%. **Sem pull, deploy, chaves reais, systemd instalável, conta ou ACL alterada no `srv-api`.**

## 1. Problema encerrado no código candidato

A Etapa 62 havia deixado duas incompatibilidades para uma futura ativação:

1. Produtor que consulta Docker é root; assinador aceita exclusivamente UID de cliente positivo e não-root, verificado por `SO_PEERCRED`. Abrir exceção para root tornaria a fronteira de acesso ainda menos defensável.
2. O assinador mantinha o último número assinado só em memória, obrigando geração 1 após toda reinicialização, mesmo quando já existia um contador persistente.

A Etapa 63 **não concede permissão operacional**. Acrescenta um caminho de integração com testes reais de processos em runners descartáveis.

### Fluxo proposto

```text
[root one-shot produtor Docker, sem chave privada]
          |
          | snapshot HML mínimo publicado atomicamente (root:atlas-hml 0640)
          v
[ponte atlas-hml-bridge, UID não-root, sem Docker, sem chave privada]
          | FD-checked read, tempo/alvo/JSON estritos
          | canonical signing intent
          v
[UDS local root:atlas-hml-bridge 0660]
          | SO_PEERCRED verificado em ambas as pontas
          v
[signer atlas-hml-signer, sem Docker, chave Ed25519 0600]
          | Ed25519 + reserva de geração via estado FD-safe/fsync
          | apenas assinatura retornada; PREPARE e ACT OFF
          v
[ponte verifica assinatura com chave pública -> envelope]
          |
          v
[publicação e leitura de envelope + presenter READ, ainda candidatos]
```

**Fronteiras reconhecidas:** o produtor root do mesmo host tem poder equivalente a host e poderia modificar observações/credenciais; a assinatura é integridade local, **não** autenticidade independente. A estrutura Unix e ACL real ainda será atestada após ativação expressamente autorizada. Não existe um serviço operacional implementado nesta PR.

## 2. Componentes e defesa em profundidade

- `atlas_hml_b_nonroot_sign_bridge.py`: recusa UID root, real/efetivo/salvo divergentes; reabre apenas o nome fixo do snapshot HML por FD seguro com DAC/ACL, mtime/inode/TTL; recompõe mensagem canônica; faz pedido UDS limitado; compara UID real do servidor via `SO_PEERCRED`, propriedade/mode/inode do socket; valida JSON estrito e confirma Ed25519 com chave pública. Um teste explicita a exceção descartável de mesmo UID usada somente no runner; para futuro host, signer e bridge precisam UIDs distintos.
- `atlas_hml_b_local_signer.py` reutiliza `HMLContinuityStore` em diretório **próprio do signer**, estrito 0750/0640, para reservar uma emissão por geração com `flock`, FD, rename e fsync **antes de devolver** a assinatura. Reinicialização carrega a última geração persistida e exige a seguinte, sem reiniciar em 1. Duas instâncias concorrentes que assinem geração idêntica só podem devolver uma assinatura bem-sucedida. Falhas de checkpoint acionam latch fail-closed.
- Sem checkpoint em processo novo: **rejeição obrigatória** (`HML_LOCAL_SIGNER_BOOTSTRAP_REVIEW_REQUIRED`). O parâmetro `disposable_genesis=True` destina-se exclusivamente a fixtures. Não é caminho de bootstrap de produção; criar primeiro checkpoint confiável exige procedimento futuro, evidência e autorização isolada. Perda/corrupção/rollback do estado bloqueia; um root malicioso ainda pode adulterar ou restaurar arquivos e precisa ser coberto pelo aceite do owner.
- Se um processo falha após reservar geração mas antes do handoff de envelope, a emissão fica **consumida**. NÃO reutilizar, zerar o contador, inventar geração ou automatizar recuperação. Preservar logs sem segredos e decidir recuperação em change-control.
- A assinatura local não confere autorização de PREPARE/ACT. Todas as revisões retornam `blocked` e não implementam MCP de escrita.

## 3. Blueprints revisão-only e isolamento de identidade

Uma nova `atlas-hml-nonroot-bridge.service.review` propõe `User=atlas-hml-bridge`, `Group=atlas-hml-bridge`, `SupplementaryGroups=atlas-hml` apenas para leitura do arquivo HML. Nenhum grupo Docker. `ExecStart=/usr/bin/false`, condição impossível, `RefuseManualStart=yes`, nenhuma seção `[Install]`.

A proposta de socket do signer usa `SocketUser=root`, `SocketGroup=atlas-hml-bridge`, `SocketMode=0660`. O grupo bridge tem direito de conectar ao UDS, **não** à chave privada; futura diretoria de chave sob `atlas-hml-signer:atlas-hml-signer` 0700, arquivo 0600. Diretório pai do socket, ACL, travessia e herança de FD deverão ser revistos pelo responsável. O signer utiliza o listener pré-vinculado, não precisa ter leitura no diretório pai do socket.

A revisão lexical bloqueia alterações para Docker group, root no bridge, endpoints arbitrários, seções `[Install]` e caminhos operacionais. **Não renomear, copiar para /etc/systemd ou habilitar** as unidades `.review`.

## 4. Custódia da chave para a futura operação

- **Identificador no GLPI:** `ATLAS-HML-ED25519-PRIVATE-V1`. GLPI guarda cópia PKCS#8 **criptografada antes do upload**; senha de recuperação em local diferente, acesso nominal mínimo, auditoria e MFA. Confirmar controles reais do cofre antes de confiar no armazenamento.
- Chave operacional Ed25519 raw 32 bytes somente no diretório da identidade `atlas-hml-signer` (0700, 0600) e protegida do bridge, presenter e produtor. Root do mesmo host ainda a acessa; risco aceito, não mitigado.
- Exportar somente pública e `key_id` ao keyring do presenter. Prever rotação/revogação, recuperação testada e novo identificador na próxima versão. **Não gerar chave operacional até existir aprovação de mudança específica.**
- Nunca enviar chave privada, frase, PEM ou token a GitHub, Cursor, chat, tickets, logs, argumentos de processo ou CI.

## 5. Baseline read-only do Linux, sem executar nesta etapa

Antes da ativação, capturar o estado do `srv-api` com responsável, data, SHA e evidências sanitizadas: hash e origem de código/binário planejado; `docker.service` e `containerd.service`; processos e FDs do signer/bridge/presenter **se já existirem**; `systemd` unit efetiva, UID/GID/capabilities/NoNewPrivileges/seccomp/LSM; caminhos alternativos e transporte TCP/TLS do Docker; socket/diretórios com ownership, ACLs e `SO_PEERCRED`; estado `delpi-public-hub` PROD e `delpi-hml-public-hub` HML. Nada de `docker inspect` bruto, `/proc/*/environ` indiscriminado, segredos ou permissões de escrita.

A ferramenta MCP ATLAS atual informa somente saúde sanitizada e pode retornar `observation_status=partial`, sem inventário Docker. Isto não prova UID/FD reais das futuras unidades nem valida SEC-02 a SEC-05.

## 6. Condições necessárias para pedir autorização do piloto

1. O owner ratifica por identidade verificável o risco root+Docker e chave local; documenta exceção à independência **somente se compatível com a política de governança**. Aceite não vira parecer independente.
2. CI da PR etapa 63 verde, DELPI Verifier ao fim, correções obrigatórias encerradas, diff reproduzível na `main`; proibir usar esta PR como autorização.
3. Criar e revisar **em PR posterior**, se autorizado, unidades instaláveis com comando/identidade reais, entradas fixas, isolamento dos três processos, diretórios, permissões e autenticação do UDS.
4. Planejar bootstrap confiável do primeiro contador com evidência assinada/ratificada e recuperação pós-crash; sem fallback para geração 1 após perda.
5. Validar produção intacta, janela, responsáveis, critérios de STOP, plano detalhado de rollback que desliga apenas ATLAS. Nunca reiniciar o Docker compartilhado nem tocar `delpi-public-hub`.
6. Autorizar explicitamente **separadamente** geração da chave real, atualização GLPI, criação de contas/dirs/unidades e primeiros testes de HML. Cada ação deve ter inventário exato, rollback e limites.
7. Após ensaio autorizado, coletar prova real SEC-03/04/05 (UID/FD/ACL/LSM/aliases/socket) e SEC-06/07/08/09/10, com emissão negativa de PROD, replay, contrabando Docker e falhas. Se uma evidência faltar, **status BLOCKED**.

## 7. Aceite da Etapa 63

Testes em tmp e subprocessos reais descartáveis: emissão e reemissão negada, reinicialização na geração 2, store ausente/corrupto, concorrência de signers, erro de fsync, ponte não-root e real `SO_PEERCRED`, JSON adversarial, claim PROD/stale, blueprint não executável. Cobrir no workflow Linux/Docker e documentar logs GitHub Actions. DELPI Verifier uma única rodada ao fim do pacote consolidado. Revisor humano independente continua não comprovado; exceção formal se aplicável, posterior.

**Estado operacional:** bloqueado, quatro ferramentas MCP READ, PREPARE/ACT OFF. **Não executar pull/deploy, não gerar chave privada operacional e não alterar o `srv-api`. Progresso conservador: 58%.**
