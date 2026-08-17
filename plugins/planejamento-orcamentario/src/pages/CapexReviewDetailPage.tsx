import { ClipboardCheck } from "lucide-react";

import { CapexApprovalWorkspace } from "../components/CapexApprovalWorkspace";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import { hasCapexApproveAccess } from "../utils/permissions";
import { capexApprovalsHref, resolveCapexPlanId } from "../utils/routing";

type CapexReviewDetailPageProps = {
  planId?: string | null;
  pathname?: string;
};

export function CapexReviewDetailPage({ planId, pathname }: CapexReviewDetailPageProps) {
  const resolvedId = planId ?? resolveCapexPlanId(pathname);
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasCapexApproveAccess(profile);

  if (permLoading) {
    return (
      <PageShell
        title="Análise CAPEX"
        subtitle="Decida investimento a investimento. Abra os detalhes para ver observações e anexos."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backHref={capexApprovalsHref()}
      >
        <LoadingActivityCard title="Carregando planejamento…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Acesso negado (403). Sem permissão de aprovação CAPEX.
        </StateBox>
      </PageShell>
    );
  }

  if (!resolvedId) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Identificador do planejamento ausente na URL.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Análise CAPEX"
      subtitle="Decida cada investimento. Abra os detalhes para ver observações, justificativa e anexos."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backHref={capexApprovalsHref()}
    >
      <CapexApprovalWorkspace planId={resolvedId} />
    </PageShell>
  );
}
