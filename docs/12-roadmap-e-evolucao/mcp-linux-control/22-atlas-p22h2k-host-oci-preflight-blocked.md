# ATLAS | P2.2h.2k: bloqueio fail-closed entre host assinado e intent OCI

**Data:** 16/11/2026. **Estado:** candidato em Pull Request, aguardando gates e revisao independente. **PREPARE_DISABLED / ACT_DISABLED.**

## Fonte de verdade e problema

As PRs #209 a #211 implementaram os leitores de proveniencia GitHub, digest de imagem no GHCR e sua correlacao. A PR #212, ja integrada, adicionou comprovante assinado de host v2 com nome de container, projeto Compose, estado Docker, commit, ImageID e challenge. O v2 continua retornando `checkout_clean=False`, `migrations_safe=False`, `rollback_ready=False` e `challenge_consumed=False` porque a assinatura Docker **nao** prova a elegibilidade do PREPARE.

Esta fase mede a **consistencia da intencao OCI com a base instalada**, rejeitando alvos, digests, autenticacao de host e nonce divergentes. Ela nao converte o comprovante em autorizacao.

## Entrega

Novo modulo puro `linux-ops-mcp/linux_ops_mcp/deploy_host_oci_preflight.py`:
- `HostOCIIntentPreview`: projecao tipada de ambiente/servico, commits de base e destino, dois ImageIDs, manifesto OCI, SHA da declaracao de proveniencia, hash do nonce e rollback image. Essa estrutura e **shape-only**: construir uma dataclass nao autentica proveniencia.
- `inspect_host_oci_preflight_v2`: exige target `RuntimeTarget` validado e mapeia estritamente `(hml,public-hub) -> (delpi-hml-public-hub,delpi-hml)` e `(prod,public-hub) -> (delpi-public-hub,infra)`. A identidade do host e o segredo HMAC devem ser emitidos e administrados exclusivamente pelo backend/host, nunca por HTTP, MCP, GitHub comments ou dados do usuario.
- Verifica SHA de commit completo em lower hex, digest SHA-256 OCI completo e campos hash; recusa intencoes sem conformidade ou direcionadas a ambiente/servico diferentes.
- Calcula `SHA256(bytes.fromhex(challenge))` igual ao contrato do journal V016 e compara em tempo constante com `intent.host_challenge_sha256` **antes de ler** o receipt.
- Chama `verify_host_runtime_receipt_v2` no proprio modulo, garantindo MAC valido, challenge exatamente correspondente, nome de container, labels/projeto e frescor de até 90 segundos. Nao aceita uma instância `VerifiedHostRuntimeSnapshot` fornecida por terceiros no lugar dos bytes assinados.
- Para receipt autentico, compara commit/ImageID de base, verifica `running` e `healthy` e sinaliza divergencias de target igual a base, rollback apontando a imagem errada ou rollback intent falso.
- Retorna `HostOCIPreflightReport` imutavel: `status=blocked` e `blocks` finitos. **Nao** fornece candidate, aprovacao, ticket de ACT nem mutacao do journal.
- Bloqueios que jamais sao considerados satisfeitos neste incremento: `OCI_CI_RELEASE_NOT_REVERIFIED`, `OCI_CHECKOUT_NOT_ATTESTED`, `OCI_MIGRATIONS_NOT_ATTESTED`, `OCI_ROLLBACK_NOT_ATTESTED`, `OCI_CHALLENGE_NOT_CONSUMED`, `OCI_CORE_AUTHORIZATION_MISSING`.

## Testes e CI

`linux-ops-mcp/tests/test_deploy_host_oci_preflight.py` exercita assinatura HMAC local via os componentes reais `issue_host_runtime_receipt_v2` e `verify_host_runtime_receipt_v2` com `RuntimeInspector` simulado. Cobre assinatura alterada, chave errada, nonce reciclado, alvo fora da allowlist, drift de commit e ImageID, health falso, clocks invalidos/obsoletos, intencao malformada, rollback divergente e prova perfeitamente coerente que **mesmo assim permanece bloqueada**. O workflow de integracao ATLAS executa os novos testes no job Docker descartavel. Nenhum teste acessa sistemas ou chaves PROD.

## Limites e dependencia futura

- A verificacao HMAC **nao consome** o challenge DB. O par nonce + digest deve ser recuperado de autoridade do journal, e o consumo unico precisa ocorrer na mesma transacao de persistencia do PREPARE com papel de escrita minimo. Nenhuma mutacao de DB aparece nesta PR.
- A `HostOCIIntentPreview` nao substitui `CIReleaseEvidence` verificada pelo backend: o alvo de CI continua nao revalidado aqui e a combinacao com a release real ainda precisa ser desenhada sob limites de importacao entre bounded contexts.
- `checkout_clean` nao e confiavel ate leitor independente de Git, assim como migrations/backup/rollback. Nao inferir prontidao por health Docker.
- `Core` precisa de identidade humana e grant dedicado, aprovado e auditavel. A autorizacao ACT necessita etapa, permissao e validacao adicional e continuara bloqueada.
- Sem endpoints, manifests, Compose, montagem de Docker socket, secret/env novo, migracao ou scripts de deploy. A implantacao manual existente continua operacional.

## Portoes de aceite

- [ ] 5 checks GitHub CI e testes do novo modulo aprovados em PR.
- [ ] `delpi-verifier` executado por agente independente; nao disponivel nesta sessao.
- [ ] Revisao humana e seguranca das credenciais e mapeamento de host.
- [ ] Teste HML em processo segregado com proxy Docker somente leitura, nonce persistido, chaves fora do Git e acordo de ownership.
- [ ] Verificacao real GitHub/GHCR com digest assinado autorizada.
- [ ] Evidencia de checkout limpo, migracoes seguras, rollback/backup provados, Core grant e writer transacional antes de qualquer POST PREPARE.

**Proxima etapa recomendada:** planejar uma fonte independente e restrita para medir checkout Git sem comando de deploy nem credencial de escrita, conectada a um host witness separado. Não habilitar ACT.
