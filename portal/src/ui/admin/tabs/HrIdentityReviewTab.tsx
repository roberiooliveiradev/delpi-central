import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Link2, RefreshCw, Search } from "lucide-react";
import { createPortal } from "react-dom";

import type {
  AdminUser,
  HrIdentityReview,
  HrIdentityReviewMember,
} from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { Modal } from "../../../components/Modal";
import { Alert, Button, Input, Spinner } from "../../../ui-kit";

import "./HrIdentityReviewTab.css";

type ListFilter = "pending" | "suggested" | "linked" | "all";

const normalizeText = (text: string) =>
  text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Não foi possível carregar os cadastros.";
}

function statusLabel(member: HrIdentityReviewMember): string {
  if (member.verified) return "Vinculado";
  if (member.status === "suggestion_by_name") return "Sugestão disponível";
  if (member.status.startsWith("ambiguous")) return "Revisar nomes";
  if (member.status === "already_assigned_to_other_registration") return "Conta já vinculada";
  return "Sem conta sugerida";
}

export function HrIdentityReviewTab() {
  const api = useAdminApi();
  const [managerRegistration, setManagerRegistration] = useState("20001");
  const [includeIndirect, setIncludeIndirect] = useState(true);
  const [review, setReview] = useState<HrIdentityReview | null>(null);
  const [filter, setFilter] = useState<ListFilter>("pending");
  const [memberSearch, setMemberSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [activeMember, setActiveMember] = useState<HrIdentityReviewMember | null>(null);
  const [accountQuery, setAccountQuery] = useState("");
  const [accounts, setAccounts] = useState<AdminUser[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<AdminUser | null>(null);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const initialLoad = useRef(false);
  const searchSequence = useRef(0);

  // O modal fica no <body>; travar somente a rolagem da página por trás.
  useEffect(() => {
    if (!activeMember) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, [activeMember]);

  const loadTeam = useCallback(async () => {
    const registration = managerRegistration.trim();
    if (!registration) {
      setError("Informe a matrícula do gestor.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHrIdentityReview(registration, includeIndirect);
      setReview(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [api, includeIndirect, managerRegistration]);

  // Carrega a equipe habitual ao entrar na aba. Editar a matrícula não
  // dispara novas consultas até o administrador clicar em Atualizar.
  useEffect(() => {
    if (initialLoad.current) return;
    initialLoad.current = true;
    void loadTeam();
  }, [loadTeam]);

  const members = useMemo(() => {
    const rows = [...(review?.members ?? [])];
    const order = (item: HrIdentityReviewMember) =>
      item.verified ? 3 : item.status === "suggestion_by_name" ? 0 : 1;
    rows.sort((a, b) =>
      order(a) - order(b) ||
      a.fullName.localeCompare(b.fullName, "pt-BR"),
    );
    const needle = normalizeText(memberSearch);
    return rows.filter((item) => {
      if (filter === "pending" && item.verified) return false;
      if (filter === "suggested" && item.status !== "suggestion_by_name") return false;
      if (filter === "linked" && !item.verified) return false;
      return !needle ||
        normalizeText(item.fullName).includes(needle) ||
        item.registration.includes(memberSearch.trim());
    });
  }, [review, filter, memberSearch]);

  const fetchAccounts = async (term: string) => {
    const searchId = ++searchSequence.current;
    setAccountQuery(term);
    setSelectedAccount(null);
    setAccounts([]);
    if (!term.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const response = await api.listUsers({
        q: term.trim(),
        page: 1,
        pageSize: 20,
      });
      if (searchId === searchSequence.current) {
        setAccounts((response.data ?? []).filter((user) => user.active !== false));
      }
    } catch (err) {
      if (searchId === searchSequence.current) setError(errorMessage(err));
    } finally {
      if (searchId === searchSequence.current) setSearching(false);
    }
  };

  const openMember = (member: HrIdentityReviewMember) => {
    if (member.verified) return;
    setActiveMember(member);
    setConfirmOpen(false);
    setError(null);
    setNotice(null);
    // Busca a conta sugerida automaticamente. Não a seleciona sozinho.
    void fetchAccounts(member.fullName);
  };

  const closeMember = () => {
    searchSequence.current += 1;
    setActiveMember(null);
    setAccounts([]);
    setSelectedAccount(null);
    setSearching(false);
    setConfirmOpen(false);
    setError(null);
  };

  const linkAccount = async () => {
    if (!activeMember || !selectedAccount || saving) return;
    setConfirmOpen(false);
    setSaving(true);
    setError(null);
    const registration = activeMember.registration;
    const account = selectedAccount;
    try {
      // Rejeitar conflito antes do PUT; a Core também valida unicidade e
      // existência/atividade das duas pontas e audita a confirmação.
      const current = await api.getHrIdentityMapping(account.id);
      if (current.mapping?.registration === registration) {
        setNotice("Este cadastro já está vinculado. A lista foi atualizada.");
      } else {
        if (current.mapping) {
          throw new Error(
            `Esta conta já pertence à matrícula ${current.mapping.registration}. Nada foi alterado.`,
          );
        }
        await api.confirmHrIdentityMapping(account.id, registration);
        setNotice(`${activeMember.fullName} vinculado à conta ${account.name}.`);
      }
      closeMember();
      // closeMember limpa o erro, mas não o aviso de sucesso.
      await loadTeam();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const suggestedCount = review?.suggestionCount ?? 0;
  const linkedCount = review?.verifiedCount ?? 0;
  const pendingCount = (review?.teamCount ?? 0) - linkedCount;

  return (
    <section className="hr-identity-review">
      <div className="hr-identity-review__heading">
        <div>
          <h2>Vincular cadastros</h2>
          <p>Escolha um colaborador do RH e a conta correspondente na Minha Delpi.</p>
        </div>
      </div>

      <div className="hr-identity-review__toolbar">
        <label htmlFor="hr-manager-registration">Equipe do gestor</label>
        <Input
          id="hr-manager-registration"
          value={managerRegistration}
          onChange={(event) => setManagerRegistration(event.target.value)}
          size="sm"
          aria-label="Matrícula do gestor"
        />
        <label className="hr-identity-review__inline">
          <input
            type="checkbox"
            checked={includeIndirect}
            onChange={(event) => setIncludeIndirect(event.target.checked)}
          />
          Equipe completa
        </label>
        <Button
          variant="secondary"
          disabled={loading}
          onClick={() => void loadTeam()}
          icon={<RefreshCw size={14} />}
        >
          Atualizar
        </Button>
      </div>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}
      {loading ? <Spinner label="Carregando colaboradores…" /> : null}

      {review ? (
        <>
          <div className="hr-identity-review__stats">
            <div><strong>{linkedCount}</strong><span>Vinculados</span></div>
            <div><strong>{pendingCount}</strong><span>Pendentes</span></div>
            <div><strong>{suggestedCount}</strong><span>Com sugestão</span></div>
          </div>
          <div className="hr-identity-review__toolbar hr-identity-review__filters">
            <div className="hr-identity-review__search-field">
              <Search size={15} aria-hidden="true" />
              <Input
                size="sm"
                placeholder="Buscar colaborador ou matrícula"
                aria-label="Buscar colaborador ou matrícula"
                value={memberSearch}
                onChange={(event) => setMemberSearch(event.target.value)}
              />
            </div>
            <label htmlFor="hr-identity-filter" className="hr-identity-review__sr-only">
              Filtrar colaboradores
            </label>
            <select
              id="hr-identity-filter"
              value={filter}
              onChange={(event) => setFilter(event.target.value as ListFilter)}
            >
              <option value="pending">Pendentes</option>
              <option value="suggested">Com sugestão</option>
              <option value="linked">Vinculados</option>
              <option value="all">Todos</option>
            </select>
          </div>
          <div className="hr-identity-review__table-scroll">
            <table className="hr-identity-review__table">
              <thead><tr>
                <th scope="col">Colaborador RH</th>
                <th scope="col">Matrícula</th>
                <th scope="col">Situação</th>
                <th scope="col">Ação</th>
              </tr></thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.registration}>
                    <td>{member.fullName}</td>
                    <td><code>{member.registration}</code></td>
                    <td>{statusLabel(member)}</td>
                    <td>
                      {member.verified ? (
                        <span className="hr-identity-review__verified">
                          <Check size={14} /> Vinculado
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => openMember(member)}
                          icon={<Link2 size={14} />}
                        >
                          Vincular
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {!members.length ? (
                  <tr><td colSpan={4}>Nenhum colaborador encontrado.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </>
      ) : null}

      {activeMember ? createPortal(
        <div
          className="hr-identity-review__modal-root"
          onKeyDown={(event) => {
            if (event.key === "Escape" && !saving) {
              event.preventDefault();
              event.stopPropagation();
              closeMember();
            }
          }}
        >
          <Modal
            open
            title={confirmOpen ? "Confirmar vínculo" : "Vincular cadastro"}
            size="md"
            onClose={() => { if (!saving) closeMember(); }}
            footer={
              <div className="hr-identity-review__actions">
                <Button
                  variant="secondary"
                  disabled={saving}
                  onClick={confirmOpen ? () => setConfirmOpen(false) : closeMember}
                >
                  {confirmOpen ? "Voltar" : "Cancelar"}
                </Button>
                <Button
                  variant="primary"
                  disabled={!selectedAccount || searching || saving}
                  loading={saving}
                  onClick={confirmOpen ? () => void linkAccount() : () => setConfirmOpen(true)}
                  icon={<Link2 size={14} />}
                >
                  {confirmOpen ? "Sim, vincular" : "Vincular conta"}
                </Button>
              </div>
            }
          >
            {confirmOpen ? (
              <div className="hr-identity-review__modal-content">
                <p className="hr-identity-review__helper">
                  Confira se os cadastros abaixo pertencem à mesma pessoa.
                </p>
                <div className="hr-identity-review__confirmation">
                  <div>
                    <span>Colaborador RH</span>
                    <strong>{activeMember.fullName}</strong>
                    <small>Matrícula {activeMember.registration}</small>
                  </div>
                  <div>
                    <span>Conta Minha Delpi</span>
                    <strong>{selectedAccount?.name ?? "Conta não selecionada"}</strong>
                    <small>{selectedAccount?.email ?? ""}</small>
                  </div>
                </div>
              </div>
            ) : (
              <div className="hr-identity-review__modal-content">
                <div className="hr-identity-review__heading">
                  <div>
                    <h3>{activeMember.fullName}</h3>
                    <p>Matrícula RH: <strong>{activeMember.registration}</strong></p>
                  </div>
                </div>
                <p className="hr-identity-review__helper">
                  Selecione a conta da Minha Delpi que pertence a esta pessoa.
                </p>
                <form
                  className="hr-identity-review__toolbar"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void fetchAccounts(accountQuery);
                  }}
                >
                  <Input
                    autoFocus
                    size="sm"
                    placeholder="Buscar conta por nome ou e-mail"
                    aria-label="Buscar conta por nome ou e-mail"
                    value={accountQuery}
                    disabled={saving}
                    onChange={(event) => {
                      searchSequence.current += 1;
                      setAccountQuery(event.target.value);
                      setSelectedAccount(null);
                      setAccounts([]);
                      setSearching(false);
                    }}
                  />
                  <Button
                    type="submit"
                    disabled={searching || saving || !accountQuery.trim()}
                    loading={searching}
                    icon={<Search size={14} />}
                  >
                    Buscar
                  </Button>
                </form>

                {searching ? <Spinner label="Procurando contas…" /> : null}
                {!searching && accounts.length === 0 ? (
                  <p className="hr-identity-review__helper">
                    Nenhuma conta encontrada nesta busca. Tente um nome menor ou e-mail.
                  </p>
                ) : null}
                {!searching && accounts.length > 0 ? (
                  <div
                    className="hr-identity-review__accounts"
                    role="radiogroup"
                    aria-label="Conta da Minha Delpi"
                  >
                    {accounts.map((account) => (
                      <label
                        key={account.id}
                        className={
                          "hr-identity-review__account" +
                          (selectedAccount?.id === account.id ? " hr-identity-review__account--selected" : "")
                        }
                      >
                        <input
                          type="radio"
                          name="hr-selected-core-user"
                          checked={selectedAccount?.id === account.id}
                          onChange={() => setSelectedAccount(account)}
                          disabled={saving}
                        />
                        <span>
                          <strong>{account.name || "Usuário sem nome"}</strong>
                          <small>{account.email}</small>
                        </span>
                        {activeMember.suggestedCoreUserId === account.id ? (
                          <span className="hr-identity-review__tag">Sugerido</span>
                        ) : null}
                      </label>
                    ))}
                    {accounts.length === 20 ? (
                      <p className="hr-identity-review__helper">
                        Mostrando 20 contas. Refine a busca se necessário.
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            )}
          </Modal>
        </div>,
        document.body,
      ) : null}
    </section>
  );
}
