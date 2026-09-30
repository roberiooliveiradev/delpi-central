import {
  ConfirmModalPanel,
  EmptyState,
  FloatingNoticeStack,
  LoadingState,
  ModalShell,
  confirmModalBemClasses,
  emptyStatePanelBemClasses,
  floatingNoticeStackBemClasses,
  loadingStatePanelBemClasses,
  modalShellBemClasses,
  useFloatingNotices,
} from "@delpi/plugin-ui/index";
import { ChevronLeft, Pencil, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";

import {
  createDowntimeReason,
  setDowntimeReasonActive,
  updateDowntimeReason,
  type CreateDowntimeReasonInput,
  type DowntimeReason,
  type UpdateDowntimeReasonInput,
} from "../api/downtimeReasonsApi";
import { DelpiMesRequestError } from "../api/httpClient";
import { DowntimeReasonForm } from "../components/registrations/DowntimeReasonForm";
import { DELPI_MES_COPY } from "../content/copy";
import { useDowntimeReasons } from "../hooks/useDowntimeReasons";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const emptyClasses = emptyStatePanelBemClasses("delpi-mes");
const modalClasses = modalShellBemClasses("delpi-mes");
const confirmClasses = confirmModalBemClasses("delpi-mes");
const noticeClasses = floatingNoticeStackBemClasses("delpi-mes");

const BASE_CATEGORIES = [
  "machine",
  "tooling",
  "material",
  "quality",
  "setup",
  "maintenance",
  "people",
  "logistics",
  "planned",
  "other",
];

type StatusFilter = "all" | "active" | "inactive";
type FormModal = { mode: "create" } | { mode: "edit"; reason: DowntimeReason };

function describeApiError(error: unknown): string {
  if (error instanceof DelpiMesRequestError) {
    if (error.status === 401) return "Sua sessão expirou. Entre novamente para continuar.";
    if (error.status === 403) return "Seu perfil não possui permissão para gerenciar motivos de parada.";
    if (error.status === 404) return "Este motivo não existe mais. A lista foi atualizada.";
    if (error.message) return error.message;
  }
  return "Não foi possível concluir a operação. Tente novamente.";
}

export function DowntimeReasonsPage({ onBack }: { onBack: () => void }) {
  const copy = DELPI_MES_COPY.registrations;
  const { items, loading, error, reload, upsert } = useDowntimeReasons();
  const notices = useFloatingNotices();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [modal, setModal] = useState<FormModal | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [pendingDeactivate, setPendingDeactivate] = useState<DowntimeReason | null>(null);
  const [deactivateBusy, setDeactivateBusy] = useState(false);
  const [deactivateError, setDeactivateError] = useState<string | null>(null);
  const [reactivating, setReactivating] = useState<string | null>(null);

  const categorySuggestions = useMemo(() => {
    const all = new Set([...BASE_CATEGORIES, ...items.map((item) => item.category)]);
    return [...all].sort();
  }, [items]);

  const counts = useMemo(
    () => ({
      total: items.length,
      active: items.filter((item) => item.active).length,
      inactive: items.filter((item) => !item.active).length,
    }),
    [items],
  );

  const visible = useMemo(() => {
    const term = search.trim().toLowerCase();
    return items.filter((item) => {
      if (statusFilter === "active" && !item.active) return false;
      if (statusFilter === "inactive" && item.active) return false;
      if (!term) return true;
      return [item.code, item.label, item.category].some((field) =>
        field.toLowerCase().includes(term),
      );
    });
  }, [items, search, statusFilter]);

  const closeModal = () => {
    if (submitting) return;
    setModal(null);
    setFormError(null);
  };

  const handleSubmit = async (values: CreateDowntimeReasonInput | UpdateDowntimeReasonInput) => {
    if (!modal || submitting) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const saved =
        modal.mode === "edit"
          ? await updateDowntimeReason(modal.reason.code, values as UpdateDowntimeReasonInput)
          : await createDowntimeReason(values as CreateDowntimeReasonInput);
      upsert(saved);
      setModal(null);
      notices.push({
        message: modal.mode === "edit" ? "Motivo atualizado." : "Motivo criado.",
        variant: "success",
      });
    } catch (requestError) {
      if (requestError instanceof DelpiMesRequestError && requestError.status === 404) {
        setModal(null);
        notices.push({ message: describeApiError(requestError), variant: "error" });
        void reload();
      } else {
        setFormError(describeApiError(requestError));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async () => {
    if (!pendingDeactivate || deactivateBusy) return;
    setDeactivateBusy(true);
    setDeactivateError(null);
    try {
      const saved = await setDowntimeReasonActive(pendingDeactivate.code, false);
      upsert(saved);
      setPendingDeactivate(null);
      notices.push({ message: "Motivo desativado.", variant: "success" });
    } catch (requestError) {
      setDeactivateError(describeApiError(requestError));
      if (requestError instanceof DelpiMesRequestError && requestError.status === 404) {
        void reload();
      }
    } finally {
      setDeactivateBusy(false);
    }
  };

  const handleReactivate = async (reason: DowntimeReason) => {
    if (reactivating) return;
    setReactivating(reason.code);
    try {
      const saved = await setDowntimeReasonActive(reason.code, true);
      upsert(saved);
      notices.push({ message: "Motivo reativado.", variant: "success" });
    } catch (requestError) {
      notices.push({ message: describeApiError(requestError), variant: "error" });
      if (requestError instanceof DelpiMesRequestError && requestError.status === 404) {
        void reload();
      }
    } finally {
      setReactivating(null);
    }
  };

  if (loading && items.length === 0) {
    return <LoadingState classNames={loadingClasses} defaultMessage="Carregando motivos de parada…" />;
  }

  if (error && items.length === 0) {
    return (
      <section className="delpi-mes-registrations-error" role="alert">
        <h2>Não foi possível carregar os motivos de parada</h2>
        <p>{error}</p>
        <button type="button" className="delpi-mes-ghost-btn" onClick={() => void reload()}>
          Tentar novamente
        </button>
      </section>
    );
  }

  return (
    <section className="delpi-mes-page" aria-labelledby="delpi-mes-page-title">
      <nav className="delpi-mes-breadcrumb" aria-label="Voltar para Cadastros">
        <button type="button" className="delpi-mes-breadcrumb__back" onClick={onBack}>
          <ChevronLeft aria-hidden="true" />
          Cadastros
        </button>
      </nav>
      <div className="delpi-mes-page__heading">
        <p className="delpi-mes-eyebrow">{copy.globalScope}</p>
        <h2 id="delpi-mes-page-title">{copy.downtimeReasons.title}</h2>
        <p>{copy.downtimeReasons.description}</p>
      </div>
      <p className="delpi-mes-global-scope" role="note">
        <strong>{copy.globalScope}</strong>
        <span>{copy.globalScopeHint}</span>
      </p>

      {items.length === 0 ? (
        <EmptyState
          title="Nenhum motivo cadastrado"
          message="Crie o primeiro motivo para começar a classificar as paradas MES."
          defaultMessage="Crie o primeiro motivo para começar a classificar as paradas MES."
          classNames={emptyClasses}
          role="status"
        >
          <button type="button" className="delpi-mes-primary-btn" onClick={() => setModal({ mode: "create" })}>
            <Plus aria-hidden="true" />
            Novo motivo
          </button>
        </EmptyState>
      ) : (
        <>
          <div className="delpi-mes-reasons-toolbar">
            <label className="delpi-mes-search">
              <Search aria-hidden="true" />
              <span className="delpi-mes-sr-only">Buscar motivo</span>
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Buscar por código, descrição ou categoria"
              />
            </label>
            <label className="delpi-mes-status-filter">
              <span className="delpi-mes-sr-only">Filtrar por status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
                aria-label="Status"
              >
                <option value="all">Todos</option>
                <option value="active">Ativos</option>
                <option value="inactive">Inativos</option>
              </select>
            </label>
            <p className="delpi-mes-counts" aria-live="polite">
              {counts.total} no total · {counts.active} ativos · {counts.inactive} inativos
            </p>
            <button
              type="button"
              className="delpi-mes-primary-btn"
              onClick={() => {
                setFormError(null);
                setModal({ mode: "create" });
              }}
            >
              <Plus aria-hidden="true" />
              Novo motivo
            </button>
          </div>

          {visible.length === 0 ? (
            <EmptyState
              title="Nenhum motivo encontrado"
              message="Ajuste a busca ou o filtro de status para localizar outros motivos."
              defaultMessage="Ajuste a busca ou o filtro de status para localizar outros motivos."
              classNames={emptyClasses}
              role="status"
            />
          ) : (
            <div className="delpi-mes-table-scroll">
              <table className="delpi-mes-reasons-table">
                <thead>
                  <tr>
                    <th scope="col">Código</th>
                    <th scope="col">Descrição</th>
                    <th scope="col">Categoria</th>
                    <th scope="col">Exige observação</th>
                    <th scope="col">Ordem</th>
                    <th scope="col">Status</th>
                    <th scope="col">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((item) => (
                    <tr key={item.code}>
                      <td>
                        <span className="delpi-mes-code">{item.code}</span>
                        {item.code === "setup" ? (
                          <span className="delpi-mes-system-tag">sistema</span>
                        ) : null}
                      </td>
                      <td>{item.label}</td>
                      <td>{item.category}</td>
                      <td>{item.requiresNote ? "Sim" : "Não"}</td>
                      <td>{item.sortOrder}</td>
                      <td>
                        <span
                          className={`delpi-mes-event-state ${item.active ? "delpi-mes-event-state--success" : "delpi-mes-event-state--inactive"}`}
                        >
                          {item.active ? "Ativo" : "Inativo"}
                        </span>
                      </td>
                      <td>
                        <div className="delpi-mes-row-actions">
                          <button
                            type="button"
                            className="delpi-mes-icon-btn"
                            onClick={() => {
                              setFormError(null);
                              setModal({ mode: "edit", reason: item });
                            }}
                          >
                            <Pencil aria-hidden="true" />
                            Editar
                          </button>
                          {item.active ? (
                            <button
                              type="button"
                              className="delpi-mes-icon-btn delpi-mes-icon-btn--danger"
                              onClick={() => {
                                setDeactivateError(null);
                                setPendingDeactivate(item);
                              }}
                            >
                              Desativar
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="delpi-mes-icon-btn"
                              disabled={reactivating === item.code}
                              onClick={() => void handleReactivate(item)}
                            >
                              {reactivating === item.code ? "Reativando…" : "Reativar"}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <ModalShell
        open={modal !== null}
        title={modal?.mode === "edit" ? "Editar motivo" : "Novo motivo"}
        onClose={closeModal}
        classNames={modalClasses}
        closeAriaLabel="Fechar formulário"
        initialFocusSelector="input:not([readonly])"
      >
        {modal ? (
          <DowntimeReasonForm
            mode={modal.mode}
            reason={modal.mode === "edit" ? modal.reason : undefined}
            busy={submitting}
            error={formError}
            categorySuggestions={categorySuggestions}
            onSubmit={(values) => void handleSubmit(values)}
            onCancel={closeModal}
          />
        ) : null}
      </ModalShell>

      <ModalShell
        open={pendingDeactivate !== null}
        title="Desativar motivo?"
        onClose={() => {
          if (deactivateBusy) return;
          setPendingDeactivate(null);
          setDeactivateError(null);
        }}
        classNames={modalClasses}
        closeAriaLabel="Fechar confirmação"
      >
        {pendingDeactivate ? (
          <ConfirmModalPanel
            variant="danger"
            message={
              <span>
                <span className="delpi-mes-code">{pendingDeactivate.code}</span> deixará de aparecer
                para novas classificações de parada. Registros históricos que já utilizam esse motivo
                serão preservados.
                {deactivateError ? (
                  <span className="delpi-mes-form__error" role="alert">{deactivateError}</span>
                ) : null}
              </span>
            }
            confirmLabel="Desativar motivo"
            confirmBusy={deactivateBusy}
            confirmBusyLabel="Desativando…"
            onConfirm={() => void handleDeactivate()}
            onCancel={() => {
              setPendingDeactivate(null);
              setDeactivateError(null);
            }}
            classNames={confirmClasses}
          />
        ) : null}
      </ModalShell>

      <FloatingNoticeStack
        items={notices.items}
        onDismiss={notices.dismiss}
        classNames={noticeClasses}
        labels={{ dismissAriaLabel: "Fechar aviso", stackAriaLabel: "Avisos do cadastro" }}
      />
    </section>
  );
}
