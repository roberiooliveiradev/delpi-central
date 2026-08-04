import type { CustomerDetailSection } from "../utils/customerDetailSection";
import { CUSTOMER_DETAIL_SECTION_ORDER } from "../utils/customerDetailSection";

type CustomerDetailSectionsProps = {
  section: CustomerDetailSection;
  onChange: (section: CustomerDetailSection) => void;
  openOrdersCount?: number;
};

const LABELS: Record<CustomerDetailSection, string> = {
  resumo: "Visão geral",
  pedidos: "Pedidos em aberto",
  historico: "Histórico de vendas",
  oportunidades: "Oportunidades",
  contatos: "Contatos",
};

export function CustomerDetailSections({
  section,
  onChange,
  openOrdersCount = 0,
}: CustomerDetailSectionsProps) {
  return (
    <nav className="pva-checkup-sections" aria-label="Seções do cliente">
      <div className="pva-checkup-sections__list" role="tablist" aria-orientation="horizontal">
        {CUSTOMER_DETAIL_SECTION_ORDER.map((id) => {
          const active = section === id;
          const label = LABELS[id];
          const showBadge = id === "pedidos" && openOrdersCount > 0;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              id={`pva-customer-tab-${id}`}
              className={
                active
                  ? "pva-checkup-sections__tab pva-checkup-sections__tab--active"
                  : "pva-checkup-sections__tab"
              }
              aria-selected={active}
              tabIndex={active ? 0 : -1}
              onClick={() => onChange(id)}
              onKeyDown={(event) => {
                if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
                event.preventDefault();
                const index = CUSTOMER_DETAIL_SECTION_ORDER.indexOf(id);
                const delta = event.key === "ArrowRight" ? 1 : -1;
                const next =
                  CUSTOMER_DETAIL_SECTION_ORDER[
                    (index + delta + CUSTOMER_DETAIL_SECTION_ORDER.length) %
                      CUSTOMER_DETAIL_SECTION_ORDER.length
                  ];
                if (!next) return;
                onChange(next);
                document.getElementById(`pva-customer-tab-${next}`)?.focus();
              }}
            >
              <span className="pva-checkup-sections__tab-label">{label}</span>
              {showBadge ? (
                <span className="pva-checkup-sections__badge" aria-label={`${openOrdersCount} pedidos`}>
                  {openOrdersCount}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
