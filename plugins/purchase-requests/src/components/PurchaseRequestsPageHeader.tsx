import { CalendarDays, MapPin, ShoppingCart } from "lucide-react";
import { PageHeader, pageHeaderHeroBemClasses } from "@delpi/plugin-ui/index";

import { formatDatePtBr } from "../utils/formatters";

type PurchaseRequestsPageHeaderProps = {
  branchLabel: string;
  branchCode: string;
  dateFrom: string;
  dateTo: string;
  onRefresh: () => void;
  refreshing?: boolean;
};

const HEADER_CLASS_NAMES = pageHeaderHeroBemClasses("pr");
const HEADER_LABELS = { refresh: "Atualizar", refreshing: "Atualizando…" };

export function PurchaseRequestsPageHeader({
  branchLabel,
  branchCode,
  dateFrom,
  dateTo,
  onRefresh,
  refreshing = false,
}: PurchaseRequestsPageHeaderProps) {
  const periodLabel =
    dateFrom && dateTo
      ? `${formatDatePtBr(dateFrom)} — ${formatDatePtBr(dateTo)}`
      : "Período não definido";

  return (
    <PageHeader
      layout="hero"
      classNames={HEADER_CLASS_NAMES}
      labels={HEADER_LABELS}
      icon={<ShoppingCart size={28} strokeWidth={1.75} />}
      eyebrow={`${branchLabel} · Suprimentos`}
      title="Solicitações de Compras"
      subtitle="Acompanhe solicitações, pedidos de compra e recebimentos em um único lugar."
      onRefresh={onRefresh}
      refreshing={refreshing}
      metaItems={[
        { icon: <MapPin size={15} aria-hidden />, label: `Filial ${branchCode}` },
        { icon: <CalendarDays size={15} aria-hidden />, label: periodLabel },
      ]}
    />
  );
}
