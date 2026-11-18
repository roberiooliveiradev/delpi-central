import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, Search, RefreshCw } from "lucide-react";

import type {
  AdminUser,
  HrIdentityReview,
  HrIdentityReviewMember,
  HrIdentityReviewStatus,
} from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { Alert, Button, Input, Spinner } from "../../../ui-kit";

import "./HrIdentityReviewTab.css";

const labels: Record<HrIdentityReviewStatus, string> = {
  verified_mapping: "Vínculo verificado",
  suggestion_by_name: "Sugestão por nome",
  ambiguous_rh_name: "Nome duplicado no RH",
  ambiguous_core_name: "Nome duplicado na Minha Delpi",
  already_assigned_to_other_registration: "Conta já associada",
  no_exact_name_suggestion: "Sem sugestão por nome",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Erro ao consultar identidades.";
}

export function HrIdentityReviewTab() {
  const api = useAdminApi();
  const [managerRegistration, setManagerRegistration] = useState("20001");
  const [includeIndirect, setIncludeIndirect] = useState(true);
  const [review, setReview] = useState<HrIdentityReview | null>(null);
  const [filter, setFilter] = useState<"all" | HrIdentityReviewStatus>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [activeMember, setActiveMember] = useState<HrIdentityReviewMember | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [confirmedEvidence, setConfirmedEvidence] = useState(false);
  const [typedRegistration, setTypedRegistration] = useState("");
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const registration = managerRegistration.trim();
    if (!registration) {
      setError("Informe a matrícula do gestor.");
      return;
    }
    setLoading(true);
    setError(null);
    setReview(null);
    try {
      const data = await api.getHrIdentityReview(registration, includeIndirect);
      setReview(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [api, includeIndirect, managerRegistration]);

  const visibleMembers = useMemo(
    () => (review?.members ?? []).filter((member) =>
      filter === "all" || member.status === filter,
    ),
    [review, filter],
  );

  const openReview = (member: HrIdentityReviewMember) => {
    if (member.verified) return;
    setActiveMember(member);
    setSelectedId(null);
    setSelectedUser(null);
    setUsers([]);
    setSearchTerm("");
    setConfirmedEvidence(false);
    setTypedRegistration("");
    setNotice(null);
    setError(null);
  };

  const searchUsers = async () => {
    if (!searchTerm.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const found = await api.listUsers({
        q: searchTerm.trim(),
        page: 1,
        pageSize: 20,
      });
      setUsers((found.data ?? []).filter((user) => user.active !== false));
    } catch (err) {
      setError(errorMessage(err));
      setUsers([]);
    } finally {
      setSearching(false);
    }
  };

  const chooseUser = (user: AdminUser) => {
    setSelectedId(user.id);
    setSelectedUser(user);
    setConfirmedEvidence(false);
    setTypedRegistration("");
    setConfirmationOpen(false);
  };

  const chooseWeakSuggestion = () => {
    const uuid = activeMember?.suggestedCoreUserId;
    if (!uuid) return;
    setSelectedId(uuid);
    setSelectedUser(null);
    setConfirmedEvidence(false);
    setTypedRegistration("");
  };

  const canConfirm = !!activeMember &&
    !!selectedId &&
    !activeMember.verified &&
    confirmedEvidence &&
    typedRegistration === activeMember.registration &&
    !saving;

  const confirmIndividualBinding = async () => {
    if (!canConfirm || !activeMember || !selectedId) return;
    setSaving(true);
    setError(null);
    setConfirmationOpen(false);
    try {
      // Do not silently reassign a Core account to a different registration.
      const existing = await api.getHrIdentityMapping(selectedId);
      if (existing.mapping && existing.mapping.registration !== activeMember.registration) {
        throw new Error(
          "Esta conta já está associada à matrícula " + existing.mapping.registration +
          ". Investigue o vínculo antes de continuar.",
        );
      }
      if (existing.mapping?.registration === activeMember.registration) {
        throw new Error("Esse vínculo já existe. Atualize a consulta para conferir.");
      }

      const registered = activeMember.registration;
      await api.confirmHrIdentityMapping(selectedId, registered);
      setActiveMember(null);
      setSelectedId(null);
      setSelectedUser(null);
      setConfirmedEvidence(false);
      setTypedRegistration("");
      setNotice("Associação da matrícula " + registered + " registrada com auditoria.");
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="hr-identity-review">
      <div className="hr-identity-review__heading">
        <div>
          <h2>Identidades RH</h2>
          <p>
            GLPI #887. Conferência administrativa de matrículas RH e contas da Minha Delpi.
            Sugestões por nome não são confirmação de identidade.
          </p>
        </div>
      </div>

      <div className="hr-identity-review__toolbar">
        <label htmlFor="hr-manager-registration">Matrícula do gestor</label>
        <Input
          id="hr-manager-registration"
          value={managerRegistration}
          onChange={(event) => setManagerRegistration(event.target.value)}
          placeholder="Ex.: 20001"
          size="sm"
        />
        <label className="hr-identity-review__inline">
          <input
            type="checkbox"
            checked={includeIndirect}
            onChange={(event) => setIncludeIndirect(event.target.checked)}
          />
          Incluir subordinados indiretos
        </label>
        <Button onClick={() => void load()} disabled={loading} icon={<RefreshCw size={14} />}>
          Consultar equipe
        </Button>
      </div>

      {loading ? <Spinner label="Consultando hierarquia e identidades…" /> : null}
      {error ? <Alert tone="danger">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}

      {review ? (
        <>
          <div className="hr-identity-review__stats" aria-label="Contagens da equipe">
            <div><strong>{review.teamCount}</strong><span>Colaboradores</span></div>
            <div><strong>{review.verifiedCount}</strong><span>Verificados</span></div>
            <div><strong>{review.suggestionCount}</strong><span>Sugestões para revisar</span></div>
            <div><strong>{review.statusCounts.no_exact_name_suggestion}</strong><span>Sem sugestão</span></div>
          </div>

          <Alert tone="warning">
            {review.warning} A ausência de sugestão não significa ausência de conta.
            Não faça associações em lote nem use somente nome ou e-mail como prova.
          </Alert>

          <div className="hr-identity-review__toolbar">
            <label htmlFor="hr-identity-filter">Situação</label>
            <select
              id="hr-identity-filter"
              value={filter}
              onChange={(event) =>
                setFilter(event.target.value as "all" | HrIdentityReviewStatus)
              }
            >
              <option value="all">Todas</option>
              {Object.entries(labels).map(([value, label]) => (
                <option value={value} key={value}>{label}</option>
              ))}
            </select>
          </div>
          <div className="hr-identity-review__table-scroll">
            <table className="hr-identity-review__table">
              <thead>
                <tr>
                  <th scope="col">Matrícula</th>
                  <th scope="col">Colaborador RH</th>
                  <th scope="col">Filial</th>
                  <th scope="col">Situação</th>
                  <th scope="col">Ação</th>
                </tr>
              </thead>
              <tbody>
                {visibleMembers.map((member) => (
                  <tr key={member.registration}>
                    <td><code>{member.registration}</code></td>
                    <td>{member.fullName}</td>
                    <td>{member.branchCode}</td>
                    <td>{labels[member.status]}</td>
                    <td>
                      {member.verified ? (
                        <span className="hr-identity-review__verified">
                          <ShieldCheck size={14} /> Verificado
                        </span>
                      ) : (
                        <Button size="sm" onClick={() => openReview(member)}>
                          Conferir
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {!visibleMembers.length ? (
                  <tr><td colSpan={5}>Nenhum colaborador neste filtro.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </>
      ) : null}

      {activeMember ? (
        <section className="hr-identity-review__panel" aria-label="Revisão individual">
          <div className="hr-identity-review__heading">
            <div>
              <h3>Conferência individual</h3>
              <p>
                <strong>{activeMember.fullName}</strong> | matrícula{" "}
                <code>{activeMember.registration}</code> | filial {activeMember.branchCode}
              </p>
            </div>
            <Button variant="ghost" onClick={() => setActiveMember(null)} disabled={saving}>
              Fechar
            </Button>
          </div>

          {activeMember.suggestedCoreUserId ? (
            <div className="hr-identity-review__hint">
              <p>
                Há uma sugestão fraca por igualdade de nome:
                {" "}<code>{activeMember.suggestedCoreUserId}</code>.
                Consulte o cadastro e evidências oficiais antes de confirmar.
              </p>
              <Button
                size="sm"
                variant="secondary"
                onClick={chooseWeakSuggestion}
                disabled={saving}
              >
                Selecionar sugestão para conferência
              </Button>
            </div>
          ) : null}

          <div className="hr-identity-review__toolbar">
            <label htmlFor="hr-core-search">Buscar conta Core</label>
            <Input
              id="hr-core-search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Nome ou e-mail corporativo"
              disabled={saving}
              size="sm"
            />
            <Button
              onClick={() => void searchUsers()}
              disabled={searching || saving || !searchTerm.trim()}
              loading={searching}
              icon={<Search size={14} />}
            >
              Buscar
            </Button>
          </div>

          {users.length ? (
            <ul className="hr-identity-review__results">
              {users.map((user) => (
                <li key={user.id}>
                  <span>{user.name || "Sem nome"} | {user.email}</span>
                  <Button size="sm" onClick={() => chooseUser(user)} disabled={saving}>
                    Selecionar
                  </Button>
                </li>
              ))}
            </ul>
          ) : null}

          {selectedId ? (
            <div className="hr-identity-review__verification">
              <p><strong>Conta selecionada:</strong> {selectedUser?.name || "Sugestão por nome"}</p>
              <p><code>{selectedId}</code></p>
              <Link to={"/admin/users/" + encodeURIComponent(selectedId)} target="_blank" rel="noreferrer">
                Abrir cadastro completo da conta
              </Link>
              <label className="hr-identity-review__inline">
                <input
                  type="checkbox"
                  checked={confirmedEvidence}
                  onChange={(event) => setConfirmedEvidence(event.target.checked)}
                />
                Conferi a identidade do titular em fonte oficial, além de nome/e-mail.
              </label>
              <label htmlFor="hr-confirm-registration">
                Digite a matrícula exata para confirmar
              </label>
              <Input
                id="hr-confirm-registration"
                size="sm"
                value={typedRegistration}
                onChange={(event) => setTypedRegistration(event.target.value)}
                placeholder={activeMember.registration}
                disabled={saving}
                autoComplete="off"
              />
              <Button
                variant="primary"
                disabled={!canConfirm}
                loading={saving}
                onClick={() => setConfirmationOpen(true)}
              >
                Confirmar associação individual
              </Button>
            </div>
          ) : null}
        </section>
      ) : null}

      <ConfirmDialog
        open={confirmationOpen}
        title="Confirmar vínculo de identidade"
        message={
          "Você confirma, após conferência independente dos cadastros oficiais, " +
          "que a matrícula " + (activeMember?.registration || "") +
          " pertence à conta Core " + (selectedId || "") +
          "? A associação será gravada e auditada individualmente."
        }
        confirmText="Confirmar vínculo"
        danger={false}
        loading={saving}
        onCancel={() => setConfirmationOpen(false)}
        onConfirm={() => void confirmIndividualBinding()}
      />
    </section>
  );
}
