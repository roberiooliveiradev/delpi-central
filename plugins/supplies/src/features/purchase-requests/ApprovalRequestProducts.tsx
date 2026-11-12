import type { ApprovalRequestProduct } from "./approvalLeadTimeApi";

function ProductEntry({ product }: { product: ApprovalRequestProduct }) {
  const code = product.product_code || "Código não informado";
  const description = product.product_description || "Descrição não informada";
  return (
    <div className="sp-approval-lead-time__product-entry">
      <span className="sp-approval-lead-time__product-code">{code}</span>
      <span className="sp-approval-lead-time__product-description" title={description}>
        {description}
      </span>
      {product.line_count > 1 ? (
        <span className="sp-approval-lead-time__product-count">
          {product.line_count} itens da SC
        </span>
      ) : null}
    </div>
  );
}

/** Reusable compact SC product listing for pending and confirmed history. */
export function ApprovalRequestProducts({ products }: { products: ApprovalRequestProduct[] }) {
  if (!products?.length) return <span>Produto não informado</span>;
  const [first, ...others] = products;
  return (
    <div className="sp-approval-lead-time__products">
      <ProductEntry product={first} />
      {others.length > 0 ? (
        <details className="sp-approval-lead-time__products-more">
          <summary>
            Ver mais {others.length} {others.length === 1 ? "produto" : "produtos"}
          </summary>
          <div className="sp-approval-lead-time__products-expanded">
            {others.map((product, index) => (
              <ProductEntry
                key={`${product.product_code}:${product.product_description || ""}:${index}`}
                product={product}
              />
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
