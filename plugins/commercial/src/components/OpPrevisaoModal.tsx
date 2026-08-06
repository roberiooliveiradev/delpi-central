import { PVA_COL_NUMERIC, PVA_TABLE } from "../ui/tableChrome";
import { PVA_STATE_BOX } from "../ui/stateChrome";
import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { formatDisplayDate, resolveOpVsPedidoPrazo } from "../utils/dates";
import { formatQuantity } from "../utils/format";
import { getLineOpPrevisao } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { PvaModal } from "./PvaModal";
import { StatusBadge } from "./StatusBadge";

type OpPrevisaoModalProps = {
  item: PedidosVendaAbertosItem | null;
  open: boolean;
  onClose: () => void;
};

function prazoTone(status: ReturnType<typeof resolveOpVsPedidoPrazo>["status"]) {
  if (status === "no_prazo") return "success" as const;
  if (status === "atrasado") return "danger" as const;
  return "neutral" as const;
}

export function OpPrevisaoModal({ item, open, onClose }: OpPrevisaoModalProps) {
  if (!item) return null;

  const previsao = getLineOpPrevisao(item);
  const subtitle = `${item.nome_cliente || "Cliente"} · Pedido ${item.pedido || "—"} · Linha ${item.linha || "—"} · Produto ${item.produto || "—"}`;

  return (
    <PvaModal
      open={open}
      onClose={onClose}
      title="Previsão de entrega por OP"
      subtitle={subtitle}
    >
      <div className="pva-op-modal">
        <section className="pva-op-modal__summary" aria-label="Resumo da linha">
          <dl className="pva-op-modal__metrics">
            <div>
              <dt>Saldo do pedido</dt>
              <dd>{formatQuantity(item.saldo)}</dd>
            </div>
            <div>
              <dt>Estoque alocado</dt>
              <dd>{formatQuantity(getAllocatedStock(item))}</dd>
            </div>
            <div>
              <dt>Saldo a produzir</dt>
              <dd>{formatQuantity(previsao.saldoNecessarioProducao)}</dd>
            </div>
            <div>
              <dt>Entrega pedido</dt>
              <dd>{formatDisplayDate(item.data_entrega)}</dd>
            </div>
            <div>
              <dt>Previsão de entrega</dt>
              <dd>{previsao.previsaoLabel}</dd>
            </div>
            {previsao.saldoFaltanteProducao > 0 ? (
              <div>
                <dt>Ainda falta produzir</dt>
                <dd>{formatQuantity(previsao.saldoFaltanteProducao)}</dd>
              </div>
            ) : null}
          </dl>
          <p className="pva-op-modal__note">
            OPs compartilhadas por produto/filial, alocadas por ordem de entrega do pedido. Indicação
            operacional — não reserva formal ao cliente.
          </p>
        </section>

        {previsao.opsUtilizadas.length > 0 ? (
          <div className={`${PVA_TABLE.wrap} pva-op-modal__table-wrap`}>
            <table className={`${PVA_TABLE.table} pva-op-modal__table`}>
              <thead>
                <tr>
                  <th>Número OP</th>
                  <th className={PVA_COL_NUMERIC}>Saldo OP</th>
                  <th className={PVA_COL_NUMERIC}>Alocado p/ o pedido</th>
                  <th>Fim previsto</th>
                  <th>Status</th>
                  <th>Observação</th>
                </tr>
              </thead>
              <tbody>
                {previsao.opsUtilizadas.map((entry) => {
                  const prazo = resolveOpVsPedidoPrazo(entry.data_fim_prevista_op, item.data_entrega);

                  return (
                  <tr key={entry.numero_op}>
                    <td>{entry.numero_op || "—"}</td>
                    <td className={PVA_COL_NUMERIC}>{formatQuantity(entry.saldo_op_total)}</td>
                    <td className={PVA_COL_NUMERIC}>{formatQuantity(entry.saldo_alocado)}</td>
                    <td>
                      {entry.data_fim_prevista_op
                        ? formatDisplayDate(entry.data_fim_prevista_op)
                        : "Sem data prevista"}
                    </td>
                    <td>
                      {prazo.status === "indeterminado" ? (
                        "—"
                      ) : (
                        <StatusBadge
                          badge={{ label: prazo.label, tone: prazoTone(prazo.status) }}
                        />
                      )}
                    </td>
                    <td className="pva-op-modal__observacao">{entry.observacao_op || "—"}</td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={PVA_STATE_BOX}>Nenhuma OP alocada para esta linha.</p>
        )}
      </div>
    </PvaModal>
  );
}
