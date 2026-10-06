import type { NfeItemDetail, NfeMappedItem, NfeMappingStatus } from "../../domain/types";

export type NfeProductMappingView =
  | { status: "supplier_required" }
  | { status: "loading" }
  | { status: "issuer_mismatch"; detail?: NfeItemDetail }
  | { status: "ready"; detail: NfeItemDetail }
  | { status: "error"; message: string };

const STATUS_LABEL: Record<NfeMappingStatus, string> = {
  mapped: "Relacionado",
  unmapped: "Não relacionado",
  ambiguous: "Relação ambígua",
};

type Props = {
  view: NfeProductMappingView;
};

export function NfeProductMappingPanel({ view }: Props) {
  return (
    <section className="lnf-card lnf-form-section" data-testid="nfe-product-mapping">
      <h2>Itens da NF-e</h2>
      {view.status === "supplier_required" ? (
        <p className="lnf-hint" data-testid="nfe-mapping-waiting">
          Selecione o fornecedor/loja para visualizar a tradução dos produtos.
        </p>
      ) : null}
      {view.status === "loading" ? (
        <p className="lnf-hint" data-testid="nfe-mapping-loading">
          Carregando itens e a relação Produto x Fornecedor…
        </p>
      ) : null}
      {view.status === "error" ? (
        <p className="lnf-error" role="alert" data-testid="nfe-mapping-error">
          {view.message}
        </p>
      ) : null}
      {view.status === "issuer_mismatch" ? (
        <div data-testid="nfe-mapping-mismatch">
          <p className="lnf-error" role="alert">
            O fornecedor selecionado não corresponde ao emitente da NF-e. A tradução dos produtos não foi aplicada.
          </p>
          <ItemTable items={view.detail?.items ?? []} hideInternal />
        </div>
      ) : null}
      {view.status === "ready" ? <ReadyDetail detail={view.detail} /> : null}
    </section>
  );
}

function ReadyDetail({ detail }: { detail: NfeItemDetail }) {
  const items = detail.items ?? [];
  if (items.length === 0) {
    return (
      <p className="lnf-hint" data-testid="nfe-mapping-empty">
        Esta NF-e não tem itens de produto.
      </p>
    );
  }
  const summary = detail.summary ?? countSummary(items);
  return (
    <>
      <p className="lnf-hint" data-testid="nfe-item-summary">
        {countLabel(summary.items, "item", "itens")} · {countLabel(summary.mapped, "relacionado", "relacionados")} ·{" "}
        {countLabel(summary.unmapped, "não relacionado", "não relacionados")} ·{" "}
        {countLabel(summary.ambiguous, "ambíguo", "ambíguos")}
      </p>
      <ItemTable items={items} />
    </>
  );
}

function ItemTable({ items, hideInternal = false }: { items: NfeMappedItem[]; hideInternal?: boolean }) {
  if (items.length === 0) return null;
  return (
    <div className="lnf-table-wrap">
      <table className="lnf-table lnf-nfe-items">
        <thead>
          <tr>
            <th>Item</th>
            <th>Código fornecedor</th>
            <th>Descrição fornecedor</th>
            <th aria-hidden="true" />
            <th>Código Delpi</th>
            <th>Descrição Delpi</th>
            <th>Qtd</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <ItemRow key={`${item.itemNumber ?? index}-${item.supplierProductCode ?? ""}`} item={item} hideInternal={hideInternal} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ItemRow({ item, hideInternal }: { item: NfeMappedItem; hideInternal: boolean }) {
  const status = hideInternal ? null : item.mappingStatus;
  const internalCode = status === "mapped" ? item.internalProductCode || "—" : "—";
  const internalDescription =
    status === "mapped"
      ? item.internalProductDescription || "—"
      : status === "unmapped"
        ? "Não relacionado"
        : status === "ambiguous"
          ? "Relação ambígua"
          : "—";
  return (
    <tr data-testid={`nfe-item-${item.itemNumber || item.supplierProductCode || "row"}`}>
      <td>{item.itemNumber || "—"}</td>
      <td>
        <code className="lnf-nfe-code">{item.supplierProductCode || "—"}</code>
      </td>
      <td>{item.supplierProductDescription || "—"}</td>
      <td className="lnf-nfe-arrow" aria-hidden="true">
        →
      </td>
      <td>
        <code className="lnf-nfe-code">{internalCode}</code>
      </td>
      <td>{internalDescription}</td>
      <td>
        {item.quantity || "—"}
        {item.unit ? ` ${item.unit}` : ""}
      </td>
      <td>
        {status ? (
          <span className={`lnf-nfe-status lnf-nfe-status--${status}`}>{STATUS_LABEL[status]}</span>
        ) : (
          "—"
        )}
      </td>
    </tr>
  );
}

function countLabel(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function countSummary(items: NfeMappedItem[]) {
  return {
    items: items.length,
    mapped: items.filter((item) => item.mappingStatus === "mapped").length,
    unmapped: items.filter((item) => item.mappingStatus === "unmapped").length,
    ambiguous: items.filter((item) => item.mappingStatus === "ambiguous").length,
  };
}
