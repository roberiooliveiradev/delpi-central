import {
  CalendarRange,
  ClipboardList,
  Landmark,
  Network,
  Settings2,
  Shield,
  Tags,
  Users,
} from "lucide-react";

import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasAdminAccess, hasGuidanceManageAccess, hasScopesManageAccess } from "../../utils/permissions";
import { routeHref } from "../../utils/routing";

export function AdminHomePage() {
  const { profile, loading, error } = usePermissions();

  if (loading) {
    return (
      <PageShell title="Administração" subtitle="Configuração do ciclo orçamentário.">
        <LoadingActivityCard title="Verificando permissões…" variant="panel" />
      </PageShell>
    );
  }

  if (error || !hasAdminAccess(profile)) {
    return (
      <PageShell title="Administração" subtitle="Área restrita a perfis administrativos.">
        <StateBox variant="error" dismissible={false}>
          {error ?? "Você não possui permissão para acessar a administração do planejamento orçamentário."}
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Administração orçamentária"
      subtitle="Gerencie exercícios, orientações institucionais e escopos de acesso."
      icon={<Settings2 size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="home"
    >
      <div className="po-admin-grid">
        <a className="po-admin-card" href={routeHref("admin-exercicios")}>
          <CalendarRange size={24} aria-hidden="true" />
          <div>
            <strong>Exercícios</strong>
            <span className="po-muted">Criar e configurar ciclos anuais</span>
          </div>
        </a>

        {hasGuidanceManageAccess(profile) ? (
          <a className="po-admin-card" href={routeHref("admin-orientacoes")}>
            <ClipboardList size={24} aria-hidden="true" />
            <div>
              <strong>Orientações</strong>
              <span className="po-muted">Editar rascunho e publicar versão</span>
            </div>
          </a>
        ) : null}

        {hasScopesManageAccess(profile) ? (
          <a className="po-admin-card" href={routeHref("admin-centros-de-custo")}>
            <Landmark size={24} aria-hidden="true" />
            <div>
              <strong>Centros de Custo</strong>
              <span className="po-muted">Consultar ERP por filial e cadastrar no planejamento</span>
            </div>
          </a>
        ) : null}

        {hasScopesManageAccess(profile) ? (
          <a className="po-admin-card" href={routeHref("admin-escopos")}>
            <Users size={24} aria-hidden="true" />
            <div>
              <strong>Escopos</strong>
              <span className="po-muted">Vínculos de usuários e centros de custo</span>
            </div>
          </a>
        ) : null}

        {hasScopesManageAccess(profile) ? (
          <a className="po-admin-card" href={routeHref("admin-responsaveis")}>
            <Network size={24} aria-hidden="true" />
            <div>
              <strong>Responsáveis</strong>
              <span className="po-muted">Responsáveis CAPEX por centro de custo</span>
            </div>
          </a>
        ) : null}

        {hasScopesManageAccess(profile) ? (
          <a className="po-admin-card" href={routeHref("admin-categorias-capex")}>
            <Tags size={24} aria-hidden="true" />
            <div>
              <strong>Categorias CAPEX</strong>
              <span className="po-muted">Catálogo de categorias de investimento</span>
            </div>
          </a>
        ) : null}

        <div className="po-admin-card po-admin-card--static">
          <Shield size={24} aria-hidden="true" />
          <div>
            <strong>Auditoria</strong>
            <span className="po-muted">Histórico de transições (em evolução)</span>
          </div>
        </div>
      </div>

      <SectionCard title="Permissões detectadas" hint="Resumo do perfil autenticado no portal.">
        <ul className="po-perm-list">
          {profile?.permissions
            .filter((code) => code.startsWith("planejamento-orcamentario."))
            .map((code) => (
              <li key={code}>{code}</li>
            ))}
        </ul>
      </SectionCard>
    </PageShell>
  );
}
