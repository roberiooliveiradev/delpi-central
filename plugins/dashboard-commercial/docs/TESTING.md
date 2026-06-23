# Testes — Dashboard Comercial

```bash
cd plugins/dashboard-commercial && npm run ci
# ou na raiz:
./scripts/ci/build-dashboard-commercial.sh
```

Testes unitários: `npm run test` (Vitest em `src/export/` e `src/utils/`). Ver [export.md](./export.md).

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
- [ ] Exportação PNG do gráfico ROL gera imagem completa (eixos, linhas, legenda)
- [ ] Exportação PNG do funil inclui KPIs e etapas
- [ ] Impressão oculta filtros e mostra resumo do período (Ctrl+P)
- [ ] Recarregar página mantém filtros na URL
- [ ] Exportação CSV/Excel/PDF no header do dashboard (relatório completo)
- [ ] Exportação por seção: KPIs, ROL, funil, propostas
- [ ] Detalhe OV: exportação completa inclui BOM quando disponível

### Tabela «Propostas do período»

Ver [PROPOSTAS-PERIODO.md](./PROPOSTAS-PERIODO.md).

| Área | O que validar |
|------|----------------|
| Status | Dropdown **dentro do card** (Todas / Ganhas / Em aberto) |
| Busca | Digitar termo (ex.: `weg`, `ganha`, número) — debounce e nova requisição; total atualiza |
| Ordenação | Clicar coluna — ordem vem do backend (não só da página visível) |
| Paginação | Seletor 10/20/50/100; botões de página + «Ir para»; faixa «Exibindo X–Y de Z» |
| Exportação | CSV/Excel/PDF/PNG da tabela; PNG nos gráficos ROL e funil |
| Navegação | Clique na linha abre detalhe com filial e revisão corretas |

#### Testes automatizados

```bash
# MFE
cd plugins/dashboard-commercial && npm run ci

# api-delpi (container)
docker exec delpi-api-delpi python -m pytest \
  tests/test_commercial_proposal_list_search_service.py \
  tests/test_commercial_proposals_repository.py \
  tests/test_list_commercial_proposals_use_case.py -q
```

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
