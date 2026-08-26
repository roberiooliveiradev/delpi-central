import { useCallback, useEffect, useState } from "react";

import type { AdminUser } from "../../../data/adminApi";
import type {
  ProtheusUserMatch,
  UserProtheusMapping,
} from "../../../data/purchaseRequestsRbacApi";
import { usePurchaseRequestsRbacApi } from "../../../hooks/usePurchaseRequestsRbacApi";
import { Alert, Button, Spinner } from "../../../ui-kit";

type UserTotvsTabProps = {
  user: AdminUser;
  active: boolean;
};

function formatMappingSource(source: string | null | undefined): string {
  if (source === "email_match" || source === "email_sync") {
    return "Sincronização por e-mail (USR_EMAIL)";
  }
  if (source === "manual") return "Manual (admin SC)";
  return source?.trim() || "—";
}

export function UserTotvsTab({ user, active }: UserTotvsTabProps) {
  const api = usePurchaseRequestsRbacApi();
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [mapping, setMapping] = useState<UserProtheusMapping | null>(null);
  const [protheusUser, setProtheusUser] = useState<ProtheusUserMatch | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const row = await api.getUserProtheusMapping(user.id);
      setMapping(row);
      if (row?.protheus_user_id) {
        setProtheusUser({
          protheus_user_id: row.protheus_user_id,
          code: row.protheus_user_code,
          name: null,
          email: user.email,
        });
      } else {
        setProtheusUser(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível carregar a associação Protheus.",
      );
      setMapping(null);
      setProtheusUser(null);
    } finally {
      setLoading(false);
    }
  }, [api, user.id, user.email]);

  useEffect(() => {
    if (!active) return;
    void load();
  }, [active, load]);

  const syncByEmail = async () => {
    setSyncing(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await api.syncUserProtheusMappingByEmail(
        user.id,
        user.email,
        user.name,
      );
      setMapping(result.mapping);
      setProtheusUser(result.protheus_user);
      setSuccess(
        `Associado ao usuário Protheus ${result.protheus_user.name || result.protheus_user.protheus_user_id} (${result.synced_by_email}).`,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível sincronizar com o Protheus.",
      );
    } finally {
      setSyncing(false);
    }
  };

  if (!active) return null;

  return (
    <div className="user-rbac-totvs">
      <section className="user-rbac-panel">
        <div className="user-rbac-panel-header">
          <div>
            <h4>TOTVS / Protheus</h4>
            <p>
              Vincula o usuário do portal ao cadastro em <code>SYS_USR</code>, comparando o
              e-mail do portal com <code>USR_EMAIL</code> no Protheus.
            </p>
          </div>
          <div className="user-rbac-panel-actions">
            <Button variant="secondary" onClick={() => void load()} disabled={loading || syncing}>
              Atualizar
            </Button>
            <Button
              variant="primary"
              onClick={() => void syncByEmail()}
              disabled={loading || syncing || !user.email?.trim()}
              loading={syncing}
            >
              Sincronizar por e-mail
            </Button>
          </div>
        </div>

        {loading ? <Spinner label="Carregando associação…" /> : null}

        {error ? <Alert tone="danger">{error}</Alert> : null}
        {success ? <Alert tone="success">{success}</Alert> : null}

        {!loading ? (
          <dl className="user-rbac-totvs-grid">
            <div>
              <dt>E-mail do portal</dt>
              <dd>{user.email}</dd>
            </div>
            <div>
              <dt>USR_ID (Protheus)</dt>
              <dd>
                {mapping?.protheus_user_id || protheusUser?.protheus_user_id || "—"}
              </dd>
            </div>
            <div>
              <dt>USR_CODIGO</dt>
              <dd>{mapping?.protheus_user_code || protheusUser?.code || "—"}</dd>
            </div>
            <div>
              <dt>Nome (SYS_USR)</dt>
              <dd>{protheusUser?.name || "—"}</dd>
            </div>
            <div>
              <dt>Origem do vínculo</dt>
              <dd>{formatMappingSource(mapping?.mapping_source)}</dd>
            </div>
            <div>
              <dt>Verificado</dt>
              <dd>{mapping?.verified ? "Sim" : "Não"}</dd>
            </div>
          </dl>
        ) : null}
      </section>

      <section className="user-rbac-panel user-rbac-totvs-hint">
        <p>
          Esta associação é usada pelo módulo <strong>Solicitações de Compras</strong> para
          identificar o solicitante no TOTVS. Se não houver <code>USR_EMAIL</code> igual ao
          e-mail do portal, o vínculo não será criado automaticamente.
        </p>
      </section>
    </div>
  );
}
