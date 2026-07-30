# Comitê de Ética e Conduta

Microfrontend federado para **registrar e assinar atas** do Comitê de Ética e Conduta, com cadastro permanente de membros e notificações no sino do portal para quem precisa assinar.

API dedicada: [`comite-etica-conduta-api`](../../comite-etica-conduta-api/README.md).  
Roadmap: [`docs/12-roadmap-e-evolucao/comite-etica-conduta/`](../../docs/12-roadmap-e-evolucao/comite-etica-conduta/).

## Rotas UI

| Path | Conteúdo |
|------|----------|
| `/apps/comite-etica-conduta` / `/atas` | Lista de atas |
| `/atas/new`, `/atas/{id}/edit` | Editor |
| `/atas/{id}` | Leitura |
| `/atas/{id}/sign` | Assinatura |
| `/atas/pending` | Pendências do usuário |
| `/membros` | Cadastro do comitê |
| `/minha-assinatura` | Perfil PNG |

## Permissões

- `comite-etica-conduta.view`
- `comite-etica-conduta.manage`
- `comite-etica-conduta.sign`

## Fluxo

```text
Rascunho / Em revisão → Enviar para assinatura (notifica signatários)
  → Aguardando / Parcial → Assinada (notifica gestores) | Recusa → Em revisão
  → Finalizar → PDF
```

## Dev

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build comite-etica-conduta
```

Pré-requisito: `plugin-ui` e `comite-etica-conduta-api` no ar.
