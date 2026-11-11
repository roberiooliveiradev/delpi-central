# Controle de matéria-prima — índice da evolução

Vertical de **cadastro/alteração de matéria-prima** na Minha DELPI.

**Hoje:** app iframe `controle-mp` (repositório `controle_mp`).  
**Alvo:** nativo em **Minhas Solicitações** (solicitante) + **fila do analista** no mesmo MFE.  
**Este diretório não autoriza implementação.**

| Documento | Conteúdo |
|-----------|----------|
| [EVOLUCAO.md](./EVOLUCAO.md) | Objetivo, evidência, arquitetura alvo, fases, proibições, cutover |

## Relacionados

| Documento | Papel |
|-----------|--------|
| [../my-requests/PLAYBOOK.md](../my-requests/PLAYBOOK.md) | Request Engine e plugabilidade de tipos |
| [../my-requests/WIREFRAMES.md](../my-requests/WIREFRAMES.md) | Telas `/mine` e `/work-queue` |
| [../../10-guias-operacionais/conectar-aplicacao-iframe.md](../../10-guias-operacionais/conectar-aplicacao-iframe.md) | Iframe vigente |
| Repositório `controle_mp` | Sistema legado em produção |

## PRC-REF-023 — decisão atual (11/11/2026)

> **IMPORTANTE:** O texto histórico de `EVOLUCAO.md` apresenta um alvo antigo de integração com `requests-api`. Para o PRC-REF-023 vigente, preserva-se **Engineering API como autoridade oficial do caso**, **Portal Engenharia como atendimento** e **Minhas Solicitações como entrada/consulta/correção**; não criar caso paralelo.

- [PRC-REF-023 — Validação CREATE e UX unificada de devolução/correção](./PRC-REF-023-CREATE-VALIDATION-AND-UNIFIED-CORRECTION-UX-2026-11-11.md) — decisão funcional atual, wireframes completos do modal e card, regras CREATE × UPDATE, campos vazios, tabelas/atributos e critérios de aceite. **TARGET** até implementação validada.
- [Issue canônica #154](https://github.com/roberiooliveiradev/delpi-central/issues/154) — acompanhamento de execução e evidências.
