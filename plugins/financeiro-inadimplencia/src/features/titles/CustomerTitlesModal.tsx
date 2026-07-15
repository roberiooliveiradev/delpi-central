import { useEffect, useState } from "react";

import { ErrorState } from "../../components/ErrorState";
import { EmptyState } from "../../components/EmptyState";
import { FiModal } from "../../components/FiModal";
import { LoadingState } from "../../components/LoadingState";
import { Pagination } from "../../components/Pagination";
import {
  defaultTitulosTableState,
  useInadimplenciaTitulos,
  type TitulosTableState,
} from "../../hooks/useInadimplenciaTitulos";
import type {
  PeriodFilter,
  SelectedCustomer,
  TituloStatus,
} from "../../types/inadimplencia";
import { DELAY_RANGE_OPTIONS } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatInteger,
  formatTituloLabel,
} from "../../utils/formatters";

type CustomerTitlesModalProps = {
  open: boolean;
  customer: SelectedCustomer | null;
  period: PeriodFilter;
  onClose: () => void;
};

type TitlesModalBodyProps = {
  customer: SelectedCustomer;
  period: PeriodFilter;
};

/**
 * Corpo com estado local; remonta via `key` ao trocar cliente
 * para limpar filtros/busca sem effect de reset.
 */
function TitlesModalBody({ customer, period }: TitlesModalBodyProps) {
  const [tableState, setTableState] = useState<TitulosTableState>(defaultTitulosTableState);
  const [draftSearch, setDraftSearch] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setTableState((current) =>
        current.search === draftSearch
          ? current
          : { ...current, search: draftSearch, page: 1 },
      );
    }, 350);
    return () => window.clearTimeout(timer);
  }, [draftSearch]);

  const titulos = useInadimplenciaTitulos(
    period,
    customer.cliente_codigo,
    customer.loja,
    tableState,
    true,
  );

  const items = titulos.data?.items ?? [];
  const pagination = titulos.data?.pagination;
  const totalPages = pagination?.total_pages ?? 1;

  return (
    <>
      <div className="fi-titulos-toolbar">
        <label className="fi-field">
          <span>Status</span>
          <select
            value={tableState.status}
            onChange={(event) =>
              setTableState((current) => ({
                ...current,
                status: event.target.value as TituloStatus,
                page: 1,
              }))
            }
          >
            <option value="late">Somente atrasados</option>
            <option value="on_time">Em dia</option>
            <option value="all">Todos</option>
          </select>
        </label>

        <label className="fi-field">
          <span>Faixa</span>
          <select
            value={tableState.delayRange}
            onChange={(event) =>
              setTableState((current) => ({
                ...current,
                delayRange: event.target.value,
                page: 1,
              }))
            }
          >
            {DELAY_RANGE_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="fi-field fi-field--grow">
          <span>Busca</span>
          <input
            type="search"
            value={draftSearch}
            placeholder="Número, prefixo ou nome"
            onChange={(event) => setDraftSearch(event.target.value)}
          />
        </label>
      </div>

      {titulos.error ? (
        <ErrorState message={titulos.error} onRetry={titulos.reload} />
      ) : null}

      {titulos.isLoading && items.length === 0 ? (
        <LoadingState message="Carregando títulos…" />
      ) : null}

      {!titulos.isLoading && !titulos.error && items.length === 0 ? (
        <EmptyState
          title="Nenhum título encontrado"
          message="Nenhum título encontrado para os filtros aplicados."
        />
      ) : null}

      {items.length > 0 ? (
        <>
          <div className={`fi-table-wrap${titulos.isLoading ? " fi-table-wrap--loading" : ""}`}>
            <table className="fi-table">
              <thead>
                <tr>
                  <th scope="col">Título</th>
                  <th scope="col">Tipo</th>
                  <th scope="col">Emissão</th>
                  <th scope="col">Vencimento real</th>
                  <th scope="col">Baixa</th>
                  <th scope="col" className="fi-table__numeric">
                    Valor
                  </th>
                  <th scope="col" className="fi-table__numeric">
                    Dias de atraso
                  </th>
                  <th scope="col">Faixa</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={`${item.prefixo}-${item.numero}-${item.parcela}-${item.data_baixa}-${item.valor_titulo}`}
                  >
                    <td data-label="Título">
                      {formatTituloLabel(item.prefixo, item.numero, item.parcela)}
                    </td>
                    <td data-label="Tipo">{item.tipo || "—"}</td>
                    <td data-label="Emissão">{formatDatePtBr(item.data_emissao)}</td>
                    <td data-label="Vencimento real">
                      {formatDatePtBr(item.data_vencimento_real)}
                    </td>
                    <td data-label="Baixa">{formatDatePtBr(item.data_baixa)}</td>
                    <td data-label="Valor" className="fi-table__numeric">
                      {formatCurrencyBrl(item.valor_titulo)}
                    </td>
                    <td data-label="Dias de atraso" className="fi-table__numeric">
                      {formatInteger(item.dias_atraso)}
                    </td>
                    <td data-label="Faixa">{item.faixa_atraso?.rotulo || item.faixa_atraso?.codigo || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pagination ? (
            <Pagination
              page={pagination.page}
              pageSize={pagination.page_size}
              total={pagination.total_items}
              totalPages={totalPages}
              onPageChange={(page) => setTableState((current) => ({ ...current, page }))}
              hideWhenSinglePage
            />
          ) : null}
        </>
      ) : null}
    </>
  );
}

export function CustomerTitlesModal({
  open,
  customer,
  period,
  onClose,
}: CustomerTitlesModalProps) {
  return (
    <FiModal
      open={open}
      title="Títulos do cliente"
      subtitle={
        customer
          ? `${customer.nome_cliente} · ${customer.cliente_codigo}/${customer.loja} · ${formatInteger(customer.titulos_atraso)} atrasado(s) · ${formatCurrencyBrl(customer.valor_atraso)}`
          : undefined
      }
      onClose={onClose}
    >
      {open && customer ? (
        <TitlesModalBody
          key={`${customer.cliente_codigo}-${customer.loja}`}
          customer={customer}
          period={period}
        />
      ) : null}
    </FiModal>
  );
}
