import type { CommercialProposalStatusCategory } from "../types/commercial";

type ProposalStatusBadgeProps = {
  label: string;
  category?: CommercialProposalStatusCategory | null;
  code?: string | null;
};

export function ProposalStatusBadge({
  label,
  category,
  code,
}: ProposalStatusBadgeProps) {
  const variant = category ?? "other";
  const title = code ? `Código TOTVS: ${code}` : undefined;

  return (
    <span
      className={`dc-proposal-status dc-proposal-status--${variant}`}
      title={title}
    >
      {label}
    </span>
  );
}
