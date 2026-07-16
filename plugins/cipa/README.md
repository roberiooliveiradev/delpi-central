# Plugin CIPA

Gestão de atas da CIPA com assinatura manuscrita, versionamento e isolamento por filial (`01` / `02`).

## Fluxo

```text
Portal → plugins/cipa (MFE) → /apps/cipa-api → schema cipa (postgres-plugins)
```

## Rotas UI

| Path | Descrição |
|------|-----------|
| `/apps/cipa` | Início — escolha de unidade e pendências |
| `/apps/cipa/filial-01` | Lista de atas SC |
| `/apps/cipa/filial-02` | Lista de atas ES |
| `/apps/cipa/filial-{xx}/minutes/new` | Nova ata |
| `/apps/cipa/filial-{xx}/minutes/{id}` | Modo de leitura formal, impressão e download do PDF |
| `/apps/cipa/filial-{xx}/minutes/{id}/edit` | Edição |
| `/apps/cipa/filial-{xx}/minutes/{id}/sign` | Assinatura da ata |
| `/apps/cipa/my-signature` | Perfil de assinatura pessoal (nome + PNG) — exige `cipa.sign` |
| `/apps/cipa/pending` | Pendências do usuário |

### Assinatura pessoal

Cada usuário com `cipa.sign` configura **apenas a própria** assinatura em `/apps/cipa/my-signature`. Na tela de assinar uma ata, o nome é pré-preenchido e há o botão **Usar assinatura cadastrada** (o desenho no pad continua disponível só para aquela ata).

### Leitura e PDF oficial

O detalhe usa os componentes documentais compartilhados de `@delpi/plugin-ui`
(`DocumentReader`, `DocumentPage`, cabeçalho, rodapé e assinatura). A impressão
é uma conveniência do navegador; o artefato oficial é sempre gerado pelo
`cipa-api` em `GET /minutes/{id}/export.pdf`, com logo/marca d'água, conteúdo,
papéis, imagens de assinatura, validação e rodapé paginado.

## API

Base: `/apps/cipa-api` — ver [cipa-api/README.md](../../cipa-api/README.md).

## Permissões

Modelo enxuto (6 códigos) — ver `cipa.manifest.json`:

| Código | Escopo |
|--------|--------|
| `cipa.view` | Consulta e auditoria |
| `cipa.manage` | CRUD, envio, finalização, PDF e signatários |
| `cipa.sign` | Assinar, recusar e configurar assinatura pessoal |
| `cipa.admin` | Tudo, em todas as unidades |
| `cipa.unit.filial-01` | Dados da filial 01 |
| `cipa.unit.filial-02` | Dados da filial 02 |

Combine **uma ação** (`view`, `manage` ou `sign`) com **a unidade** desejada. `cipa.admin` dispensa o restante.

## Dev

```bash
cd plugins/cipa && npm install && npm run build
TOKEN=… bash scripts/register-manifest.sh
./infra/scripts/up-dev-sequential.sh --fase api --build cipa-api
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build cipa
```

## Smoke

```bash
curl -fsS http://localhost/apps/cipa/assets/remoteEntry.js | head -c 80
curl -fsS http://localhost/apps/cipa-api/health
```
