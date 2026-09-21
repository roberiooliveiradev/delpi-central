# 07 — Requisitos

> **Única lista de requisitos deste produto:** `HD-001…HD-018`
> **Ordem:** [`06-plano-execucao.md`](./06-plano-execucao.md)

Estado de cada um, até existir código: `ATENDIDO_NO_PLANO`. Nenhum está `PROVEN` em runtime da Minha DELPI.

| ID | Requisito | Decisão | Etapa | Prova |
|---|---|---|---|---|
| HD-001 | O chamado continua no GLPI. A Minha DELPI não cria banco de chamado | helpdesk-api persiste só sessão OAuth | E1.S1 | não existe tabela de ticket no schema novo |
| HD-002 | Dono do módulo é a helpdesk-api. A api-delpi não participa | bounded context próprio | E1.S1 | MFE sem chamada à api-delpi |
| HD-003 | Agir em nome do usuário via authorization code no mesmo Keycloak/SAML | cliente `minha-delpi-helpdesk` | E1.S2 | token GLPI do sujeito do JWT |
| HD-004 | Segredo e refresh token fora do browser e do log | cifra + env | E1.S2 | teste de log e de isolamento entre usuários |
| HD-005 | Sem sessão GLPI, a API pede o vínculo em vez de abrir chamado anônimo | 409 `glpi_link_required` | E1.S2 | chamada sem sessão |
| HD-006 | BFF publicado em `/apps/helpdesk-api` com a redirect já cadastrada | gateway + Compose | E1.S3 | callback bate com a URI do cliente |
| HD-007 | Categoria e urgência vêm do GLPI | adapter, sem lista fixa | E2.S1 | alteração no GLPI aparece na API |
| HD-008 | Listar os chamados visíveis para aquela pessoa | `GET /tickets` | E2.S2 | lista igual à visão do token |
| HD-009 | Detalhe com linha do tempo | `GET /tickets/{id}` | E2.S2 | chamado alheio não vaza corpo |
| HD-010 | Abrir chamado com título, descrição, categoria e urgência | `POST /tickets` | E3.S1 | chamado no GLPI com o solicitante do token |
| HD-011 | A tela não escolhe solicitante nem entidade | payload sem esses campos | E3.S1 | teste negativo rejeita campo extra de solicitante |
| HD-012 | Reenvio da mesma intenção não duplica chamado | `Idempotency-Key`, sem retry de POST | E3.S1 | duas requisições, um id |
| HD-013 | Incluir acompanhamento no chamado visível | `POST .../followups` | E3.S2 | texto na timeline; alheio não recebe |
| HD-014 | Tela nativa substitui o iframe | MFE federado | E4.S1 | menu abre `/apps/helpdesk` |
| HD-015 | Lista, formulário e detalhe com vazio, erro, loading e proibido | UI | E4.S2 | 403 não vira lista vazia; F5 no detalhe |
| HD-016 | Ajuda in-app no mesmo entregável da tela | conteúdo do plugin | E4.S3 | manual cobre abrir e acompanhar |
| HD-017 | Uma entrada de helpdesk no portal | corte do manifest iframe | E4.S4 | path antigo redireciona |
| HD-018 | Prova positive, irmã e negativa, mais um usuário real | E5 | E5.S1, E5.S2 | ledger `PROVEN` só depois da homologação |

## Herdados da plataforma

Não viram HD próprio:

- JWT e resolução de `helpdesk.access` no padrão das APIs de módulo.
- Module Federation e `@delpi/plugin-ui` no MFE novo.
- Timeout e classificação de erro HTTP no cliente do GLPI, detalhados no contrato.

## Fora com justificativa

| Item | Estado |
|---|---|
| Anexo, satisfação, fila técnica, mudança, problema, seletor de entidade | `FORA_DO_ESCOPO_COM_JUSTIFICATIVA` — onda H5 |
| Corrigir o `entry` do iframe antes do MFE | `FORA_DO_ESCOPO_COM_JUSTIFICATIVA` — o iframe deixa de ser o produto em E4 |
| Ligar API legada ou concessão password | proibido; não é requisito |
