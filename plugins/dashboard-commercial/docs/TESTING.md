# Testes — Dashboard Comercial

```bash
cd plugins/dashboard-commercial && npm run ci
# ou na raiz:
./scripts/ci/build-dashboard-commercial.sh
```

Testes unitários de exportação: `npm run test` (Vitest em `src/export/`). Ver [export.md](./export.md).

## Docker

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api dashboard-commercial
```

UI: `http://localhost/apps/dashboard-commercial`

## Registro

```bash
export TOKEN="<jwt apps.manage>"
./plugins/dashboard-commercial/scripts/register-manifest.sh
```

Conceda `dashboard-commercial.view` no RBAC.

## Smoke HTTP

```bash
export TOKEN="<jwt>"
./scripts/homologacao/check-dashboard-commercial.sh
```

## Checklist UI

- [ ] 5 KPIs carregam com período padrão (mês atual)
- [ ] Filtro de filial altera conversão e clientes novos
- [ ] Gráficos ROL e funil exibem dados
- [ ] Impressão oculta filtros e mostra resumo do período
- [ ] Recarregar página mantém filtros na URL
- [ ] Exportação CSV/Excel/PDF no header do dashboard (relatório completo)
- [ ] Exportação por seção: KPIs, ROL, funil, propostas
- [ ] Detalhe OV: exportação completa inclui BOM quando disponível

### Detalhe da proposta (`/proposta/{proposal_number}`)

Ver [DETALHE-PROPOSTA.md](./DETALHE-PROPOSTA.md).

| Área | O que validar |
|------|----------------|
| Navegação | Voltar preserva período/filial na URL |
| Cabeçalho | Status, datas, cliente, vendedor; tooltips |
| Produtos | Tabela ADJ010; badges de tipo PA/PI |
| BOM | Árvore expandível; legenda; oculta quando sem estrutura |
| Histórico | Timeline / tabela AIJ010 |
| Exportação | CSV / Excel / PDF por seção e relatório completo |
| Ações | Atualizar recarrega detalhe + histórico + BOM |
