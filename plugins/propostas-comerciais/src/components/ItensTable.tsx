import type {
  PropostaComercialItem,
  PropostaComercialItemTextDraft,
} from "../types/propostasComerciais";
import {NativeTextControl, dataTableBemClasses} from "@delpi/plugin-ui/index";
import {
  DEFAULT_ITEM_COLUMN_LABELS,
  ITEM_COLUMN_KEYS,
  type PropostaComercialItemColumnKey,
} from "../constants/propostaComercialLabels";
import { displayValue, formatLoteMinimoMil } from "../utils/format";
import { PcNativeTextAreaControl } from "./pcFormFields";

const PC_TABLE = dataTableBemClasses("pc");


type ItensTableReadOnlyProps = {
  items: PropostaComercialItem[];
  editable?: false;
  columnLabels?: Partial<Record<PropostaComercialItemColumnKey, string>>;
};

type ItensTableEditableProps = {
  items: PropostaComercialItem[];
  editable: true;
  itemDrafts: PropostaComercialItemTextDraft[];
  columnLabels: Record<PropostaComercialItemColumnKey, string>;
  onItemFieldChange: (
    itemKey: string,
    field: keyof Pick<
      PropostaComercialItemTextDraft,
      "descricao" | "referencia_cliente" | "ncm" | "prazo_dias"
    >,
    value: string,
  ) => void;
  onColumnLabelChange: (field: PropostaComercialItemColumnKey, value: string) => void;
};

type ItensTableProps = ItensTableReadOnlyProps | ItensTableEditableProps;

function resolveColumnLabels(
  labels?: Partial<Record<PropostaComercialItemColumnKey, string>>,
): Record<PropostaComercialItemColumnKey, string> {
  return {
    ...DEFAULT_ITEM_COLUMN_LABELS,
    ...labels,
  };
}

function TableCellInput({
  value,
  onChange,
  multiline = false,
  compact = false,
  "aria-label": ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  compact?: boolean;
  "aria-label": string;
}) {
  const className = [
    "pc-table-input",
    multiline ? "pc-table-input--multiline" : "",
    compact ? "pc-table-input--compact" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (multiline) {
    return (
      <PcNativeTextAreaControl
        className={className}
        rows={2}
        value={value}
        aria-label={ariaLabel}
        onChange={onChange}
      />
    );
  }

  return (
    <NativeTextControl
      type="text"
      className={className}
      value={value}
      aria-label={ariaLabel}
      onChange={onChange}
    />
  );
}

export function ItensTable(props: ItensTableProps) {
  const { items } = props;
  const columnLabels = props.editable
    ? props.columnLabels
    : resolveColumnLabels(props.columnLabels);

  return (
    <div className={PC_TABLE.wrap}>
      <table className={`${PC_TABLE.table} pc-table--items`}>
        <thead>
          <tr>
            {ITEM_COLUMN_KEYS.map((columnKey) => (
              <th key={columnKey}>
                {props.editable ? (
                  <TableCellInput
                    compact
                    aria-label={`Rótulo da coluna ${columnLabels[columnKey]}`}
                    value={columnLabels[columnKey]}
                    onChange={(value) => props.onColumnLabelChange(columnKey, value)}
                  />
                ) : (
                  columnLabels[columnKey]
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const draft = props.editable ? props.itemDrafts[index] : null;

            return (
              <tr key={item.item}>
                <td data-label={columnLabels.item}>{displayValue(item.item)}</td>
                <td data-label={columnLabels.produto}>{displayValue(item.produto)}</td>
                <td data-label={columnLabels.descricao}>
                  {props.editable && draft ? (
                    <TableCellInput
                      aria-label={`Descrição do item ${item.item}`}
                      value={draft.descricao}
                      multiline
                      onChange={(value) =>
                        props.onItemFieldChange(item.item, "descricao", value)
                      }
                    />
                  ) : (
                    displayValue(item.descricao)
                  )}
                </td>
                <td data-label={columnLabels.referencia_cliente}>
                  {props.editable && draft ? (
                    <TableCellInput
                      aria-label={`Referência do cliente do item ${item.item}`}
                      value={draft.referencia_cliente}
                      onChange={(value) =>
                        props.onItemFieldChange(item.item, "referencia_cliente", value)
                      }
                    />
                  ) : (
                    displayValue(item.referencia_cliente)
                  )}
                </td>
                <td data-label={columnLabels.ncm}>
                  {props.editable && draft ? (
                    <TableCellInput
                      aria-label={`NCM do item ${item.item}`}
                      value={draft.ncm}
                      onChange={(value) => props.onItemFieldChange(item.item, "ncm", value)}
                    />
                  ) : (
                    displayValue(item.ncm)
                  )}
                </td>
                <td data-label={columnLabels.quantidade}>
                  {item.quantidade.toLocaleString("pt-BR")} {item.unidade}
                </td>
                <td data-label={columnLabels.valor_bruto}>
                  {displayValue(item.valor_bruto_r_mil_formatado ?? item.preco_unitario)}
                </td>
                <td data-label={columnLabels.valor_liquido}>
                  {displayValue(item.valor_liquido_r_mil_formatado)}
                </td>
                <td data-label={columnLabels.total}>{displayValue(item.valor_total)}</td>
                <td data-label={columnLabels.prazo}>
                  {props.editable && draft ? (
                    <TableCellInput
                      compact
                      aria-label={`Prazo do item ${item.item}`}
                      value={draft.prazo_dias}
                      onChange={(value) =>
                        props.onItemFieldChange(item.item, "prazo_dias", value)
                      }
                    />
                  ) : (
                    displayValue(item.prazo_dias)
                  )}
                </td>
                <td data-label={columnLabels.lote_minimo}>
                  {formatLoteMinimoMil(item.lote_minimo_numerico ?? item.lote_minimo)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
