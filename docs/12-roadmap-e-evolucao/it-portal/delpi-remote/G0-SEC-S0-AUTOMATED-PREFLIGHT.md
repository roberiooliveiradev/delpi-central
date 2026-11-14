# G0-SEC-S0 | Preflight automatizado do acesso remoto (somente offline)

**Data:** 2026-11-13  
**Estado:** Codigo de seguranca preparado, **SEM APROVACAO formal de G0-SEC**.
**Escopo:** impedir regressao acidental que exponha controle remoto antes do aceite. Nao implementa nem inicia sessao remota.

## Por que esta etapa vem antes do G3

Os componentes G2-S1 a G2-S3 foram preparados e o operador informou sucesso do deploy da infraestrutura G2-S2. A autenticacao do agente e a coleta em Windows real ainda dependem de piloto presencial.

O G3-ENGINE (motor MeshCentral) depende de G0-SEC; implementar um servidor remoto antes de resolver o gate abriria uma capacidade de alto risco. Em 23/10/2026 os mantenedores publicaram MeshCentral **1.3.1** com alerta emergencial sobre **exploracao ativa capaz de tomar servidores e clientes**. A nota usa linguagem cautelosa sobre a correcao, portanto **nao tratar v1.3.1 como homologada ou automaticamente segura**.

Fontes publicas oficiais:
- https://github.com/Ylianst/MeshCentral/releases/tag/1.3.1
- https://github.com/Ylianst/MeshCentral/security/advisories
- https://docs.meshcentral.com/meshcentral/security/
- https://docs.meshcentral.com/meshcentral/
- https://github.com/Ylianst/MeshCentral/blob/master/LICENSE (Apache-2.0; conferir tambem artefato efetivo)

## Entregas deste incremento

- `G0-SEC-CHECKPOINTS.json`: checklist estruturado de **12 gates**. `pending`, `in_review` ou `documented` significam apenas acompanhamento do trabalho; `documented` exige link publico, mas **nao significa aprovado**.
- `it-portal-api/it_portal_app/domain/remote_security_readiness.py`: verificador puramente local e sem efeitos que valida checklist e observa se houve introducao prematura de rota remota, servidor no Compose, flag on ou permissao `it-portal.remote.*` no manifesto.
- `it-portal-api/tests/test_remote_security_readiness.py`: cenarios negativos para bypass, permissao, flag, rota, registro invalido e referencia ausente.
- CI `.github/workflows/it-portal-api.yml`: executa verificador de bloqueio antes do pytest. **O resultado esperado e `G0-SEC BLOCKED` e exit code 0**, indicando ausencia de superficie remota acidental, nao aceite de seguranca.

## Limites

O codigo nao substitui controle de runtime, pentest, supervisao de infraestrutura, RH/Juridico, gestor nem autorizacao formal. O registro de evidencias e publico; **nao colocar nomes de operadores, IPs internos, secrets, tokens, hostnames reais, caminhos privados, inventario de usuarios ou referencias internas detalhadas**.

O script falha se achar superficie remota introduzida no Portal/Compose antes da aprovacao. E um **alarme de CI e revisao estatica**, nao um firewall e nao um mecanismo de aprovacao automatico. O operador humano permanece o unico responsavel pelo aceite formal registrado em local privado.

## Execucao sem deploy

No checkout com Python 3.12 e dependencias do projeto:

```bash
cd it-portal-api
python -m it_portal_app.domain.remote_security_readiness --repo-root ..
python -m pytest -q tests/test_remote_security_readiness.py
```

Esperado: `G0-SEC BLOCKED` + testes aprovados. Se aparecer `INVALID`, corrigir a inconformidade antes de qualquer merge. **Nunca alterar o manifesto apenas para obter CI verde**.

## Gates ainda pendentes

1. Revisao de versao/licenca/SBOM/advisories do MeshCentral, artefato imutavel, assinatura/digest e decisao de motor.
2. Arquitetura de rede isolada, TLS, VPN, firewall e nao exposicao publica.
3. Modelo OIDC/Keycloak/MFA fresh e RBAC especifico `it-portal.remote.connect` com allowlist por operador e dispositivo.
4. Broker sem credenciais privilegiadas no navegador; capacidades de uso unico, escopo minimo, TTL curto.
5. Sessao auditavel, notificacao, revogacao forcada/kill switch, backup/restauracao.
6. Politica de RH/LGPD, retencao e testes de seguranca/integracao; piloto fisico Windows.

Todos os 12 checkpoints tecnicos permanecem sem **aceite formal**. O motor e o broker ficam bloqueados ate aprovacao registrada fora do repositorio.

**Proximo passo:** revisar `G3-ADR-002-MESHCENTRAL-SECURITY.md` e submeter decisao de seguranca; prosseguir em paralelo com homologacao presencial do agente G2 quando disponivel. Nenhuma migration, API de comando, container, segredo, permissao ou frontend e implantado por este incremento.
