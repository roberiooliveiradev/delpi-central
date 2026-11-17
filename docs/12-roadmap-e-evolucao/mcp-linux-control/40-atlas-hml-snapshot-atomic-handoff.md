# ATLAS P2.2h.2bk-bn | Publicacao atomica candidata do snapshot HML

**Data:** 17/11/2026 (BRT) | **Estado:** PR Draft source-only | **Servidor:** intocado | **PREPARE/ACT:** OFF

## Contexto e objetivo

A PR #236 foi mesclada em `0531a525eadf24fb7db3f18f1d04dbf76d1226b2`. O pacote anterior implementou apenas leitura segura por FD de `inspect-snapshot.json` para a arquitetura B **ainda candidata**, com testes de corrida, symlink e origem nao confiavel. O passo desta PR e provar a **troca atomica entre duas geracoes de snapshot**, em testes descartaveis, sem disponibilizar um escritor operacional.

O caminho de producao continua **inexistente/nao ativado**. O novo modulo `atlas_hml_snapshot_publisher_candidate.py` **nao tem CLI, timer, daemon, service unit, API HTTP, MCP tool nem funcao publica de escrita para o diretorio fixo**. A publicacao de arquivos ocorre apenas no diretório `tmp_path` dos testes.

## Implementacao

- `build_hml_snapshot_claim`: recebe somente `RuntimeContainer` tipado e `observed_at` timezone-aware, produz JSON HML com 11 campos allowlisted. Ignora quaisquer campos Docker brutos de Config.Env/Mounts/Networks. Valida o proprio payload contra `review_untrusted_snapshot` antes de retornar. Mesmo com dados validos, a origem do timestamp e da imagem continua nao atestada.
- `_publish_in_review_directory`: helper interno, para **fixtures** e arquitetura. Antes de escrever, valida os bytes, a idade da declaracao, o alvo HML e o estado BLOCKED; exige um diretorio POSIX existente, com owner/grupo esperado e modo exato `0750`.
- Recusa sobrescrever destino que seja symlink, FIFO, hardlink, owner/grupo/modo diferente de root:`atlas-hml`/`0640` na politica futura. O caminho de destino e fixo, `inspect-snapshot.json`.
- Cria nome estagiado aleatorio com `O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, modo inicial `0600`. Verifica owner, filesystem e hardlink, configura grupo e modo final `0640`, grava todos os bytes (ou recusa escrita curta), `fsync` do arquivo e reconfirma o inode do nome estagiado.
- Revê o destino antes de `os.replace(src_dir_fd=..., dst_dir_fd=...)`, realiza `fsync` do diretorio e verifica que o nome final e o descriptor aberto pertencem ao mesmo inode com owner/grupo/modo esperados.
- Se a publicacao falhar **antes de rename**, o destino anterior permanece intacto e o nome estagiado e removido em best-effort. Se falhar **depois** de rename (ex.: `fsync` do diretorio), nao ha rollback atomico garantido: o helper retorna erro e a proxima leitura permanece sujeita a validacao. Isto nao e garantia de recuperacao de host.

## Testes em CI

Arquivo `linux-ops-mcp/tests/test_atlas_hml_snapshot_publisher_candidate.py`, usando apenas `tmp_path`, sem `/run` real nem `docker.sock`:

- Handoff integrado ao leitor da PR #236, ambas as geracoes com `status=blocked`, `prepare_eligible=false`, `can_execute=false`.
- Rejeicao de IDs/booleans invalidos, origem PROD, diretorio inseguro, owner/grupo, symlink, FIFO, hardlink e destino inseguro.
- Falhas sinteticas de `os.replace`, `fsync`, escrita parcial, substituicao do temporario apos `fsync` e JSON antigo.
- Nao habilita nenhuma tool MCP adicional; as quatro de leitura existentes continuam intactas.

## Limites e seguranca

**Nao** confundir atomicidade observavel do `rename` com autenticidade/assinatura, isolamento de privilegios, anti-replay, DAC/ACL atestada, atomicidade em disco sob falha de energia, seccomp de unidade, imagem OCI implantada ou capacidade autorizada de deploy. Um processo comprometido com acesso root/Docker pode forjar todos os metadados. Este codigo nao inclui nem executa produtor que abra o Docker Engine, nao resolve a fronteira de alto privilegio. Tambem nao muda o proxy UDS em uso, `atlas_hml_unix_proxy.py`, que ainda nao aceita `HMLSnapshotInspector` em seu caminho operacional.

### Decisoes abertas na issue #232

1. Revisor independente deve aprovar/rejeitar a arquitetura B (produtor one-shot privilegiado + atendente UDS sem Docker); requisitos de controle real de `docker.sock`, FDs herdados e isolamento do produtor.
2. Analisar autenticidade do producer e do snapshot, protecao contra replay, lock multi-produtor, `fsync` com falha, ACL/LSM e politica de retencao.
3. Revisar unidades `systemd` propostas separadamente, sem instalacao antecipada, com Seccomp, NoNewPrivileges, capabilities e rollback.
4. Somente outra mudanca explicita pode instalar diretorio, socket, service/timer, alterar permissoes, conectar ao Engine e testar em `srv-api`; nunca afetar Public Hub PROD.
5. `delpi-verifier` e revisao humana continuam gates; Git HEAD nao e release implantada. PREPARE/ACT **permanecem OFF**.

## Definition of Done desta PR

- [ ] Cinco jobs CI no HEAD da PR (Linux MCP, Docker e PG descartaveis, auditoria, arquitetura)
- [ ] Review independente `delpi-verifier` (nao disponivel aqui)
- [ ] Revisao humana de Seguranca para o modelo upstream
- [ ] Nenhuma mudanca no servidor/Keycloak/DB/Docker, nenhum merge automatico
- [ ] Invariantes `status=blocked`, `prepare_eligible=false` e `can_execute=false` mantidas

**Proximo pacote sugerido:** contrato de origem de dados do produtor e mecanismo de supervisionamento somente em desenho/testes, apos parecer da issue #232. Nao criar unidade persistente por inferencia do CI.
