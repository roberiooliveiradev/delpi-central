# Cadastro de Kaizen — atalho no portal

App iframe da Minha DELPI que **abre o formulário público** de sugestão Kaizen por unidade. Não possui MFE, container nem API própria.

O formulário continua no **public-hub**. A gestão operacional dos kaizens continua no **Kaizômetro**.

## Visão geral

```text
Portal (menu / launcher)
  → rota SC ou ES (RBAC)
  → nova aba
  → public-hub /p/kaizen/sugestao/aberto?unidade=01|02
  → POST /apps/api-delpi/public/kaizen/suggestions
```

| Camada | Responsabilidade |
|--------|------------------|
| **Este app** | Manifesto, permissões e atalhos SC/ES no portal |
| **public-hub** | Formulário público (wizard, sem login) |
| **api-delpi** | `POST /public/kaizen/suggestions` |
| **Kaizômetro** | Cadastro operacional, QR e acompanhamento |

## Rotas e permissões

| Unidade | Rota no portal | Destino | Permissão |
|---------|----------------|---------|-----------|
| Santa Catarina (01) | `/apps/kaizen-suggestion/sc` | [formulário SC](https://minhadelpi.com.br/p/kaizen/sugestao/aberto?unidade=01) | `kaizen-suggestion.view.filial-sc` |
| Espírito Santo (02) | `/apps/kaizen-suggestion/es` | [formulário ES](https://minhadelpi.com.br/p/kaizen/sugestao/aberto?unidade=02) | `kaizen-suggestion.view.filial-es` |

O clique no menu abre o destino em **nova aba** (`openInNewTab`). O `ui.renderMode` é `external`.

## Como o usuário usa

1. No launcher ou no menu, abra **Cadastro de Kaizen**.
2. Escolha **SC** ou **ES** conforme a unidade.
3. O formulário público abre em nova aba, já com a unidade correta.
4. Preencha Identificação e Melhoria e envie a sugestão.

Quem não tiver a permissão da unidade não vê aquela rota.

## Registro

O manifesto **não concede acesso**. Depois do register, atribua as permissões no RBAC.

```bash
TOKEN="$(bash infra/scripts/get-dev-token.sh)" \
  bash plugins/kaizen-suggestion/scripts/register-manifest.sh
```

Em produção: Admin → Apps, ou `POST /core-api/admin/apps/register` com o JSON.

Guia: [registrar-plugin.md](../../docs/10-guias-operacionais/registrar-plugin.md).

## O que este app não faz

- Não substitui o Kaizômetro (listagem, ficha, aprovação, evidências).
- Não reimplementa o formulário nem a API pública.
- Não precisa de Docker, gateway de assets nem `plugin-ui`.

## Ajuda

O formulário público é a tela do usuário. Dúvidas de preenchimento ficam no próprio wizard do public-hub. Este app só publica os atalhos SC/ES no portal autenticado.
