import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAvatar } from "../../customers/components/CustomerAvatar";

export type OtdCustomerIdentity = {
  code?: string | null;
  store?: string | null;
  name?: string | null;
  shortName?: string | null;
  hasAvatar?: boolean;
};

type OtdCustomerIdentityCellProps = {
  customer: OtdCustomerIdentity;
  size?: "sm" | "md";
  /** Subtítulo extra (ex.: pedido) acima do código/loja. */
  eyebrow?: string;
};

/**
 * Avatar + nome + código/loja — mesmo padrão da Minha Carteira.
 */
export function OtdCustomerIdentityCell({
  customer,
  size = "sm",
  eyebrow,
}: OtdCustomerIdentityCellProps) {
  const code = (customer.code ?? "").trim();
  const store = (customer.store ?? "").trim() || "01";
  const name =
    (customer.name ?? "").trim() ||
    (customer.shortName ?? "").trim() ||
    code ||
    "—";
  const codeStore =
    code && store
      ? formatEntityCodeStore(code, store) ?? `${code} · Loja ${store}`
      : code || "—";

  return (
    <div className="cm-open-orders-client">
      {code ? (
        <CustomerAvatar
          code={code}
          store={store}
          name={name}
          hasAvatar={Boolean(customer.hasAvatar)}
          size={size}
          previewable={false}
        />
      ) : (
        <span className="cm-open-orders-client__avatar-spacer" aria-hidden="true" />
      )}
      <div className="cm-open-orders-client__text">
        {eyebrow ? <span className="cm-otd-customer-eyebrow">{eyebrow}</span> : null}
        <strong className="cm-open-orders-client__name">{name}</strong>
        <span className="cm-open-orders-client__id">{codeStore}</span>
      </div>
    </div>
  );
}
