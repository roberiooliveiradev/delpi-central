import { ClipboardCheck } from "lucide-react";

import { PersonnelApprovalWorkspace } from "../components/PersonnelApprovalWorkspace";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import { hasPersonnelApproveAccess } from "../utils/permissions";
import { pessoalApprovalsHref, resolvePersonnelPlanId } from "../utils/routing";

type PersonnelReviewDetailPageProps = {
  planId?: string | null;
  pathname?: string;
};

export function PersonnelReviewDetailPage({
  planId,
  pathname,
}: PersonnelReviewDetailPageProps) {
  const resolvedId = planId ?? resolvePersonnelPlanId(pathname);
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasPersonnelApproveAccess(profile);

  if (permLoading) {
    return (
      <PageShell
        title="Análise de Pessoal"
        subtitle="Revisão somente leitura do orçamento."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backHref={pessoalApprovalsHref()}
      >
        <LoadingActivityCard title="Carregando orçamento…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Acesso negado (403). Sem permissão de aprovação de Pessoal.
        </StateBox>
      </PageShell>
    );
  }

  if (!resolvedId) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Identificador do planejamento ausente na URL.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Análise de Pessoal"
      subtitle="Somente leitura — decisões sobre o conjunto do centro de custo."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backHref={pessoalApprovalsHref()}
    >
      <PersonnelApprovalWorkspace planId={resolvedId} />
    </PageShell>
  );
}
