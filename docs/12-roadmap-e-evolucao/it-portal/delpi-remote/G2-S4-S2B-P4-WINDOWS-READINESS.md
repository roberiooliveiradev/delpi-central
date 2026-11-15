# G2-S4-S2b-P4 | Readiness Windows somente leitura

**Estado:** EM REVISAO, 14/11/2026. Sem enrollment/attestation, rotas, Keycloak, login, grants ou acesso remoto.

## Escopo implementado

- `it-portal-api/collectors/windows_workstation/Collect-ItPortalWorkstationTrustReadiness.ps1`: apenas leitura de `Get-Tpm`, `Win32_Tpm.SpecVersion` e `Confirm-SecureBootUEFI`. Nao instala nada, nao altera TPM/BIOS/UEFI, nao cria chave/certificado, nao grava arquivo, nao consulta rede e nao requer credenciais.
- Relatorio JSON de campos fixos: versao, origem nao autenticada, data UTC, plataforma, TPM presente/ready/versao, Secure Boot e tres marcadores **sempre false**: `hardware_attested`, `key_bound`, `activation_authorized`. Nao coleta hostname, serial, MAC, IP, usuario, certificados, EK, chaves privadas nem ID corporativo.
- `workstation_trust_readiness.py`: validador puro, fail-closed, tamanho <=2048 bytes, esquema estrito, duplicidade JSON proibida, data UTC com idade maxima de 15 min e tolerancia futura de 2 min. Classificacao: `CANDIDATE` somente para Windows com TPM 2.0 ready + Secure Boot enabled, `INCONCLUSIVE` quando recurso nao pode ser verificado, `NOT_READY` em falha conhecida, `INVALID` quando dados inconsistentes/injetados. **Em todos estados: attested=false, enrollment_authorized=false.**
- CI PowerShell verifica parser e executa smoke somente leitura no Linux; pytest exercita estados negativos. O teste no Linux NAO valida resultado TPM no Windows real.

## Como testar futuramente com equipamento piloto autorizado

Abrir PowerShell 5.1 em uma estacao Windows de laboratorio isolada (sem producao critica), apos aprovar janela de HML. Executar **somente**:

```powershell
& '.\Collect-ItPortalWorkstationTrustReadiness.ps1'
```

Guardar evidencias no repositório privado/GLPI com acesso restrito, minimizando detalhes. Nunca copiar identidade do dispositivo, serial, certificado, EK ou dados do usuario para issue ou git publico. **Nao usar** `Set-Tpm`, `Clear-Tpm`, habilitar Secure Boot ou gerar certificado/chave durante este teste.

### Como interpretar

| Resultado | Interpretacao | Proximo passo |
|---|---|---|
| `CANDIDATE` | Recursos locais observados | Testar attestation real + ancoragem em HML, sem liberar |
| `INCONCLUSIVE` | Permissao, WMI ou firmware inconclusivo | Revisao manual de ambiente, sem alterar config |
| `NOT_READY` | Falta requisito local | Avaliar elegibilidade e alternativa com TI/Seguranca |
| `INVALID` | Payload ausente/adulterado/inconsistente | Rejeitar e investigar |

## Restricao criptografica importante

O P3 usa assinaturas Ed25519 e chave publica preconfiavel; isto nao prova que a chave privada esta em TPM. Microsoft Platform Crypto Provider e TPM key attestation documentam a ancoragem hardware de chave RSA, nao assumem Ed25519. Para liberar enrollment e necessario projeto especifico de chave/hardware, ancoragem corporativa, revogacao, politica de exportabilidade, verificacao de cadeia e desafio vinculado ao equipamento, registro com MFA/RBAC e canal seguro de segredo. O P4 nao fornece nenhum desses mecanismos.

## Testes automatizados

```bash
cd it-portal-api
python -m pytest -q tests/test_workstation_trust_readiness.py
python -m it_portal_app.domain.workstation_bootstrap_readiness --repo-root ..
```

CI executa tambem `Test-ItPortalWorkstationTrustReadiness.ps1` com pwsh, parser e suite geral. Nenhum Windows real/Keycloak HML foi testado por este incremento.

## Rollback e proxima tarefa

Nenhum estado de banco ou Windows e modificado; rollback e reverter apenas scripts, validador, testes e docs. Proximo passo: confirmar pipeline verde, obter inventario de capacidades do equipamento piloto HML e escolher protocolo attestation de chave aprovado, nunca usar apenas sinal de TPM/Secure Boot para aprovar identidades. G0-SEC continua bloqueado.

[Roadmap](README.md) | [Seguranca](SECURITY-GATES.md) | [P3](G2-S4-S2B-P3-SIGNED-CONSUMPTION.md) | [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179)
