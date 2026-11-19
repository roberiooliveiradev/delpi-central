import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Link2, RefreshCw, Search } from "lucide-react";

import type {
  HrCollaboratorIdentityPreview,
  HrIdentityDirectory,
  HrIdentityDirectoryUser,
} from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { Modal } from "../../../components/Modal";
import { Alert, Button, Input, Spinner } from "../../../ui-kit";

import "./HrIdentityReviewTab.css";

type Filter = "pending" | "linked" | "all";

function errorMessage(err: unknown) {
  return err instanceof Error ? err.message : "Falha ao consultar os cadastros.";
}

const normalize = (text: string) =>
  text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

export function HrIdentityReviewTab() {
  const api = useAdminApi();
  const [directory, setDirectory] = useState<HrIdentityDirectory | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<Filter>("pending");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [account, setAccount] = useState<HrIdentityDirectoryUser | null>(null);
  const [registration, setRegistration] = useState("");
  const [person, setPerson] = useState<HrCollaboratorIdentityPreview | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const lookupSequence = useRef(0);

  const loadDirectory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHrIdentityDirectory();
      if (data.scope !== "all_core_accounts" || !Array.isArray(data.items)) {
        throw new Error("O servidor não retornou o diretório geral.");
      }
      setDirectory(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void loadDirectory();
  }, [loadDirectory]);

  const visible = useMemo(() => {
    const rows = (directory?.items ?? []).filter((item) => {
      if (filter === "pending" && (item.registration || !item.active)) return false;
      if (filter === "linked" && !item.registration) return false;
      const needle = normalize(search);
      return !needle ||
        normalize(item.name).includes(needle) ||
        normalize(item.email).includes(needle) ||
        normalize(item.registration ?? "").includes(needle);
    });
    return rows.sort((a, b) =>
      Number(Boolean(a.registration)) - Number(Boolean(b.registration)) ||
      a.name.localeCompare(b.name, "pt-BR")
    );
  }, [directory, filter, search]);

  const openAccount = (item: HrIdentityDirectoryUser) => {
    if (!item.active || item.registration) return;
    lookupSequence.current += 1;
    setAccount(item);
    setRegistration("");
    setPerson(null);
    setModalError(null);
    setConfirmOpen(false);
  };

  const closeAccount = () => {
    if (saving) return;
    lookupSequence.current += 1;
    setAccount(null);
    setPerson(null);
    setRegistration("");
    setModalError(null);
    setConfirmOpen(false);
  };

  const verifyRegistration = async () => {
    const value = registration.trim();
    if (!value) {
      setModalError("Informe a matrícula exata da pessoa no Portal RH.");
      return;
    }
    const seq = ++lookupSequence.current;
    setPerson(null);
    setModalError(null);
    setLookupLoading(true);
    try {
      const result = await api.getHrCollaboratorIdentityPreview(value);
      if (seq !== lookupSequence.current) return;
      if (result.registration !== value) {
        throw new Error("A matrícula retornada pelo RH não corresponde à informada.");
      }
      if (!result.active) {
        throw new Error("Esta matrícula está inativa no Portal RH.");
      }
      setPerson(result);
    } catch (err) {
      if (seq === lookupSequence.current) setModalError(errorMessage(err));
    } finally {
      if (seq === lookupSequence.current) setLookupLoading(false);
    }
  };

  const saveMapping = async () => {
    if (
      saving || !account?.active || account.registration ||
      !person?.active || person.registration !== registration.trim()
    ) return;
    setConfirmOpen(false);
    setSaving(true);
    setModalError(null);
    try {
      const current = await api.getHrIdentityMapping(account.userId);
      if (current.mapping?.registration === person.registration) {
        setNotice("Vínculo já existente e confirmado.");
      } else {
        if (current.mapping) {
          throw new Error(
            `Esta conta já está associada à matrícula ${current.mapping.registration}. Nenhuma alteração efetuada.`
          );
        }
        await api.confirmHrIdentityMapping(account.userId, person.registration);
        setNotice(
          `Vínculo confirmado: ${account.name} ↔ ${person.fullName} (${person.registration}).`
        );
      }
      lookupSequence.current += 1;
      setAccount(null);
      setPerson(null);
      setRegistration("");
      setModalError(null);
      setConfirmOpen(false);
      await loadDirectory();
    } catch (err) {
      setModalError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const total = directory?.total ?? 0;
  const linked = directory?.linked ?? 0;
  const pendingActive = (directory?.items ?? []).filter(
    (item) => item.active && !item.registration
  ).length;

  return (
    <section className="hr-identity-directory">
      <header className="hr-identity-directory__heading">
        <div>
          <h2>Vincular cadastros RH ↔ Minha Delpi</h2>
          <p>
            Todas as contas da Minha Delpi, sem filtro por gestor ou hierarquia.
            Escolha uma conta e informe a matrícula oficial para confirmar a identidade.
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          icon={<RefreshCw size={15} />}
          disabled={loading}
          onClick={() => void loadDirectory()}
        >
          Atualizar
        </Button>
      </header>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}
      {loading && !directory ? <Spinner label="Carregando contas da Minha Delpi…" /> : null}

      {directory ? (
        <>
          <div className="hr-identity-directory__stats">
            <div><strong>{total}</strong><span>Contas no diretório</span></div>
            <div><strong>{linked}</strong><span>Com matrícula vinculada</span></div>
            <div><strong>{pendingActive}</strong><span>Ativas pendentes</span></div>
          </div>

          <div className="hr-identity-directory__toolbar">
            <label className="hr-identity-directory__search">
              <Search size={16} aria-hidden="true" />
              <Input
                size="sm"
                aria-label="Buscar conta ou matrícula"
                placeholder="Buscar nome, e-mail ou matrícula vinculada"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
            <label htmlFor="hr-identity-directory-filter">Situação</label>
            <select
              id="hr-identity-directory-filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value as Filter)}
            >
              <option value="pending">Ativas pendentes</option>
              <option value="linked">Vinculadas</option>
              <option value="all">Todas as contas</option>
            </select>
          </div>

          <div className="hr-identity-directory__scroll">
            <table className="hr-identity-directory__table">
              <thead>
                <tr>
                  <th scope="col">Conta Minha Delpi</th>
                  <th scope="col">Matrícula RH</th>
                  <th scope="col">Situação</th>
                  <th scope="col">Ação</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.userId}>
                    <td>
                      <strong>{item.name || "Usuário sem nome"}</strong>
                      <small>{item.email}</small>
                    </td>
                    <td>{item.registration ? <code>{item.registration}</code> : "Não vinculada"}</td>
                    <td>
                      {item.registration ? (
                        <span className="hr-identity-directory__linked">
                          <Check size={14} /> Vinculada
                        </span>
                      ) : item.active ? "Pendente" : "Conta inativa"}
                    </td>
                    <td>
                      {!item.registration && item.active ? (
                        <Button
                          size="sm"
                          variant="primary"
                          icon={<Link2 size={14} />}
                          onClick={() => openAccount(item)}
                        >
                          Vincular
                        </Button>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
                {!visible.length ? (
                  <tr><td colSpan={4}>Nenhuma conta encontrada neste filtro.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
          <p className="hr-identity-directory__hint">
            Esta tela lista contas Core. A matrícula é validada diretamente no Portal RH,
            inclusive para pessoas no topo da estrutura. Vínculos existentes são preservados;
            nomes iguais nunca geram associação automática.
          </p>
        </>
      ) : null}

      <Modal
        open={Boolean(account)}
        size="md"
        onClose={closeAccount}
        title="Confirmar identidade RH"
        footer={
          <div className="hr-identity-directory__footer">
            <Button variant="secondary" onClick={closeAccount} disabled={saving}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              icon={<Link2 size={14} />}
              disabled={!person || lookupLoading || saving}
              loading={saving}
              onClick={() => setConfirmOpen(true)}
            >
              Vincular conta
            </Button>
          </div>
        }
      >
        {account ? (
          <div className="hr-identity-directory__form">
            <p className="hr-identity-directory__account">
              <strong>{account.name}</strong>
              <span>{account.email}</span>
            </p>
            <p>Informe a matrícula exata desta pessoa no Portal RH.</p>
            <form
              className="hr-identity-directory__lookup"
              onSubmit={(event) => {
                event.preventDefault();
                void verifyRegistration();
              }}
            >
              <Input
                size="sm"
                value={registration}
                aria-label="Matrícula RH"
                placeholder="Ex.: 10257 ou PJ - 004"
                disabled={saving}
                onChange={(event) => {
                  lookupSequence.current += 1;
                  setRegistration(event.target.value);
                  setPerson(null);
                  setModalError(null);
                  setLookupLoading(false);
                }}
              />
              <Button
                type="submit"
                variant="secondary"
                disabled={!registration.trim() || lookupLoading || saving}
                loading={lookupLoading}
              >
                Consultar RH
              </Button>
            </form>
            {modalError ? <Alert tone="danger">{modalError}</Alert> : null}
            {person ? (
              <div className="hr-identity-directory__preview">
                <strong>Cadastro oficial encontrado</strong>
                <span>{person.fullName}</span>
                <span>Matrícula {person.registration} · Filial {person.branchCode}</span>
                <span>Situação RH: ativo</span>
              </div>
            ) : null}
          </div>
        ) : null}
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title="Vincular estes dois cadastros?"
        message={
          `Minha Delpi: ${account?.name ?? ""} (${account?.email ?? ""}). ` +
          `Portal RH: ${person?.fullName ?? ""} (matrícula ${person?.registration ?? ""}). ` +
          "Confirme apenas se verificou que pertencem à mesma pessoa. Esta ação será auditada."
        }
        confirmText="Sim, vincular"
        danger={false}
        loading={saving}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void saveMapping()}
      />
    </section>
  );
}
