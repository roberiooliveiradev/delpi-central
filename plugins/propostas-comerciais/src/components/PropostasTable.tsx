import { dataTableBemClasses } from "@delpi/plugin-ui/index";
import type { PropostaComercialListItem } from "../types/propostasComerciais";
import { StatusBadge } from "./StatusBadge";
import { displayValue } from "../utils/format";

const PC_TABLE = dataTableBemClasses("pc");


type PropostasTableProps = {
  items: PropostaComercialListItem[];
  onSelect: (propostaInterna: string) => void;
};

export function PropostasTable({ items, onSelect }: PropostasTableProps) {
  return (
    <div className={PC_TABLE.wrap}>
      <table className="pc-table">
        <thead>
          <tr>
            <th>Nº OV</th>
            <th>Proposta</th>
            <th>Cliente</th>
            <th>Data</th>
            <th>Versão</th>
            <th>Filial</th>
            <th>Itens</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.proposta_interna}-${item.versao}`}
              className="pc-table__row--clickable"
              onClick={() => onSelect(item.proposta_interna)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(item.proposta_interna);
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`Abrir proposta ${item.numero_ov}`}
            >
              <td data-label="Nº OV">
                <strong>{displayValue(item.numero_ov)}</strong>
              </td>
              <td data-label="Proposta">{displayValue(item.proposta_interna)}</td>
              <td data-label="Cliente">{displayValue(item.cliente)}</td>
              <td data-label="Data">{displayValue(item.data)}</td>
              <td data-label="Versão">{displayValue(item.versao)}</td>
              <td data-label="Filial">{displayValue(item.filial)}</td>
              <td data-label="Itens">{item.quantidade_itens}</td>
              <td data-label="Status">
                <StatusBadge status="A" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
