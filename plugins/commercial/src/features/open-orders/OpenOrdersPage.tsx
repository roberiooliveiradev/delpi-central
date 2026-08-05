import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import {
  ActionButton,
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  exportPayloadToCsv,
  type DataTableColumn,
  type TableExportPayload,
} from "@delpi/plugin-ui/index";

import { getOpenOrders, getOpsAbertas, resolveOrderStatus } from "../../api/openOrdersApi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import {
  CommercialLoadingCard,
  CommercialSelectField,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmFiltersKit,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
} from "../../app/commercialUi";
import type { OpenOrderItem, OpsAbertaResumo } from "../../types/openOrders";

const { FiltersRow, FilterInputField, FilterSelectField } = cmFiltersKit;

export function OpenOrdersPage() {
  const { isAdmin, myPortfolio, sellers, sellerIdFilter, setSellerIdFilter } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<OpenOrderItem[]>([]);
  const [portfolioMessage, setPortfolioMessage] = useState<string | null>(null);

  const [opsAbertasResumo, setOpsAbertasResumo] = useState<OpsAbertaResumo[]>([]);
  const [opsAbertasTotal, setOpsAbertasTotal] = useState(0);
  const [opsAbertasLoading, setOpsAbertasLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [filialFilter, setFilialFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const effectiveSellerId = isAdmin ? sellerIdFilter : (myPortfolio?.id ?? null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getOpenOrders(controller.signal, { sellerId: effectiveSellerId })
      .then((data) => {
        setItems(data.items ?? []);
        setPortfolioMessage(data.portfolio?.message ?? null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar pedidos.");
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [effectiveSellerId]);

  useEffect(() => {
    const controller = new AbortController();
    setOpsAbertasLoading(true);

    getOpsAbertas(controller.signal)
      .then((data) => {
        setOpsAbertasResumo(data.resumo ?? []);
        setOpsAbertasTotal(data.items?.length ?? 0);
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setOpsAbertasResumo([]);
        setOpsAbertasTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setOpsAbertasLoading(false);
      });

    return () => controller.abort();
  }, []);

  const filialOptions = useMemo(() => {
    const unique = Array.from(
      new Set(items.map((item) => item.filial?.trim()).filter((value): value is string => Boolean(value))),
    ).sort((a, b) => a.localeCompare(b, "pt-BR"));
    return unique.map((value) => ({ value, label: value }));
  }, [items]);

  const sellerOptions = useMemo(
    () => sellers.map((seller) => ({ value: seller.id, label: seller.display_name })),
    [sellers],
  );

  const filteredItems = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase("pt-BR");
    const normalizedStatus = statusFilter.trim().toLocaleLowerCase("pt-BR");

    return items.filter((item) => {
      if (filialFilter && item.filial?.trim() !== filialFilter) return false;

      if (normalizedStatus) {
        const status = resolveOrderStatus(item).toLocaleLowerCase("pt-BR");
        if (!status.includes(normalizedStatus)) return false;
      }

      if (normalizedSearch) {
        const haystack = [item.pedido, item.nome_cliente, item.produto]
          .filter(Boolean)
          .join(" ")
          .toLocaleLowerCase("pt-BR");
        if (!haystack.includes(normalizedSearch)) return false;
      }

      return true;
    });
  }, [items, search, filialFilter, statusFilter]);

  const columns = useMemo<DataTableColumn<OpenOrderItem>[]>(
    () => [
      { key: "pedido", header: "Pedido", render: (row) => row.pedido },
      { key: "cliente", header: "Cliente", render: (row) => row.nome_cliente },
      { key: "produto", header: "Produto", render: (row) => row.produto },
      {
        key: "qty",
        header: "Qtd.",
        align: "right",
        render: (row) => (row.saldo ?? row.quantidade).toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => resolveOrderStatus(row),
      },
      { key: "filial", header: "Filial", render: (row) => row.filial },
    ],
    [],
  );

  function handleExportCsv() {
    const payload: TableExportPayload = {
      title: "Pedidos em aberto",
      columns: [
        { key: "pedido", label: "Pedido" },
        { key: "cliente", label: "Cliente" },
        { key: "produto", label: "Produto" },
        { key: "qty", label: "Qtd." },
        { key: "status", label: "Status" },
        { key: "filial", label: "Filial" },
      ],
      rows: filteredItems.map((row) => ({
        pedido: row.pedido,
        cliente: row.nome_cliente,
        produto: row.produto,
        qty: row.saldo ?? row.quantidade,
        status: resolveOrderStatus(row),
        filial: row.filial,
      })),
    };
    exportPayloadToCsv(payload);
  }

  const topOpsResumo = useMemo(
    () =>
      [...opsAbertasResumo]
        .sort((a, b) => (b.saldo_total_ops ?? 0) - (a.saldo_total_ops ?? 0))
        .slice(0, 5),
    [opsAbertasResumo],
  );

  return (
    <section className="cm-page-stack">
      {portfolioMessage ? (
        <StateBanner variant="default" classNames={cmStateBannerClassNames}>
          {portfolioMessage}
        </StateBanner>
      ) : null}

      <SectionCard
        title="Pedidos em aberto"
        subtitle={`${filteredItems.length} de ${items.length} linha(s) no escopo atual`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <FiltersRow
          trailing={
            <ActionButton
              variant="ghost"
              onClick={handleExportCsv}
              disabled={filteredItems.length === 0}
              aria-label="Exportar CSV"
            >
              <Download size={16} strokeWidth={1.75} aria-hidden="true" />
              Exportar CSV
            </ActionButton>
          }
        >
          <FilterInputField
            label="Buscar"
            type="search"
            value={search}
            onChange={setSearch}
            placeholder="Pedido, cliente ou produto"
          />
          <FilterSelectField
            label="Filial"
            value={filialFilter}
            onChange={setFilialFilter}
            options={filialOptions}
            placeholderOption="Todas"
            searchable
          />
          <FilterInputField
            label="Status"
            type="text"
            value={statusFilter}
            onChange={setStatusFilter}
            placeholder="Filtrar por status"
          />
          {isAdmin ? (
            <CommercialSelectField
              label="Carteira"
              value={sellerIdFilter ?? ""}
              onChange={(value: string) => setSellerIdFilter(value || null)}
              options={sellerOptions}
              allowEmpty
              emptyLabel="Todas as carteiras"
              searchable
            />
          ) : null}
        </FiltersRow>

        {loading ? (
          <CommercialLoadingCard title="Carregando pedidos" variant="panel" />
        ) : error ? (
          <StateBanner variant="error" classNames={cmStateBannerClassNames}>
            {error}
          </StateBanner>
        ) : filteredItems.length === 0 ? (
          <EmptyState
            title="Nenhum pedido em aberto"
            message="Não há linhas para os filtros atuais."
            defaultMessage="Não há linhas para os filtros atuais."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <DataTable
            rows={filteredItems}
            columns={columns}
            rowKey={(row: OpenOrderItem, index: number) => `${row.pedido}-${row.produto}-${index}`}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        )}
      </SectionCard>

      <SectionCard
        title="OPs abertas"
        subtitle={
          opsAbertasLoading ? "Carregando…" : `${opsAbertasTotal} ordem(ns) de produção em aberto`
        }
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {opsAbertasLoading ? (
          <CommercialLoadingCard title="Carregando OPs abertas" variant="panel" />
        ) : topOpsResumo.length === 0 ? (
          <EmptyState
            title="Nenhuma OP em aberto"
            message="Não há ordens de produção em aberto no momento."
            defaultMessage="Não há ordens de produção em aberto no momento."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <ul className="cm-ops-abertas-list">
            {topOpsResumo.map((resumo) => (
              <li key={`${resumo.filial}-${resumo.produto}`}>
                <strong>{resumo.descricao_produto || resumo.produto}</strong>
                <span>
                  Filial {resumo.filial} · {resumo.quantidade_ops_abertas} OP(s) · saldo{" "}
                  {resumo.saldo_total_ops.toLocaleString("pt-BR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </section>
  );
}
