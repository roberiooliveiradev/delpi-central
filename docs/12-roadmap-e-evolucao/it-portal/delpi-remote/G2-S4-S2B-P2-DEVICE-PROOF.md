# G2-S4-S2b-P2 | Prova de posse criptografica offline (SEM ativacao)

**Estado:** EM REVISAO, 14/11/2026. Apenas biblioteca pura, nao exposta em FastAPI nem vinculada a nenhum agente Windows.

## Contrato de desenvolvimento

- `workstation_device_proof.py`: cria desafio com 32 bytes de nonce gerados com fonte criptografica, UUID canonico do ticket, UUID canonico da workstation, audiencia exclusiva para inventario, data de emissao e expiração entre 60 e 600 segundos.
- O desafio tem codificacao JSON canonica para assinar; o verificador usa Ed25519, recebe somente uma chave publica **previamente confiada por processo independente** e valida assinatura, integridade do contexto e janela de tempo. Erro, chave errada, resposta adulterada, prazo expirado ou escopo divergente falham fechado.
- `tests/test_workstation_device_proof.py`: chaves privadas aleatorias apenas dentro dos testes e casos positivos/negativos. Sem log de segredo ou chave persistida.

## Limite critico: nao e attestation Windows

Prova de posse de chave Ed25519 **NAO** prova por si que a resposta veio de uma maquina corporativa autentica. A verificacao so tem valor com registro/validacao independente da chave, prova de confianca inicial, isolamento de credenciais, politica de distribuicao e, se exigido, TPM/hardware-backed attestation conforme capacidade Windows real. **Nao** aceitar chave publica fornecida junto da assinatura ou vinculacao baseada apenas em hostname/IP/MAC. Nao criar cliente Keycloak automaticamente ao receber assinatura.

## Fluxo futuro que nao foi implementado

1. TI aprova piloto em processo privado (RBAC fresh, MFA recente, motivo/chamado) e autoriza especificamente a maquina.
2. Processo de registro seguro comprova a chave publica do agente corporativo, com assinatura de instalador e protecao local, sem aceitar chaves arbitrarias da rede.
3. API em HML cria ticket efemero P1 por workstation e desafio P2 ligado ao ticket e a identidade previamente confiada.
4. Agente responde assinando desafio com chave privada protegida; API verifica assinatura, prazo e identidade preconfiada.
5. Dentro do fluxo autorizado e transacional, banco consome ticket uma unica vez, audita e confirma que registro continua ativo. Revogacao ou rejeicao bloqueiam imediatamente. Desafio assinado nao e credencial de acesso remoto.
6. Somente apos teste de falhas, concorrencia, key rotation e Keycloak real pode-se propor grant S2S minimo. O controle remoto continua gate G0-SEC independente.

## Comandos de verificacao

```bash
cd it-portal-api
python -m pytest -q tests/test_workstation_device_proof.py
python -m it_portal_app.domain.workstation_bootstrap_readiness --repo-root ..
```

**Evidencia local:** 18 testes em Python 3.13 + biblioteca cryptography PASS. **CI de repositorio / Keycloak real / Windows 11 / TPM nao validado** nesta entrega ate confirmacao automatizada.

**Proximo passo:** validar CI V014 e deste modulo; preparar matrizes de seguranca para registro de chaves, sem publicar dispositivo, IP, segredos ou topologia no GitHub publico.

[Roadmap](README.md) | [P1](G2-S4-S2B-P1-TICKET-LEDGER.md) | [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179).
