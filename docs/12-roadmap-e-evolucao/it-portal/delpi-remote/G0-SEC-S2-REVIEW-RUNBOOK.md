# G0-SEC-S2 | Pacote de governanca para aprovacao privada

**Status:** MINUTA, **Gate:** G0-SEC. **Estado esperado:** BLOQUEADO.
**Registro publico de revisao:** [G0-SEC-S2-REVIEW-REGISTER.json](G0-SEC-S2-REVIEW-REGISTER.json).

Esta entrega cria propostas e testes estaticos **sem permitir instalacao ou controle remoto**. Aprovacao de risco, plano de rede real, assinaturas, evidencias e nomes ficam em ferramenta **privada** da empresa, nao no GitHub publico.

## Pacote preparado

| Documento | Finalidade | Revisao necessaria |
|---|---|---|
| [Politica de suporte e privacidade](G0-SEC-S2-POLICY-PRIVACY.md) | Modalidades assistida/nao assistida, transparencia, logs minimos, tratamento de dados | TI, RH, Juridico, Seguranca |
| [Isolamento e limites de rede](G0-SEC-S2-NETWORK-ISOLATION.md) | Fronteiras navegador/Core/broker/motor/Windows e matriz deny-by-default | Infra e Seguranca |
| [Revogacao, incidente e recuperacao](G0-SEC-S2-RECOVERY-AND-REVOCATION.md) | Kill switch, bloqueio por operador/dispositivo, backup/restore, tabletop | TI e Infra/Seguranca |
| [Registro de pendencias](G0-SEC-S2-REVIEW-REGISTER.json) | 10 controles exigindo aprovacao privada, todos pendentes | Funcoes de decisao, sem nomes |

## Como revisar em canal privado, sem liberar o acesso

1. Criar change/revisao de seguranca em ferramenta corporativa apropriada e anexar as **minutas**, nunca o token/segredo ou o inventario real. Designar responsaveis reais **no sistema privado**, nao no codigo.
2. Revisar com RH/Juridico uso nao assistido, aviso ao colaborador, fundamento do tratamento, dados minimos, direitos e retencao. Sem deliberação sobre esses pontos, **NO-GO**.
3. Infra/Seguranca valida, fora do GitHub, topologia segregada, origens/destinos, portas e regras, TLS/certificados, roteamento negado a producao e ausencia de acesso externo. Sem prova de isolamento, **NO-GO**.
4. TI/Seguranca define fluxos de revogacao por operador, computador e global. Ensaio tabletop seguido de teste real apenas no futuro laboratorio autorizado.
5. A equipe define **RPO/RTO e prazos de retencao** somente depois da avaliacao de impacto, protege backup e **executa teste de restauracao** em ambiente descartavel. Nao considerar backup concluido como restore testado.
6. Reavaliar no upstream o aviso de exploracao ativa e a regressao Windows da release MeshCentral candidata. Sem prova de mitigacao e artefato pinado com SHA-256, **NO-GO** para G3.
7. Registrar decisao privada, justificativa, riscos residuais, owner, validade e rollback. Um link publico para a politica nao substitui os registros assinados ou o teste.
8. Somente depois de G0-SEC aprovado formalmente e sem risco impeditivo um novo incremento separado podera implementar e testar G3 em segmento laboratorio, sem incluir computadores produtivos.

## Verificador automatico

```bash
cd it-portal-api
python -m it_portal_app.domain.remote_policy_review --repo-root ..
python -m pytest -q tests/test_remote_policy_review.py
```

Saida esperada: `G0-SEC-S2 BLOCKED`, exit 0. Isso significa que a estrutura das propostas existe e continua **sem autorizacao de deploy**. Saida `INVALID` indica omissao, mudanca indevida de status, modificacao de owner ou tentativa de marcar remoto ativo. Nenhum sinal verde tecnico equivale a aprovacao corporativa.

**Proibido neste incremento:** habilitar MeshCentral, criar client administrativo, broker, rota de controle, dependencia de agentes remotos, permissoes `it-portal.remote.*`, portas e regras reais, migracao ou deploy de API/frontend.

**Rollback:** sem efeitos no runtime. Para corrigir um documento/teste, criar commit auditavel. Nao remover gates anteriores G0-SEC-S0/S1.

## Proximo ponto verificavel

Avaliacao **privada** das minutas e plano de testes G3/LAB apos aprovacao; piloto G2-S1..S3 permanece presencial, independente do G0-SEC. A issue principal e [#179](https://github.com/roberiooliveiradev/delpi-central/issues/179).
