# ATLAS | Etapa 62: assinador local Ed25519, ciclo de chaves e prontidão do piloto HML

**17/11/2026 | SOURCE-ONLY | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)**  
**Sem instalação, deploy, criação de chave real ou alteração do Docker compartilhado.**

## 1. Decisões do responsável (preservadas, não viram SEC-01)

| Decisão | Tratamento neste pacote |
|---|---|
| Responsável assume governança e aceitação de riscos | Registrada; **não** classificada como parecer humano independente |
| Risco residual do produtor root + Docker compartilhado aceito | Documentado; producer permanece host-equivalente |
| Ed25519 local no `srv-api` autorizada como direção | Implementada em código candidato |
| Chave privada pode ficar no host (root pode comprometê-la) | Aceito; `authenticity_independent=False` |
| Assinador externo independente = evolução futura | Contrato keyless permanece disponível |
| GLPI como cofre de cópia criptografada de recuperação | Documentado; **sem** integração automática |
| Arquitetura B para piloto HML | Mantida |

Se a política exigir SEC-01 independente, a **exceção de governança permanece pendente de validação formal**.

## 2. Como a assinatura local funciona (linguagem simples)

1. O produtor monta o snapshot HML (`delpi-hml-public-hub`) e um **pedido canônico** de assinatura (sem chave privada).
2. O **assinador local** (identidade de processo distinta, sem Docker) valida o pedido: escopo HML, geração, peer UID, anti-replay.
3. Assina com Ed25519 e devolve **somente** a assinatura.
4. O envelope versionado é selado e publicado atomicamente.
5. O apresentador verifica com a **chave pública** e aplica continuidade/TTL/lifecycle.
6. Tudo permanece `status=blocked`; PREPARE/ACT OFF.

## 3. Componentes implementados

| Módulo | Função |
|---|---|
| `atlas_hml_b_key_lifecycle.py` | Geração efêmera, PKCS#8 criptografado, DAC do diretório, rotação/revogação, ID GLPI |
| `atlas_hml_b_local_signer.py` | Assinador local (in-process + UDS one-shot), peer auth, anti-replay, não-API genérica |
| `atlas_hml_b_local_signed_pipeline.py` | Cadeia integrada claim→sign→seal→publish→verify→continuity |
| `atlas_hml_b_pilot_readiness.py` | Matriz de prontidão do piloto (sempre blocked) |
| `.review` signer service/socket | Blueprints não instaláveis |
| Reuso | envelope, trust, external intent, continuity, lifecycle, producer, presenter |

## 4. Chaves e GLPI (recuperação)

**Identificador GLPI:** `ATLAS-HML-ED25519-PRIVATE-V1`

Procedimento operacional futuro (não executado nesta etapa):

1. Gerar par efêmero/operacional **fora do Git**.
2. Exportar pública para o keyring do apresentador.
3. Gerar cópia PKCS#8 criptografada (`build_encrypted_recovery_copy`).
4. Guardar o blob no GLPI sob o identificador acima; **frase de proteção separada** (não no Git, não em argv, não em arquivo world-readable).
5. Validar recuperação em exercício controlado (`recover_private_from_encrypted`).
6. Rotação: nova chave ativa + antiga revogada no keyring; atualizar GLPI com nova versão/identificador se necessário.

Nenhuma chave privada real é gerada, publicada ou instalada neste PR.

## 5. Matriz de prontidão do piloto

| Categoria | Exemplos |
|---|---|
| Implementado e comprovado em CI | Envelope, trust, local signer, intent, pipeline, lifecycle, LISTEN_*, continuity FD |
| Só em fixtures descartáveis | UDS peer auth, DAC de chave, PKCS#8 roundtrip, E2E publish |
| Exige observação Linux real | systemd real, UID/GID atlas-hml-signer, LSM, FDs herdados no host |
| Exige autorização explícita | Instalar units, criar usuários/dirs em `/run`, colocar chave operacional |
| Risco aceito pelo responsável | Produtor root+Docker; chave local no mesmo host |
| Residual sem comprovação | `flock` advisory vs root; bootstrap de estado; domínio criptográfico independente |

## 6. Checklist futuro de ativação (NÃO executar agora)

- [ ] Change-control e janela autorizada
- [ ] Contas/grupos/dirs/ACLs conforme blueprint `.review`
- [ ] Chave operacional + cópia GLPI + frase segregada
- [ ] Ensaios host: peer UID, ausência Docker no signer/presenter
- [ ] Rollback/parada documentados e ensaiados
- [ ] SEC-01 independente **ou** exceção formal registrada
- [ ] Confirmação: PREPARE/ACT continuam OFF

## 7. Progresso

**58%** — avanço material de assinatura local integrada e prontidão documentada do piloto; operação HML ainda bloqueada.
