import { useEffect, useState, type ReactNode } from "react";
import {
  IconButton,
  NativeCheckboxControl,
  SectionCard,
} from "@delpi/plugin-ui/index";
import {
  Copy,
  Mail,
  MessageCircle,
  Pencil,
  Phone,
  Plus,
  Trash2,
  UserRound,
} from "lucide-react";

import {
  createAccountContact,
  deleteAccountContact,
  getAccountContactsBundle,
  updateAccountContact,
  type AccountContact,
  type AccountContactChannel,
  type AccountContactInput,
  type AccountContactsBundle,
} from "../../../api/accountContactsApi";
import { useCommercialConfirm } from "../../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../../app/CommercialFloatingNoticeProvider";
import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  cmSectionCardClassNames,
  cmSectionLabels,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  buildWhatsAppGreeting,
  buildWhatsAppUrl,
} from "../../../content/whatsapp";

type AccountContactsPanelProps = {
  customerCode: string;
  customerStore: string;
  refreshKey?: number;
};

type ContactFormState = {
  fullName: string;
  roleTitle: string;
  channel: AccountContactChannel;
  email: string;
  phoneE164: string;
  isWhatsApp: boolean;
  isPrimary: boolean;
};

const EMPTY_FORM: ContactFormState = {
  fullName: "",
  roleTitle: "",
  channel: "mobile",
  email: "",
  phoneE164: "",
  isWhatsApp: false,
  isPrimary: false,
};

const CHANNEL_OPTIONS = [
  { value: "phone", label: "Telefone" },
  { value: "mobile", label: "Celular" },
  { value: "email", label: "E-mail" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "other", label: "Outro" },
] as const;

const CHANNEL_LABELS: Record<AccountContactChannel, string> = {
  phone: "Telefone",
  mobile: "Celular",
  email: "E-mail",
  whatsapp: "WhatsApp",
  other: "Outro",
};

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function toBrazilianE164(phone: string | null): string | null {
  const digits = (phone ?? "").replace(/\D/g, "");
  if (/^55\d{10,11}$/.test(digits)) return `+${digits}`;
  if (/^\d{10,11}$/.test(digits)) return `+55${digits}`;
  return null;
}

function looksLikeBrazilianMobile(e164: string | null): e164 is string {
  return Boolean(e164 && /^\+55\d{2}9\d{8}$/.test(e164));
}

function formFromContact(contact: AccountContact): ContactFormState {
  return {
    fullName: contact.full_name,
    roleTitle: contact.role_title ?? "",
    channel: contact.channel,
    email: contact.email ?? "",
    phoneE164: contact.phone_e164 ?? "",
    isWhatsApp: contact.is_whatsapp,
    isPrimary: contact.is_primary,
  };
}

function inputFromForm(form: ContactFormState): AccountContactInput {
  return {
    full_name: form.fullName.trim(),
    role_title: form.roleTitle.trim() || null,
    channel: form.channel,
    email: form.email.trim() || null,
    phone_e164: form.phoneE164.trim() || null,
    is_whatsapp: form.isWhatsApp,
    is_primary: form.isPrimary,
    source: "manual",
  };
}

function contactInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
}

function CopyableFieldValue({
  value,
  copyLabel,
  onCopy,
}: {
  value: string;
  copyLabel: string;
  onCopy: (text: string, label: string) => void;
}) {
  return (
    <span className="cm-nav-row">
      <span>{value}</span>
      <IconButton
        aria-label={`Copiar ${copyLabel}`}
        onClick={() => onCopy(value, copyLabel)}
      >
        <Copy size={14} aria-hidden />
      </IconButton>
    </span>
  );
}

function ContactActionBar({
  fullName,
  phone,
  email,
  showWhatsApp,
}: {
  fullName: string;
  phone: string | null;
  email: string | null;
  showWhatsApp: boolean;
}) {
  const telHref = phone ? `tel:${phone.replace(/\s+/g, "")}` : null;
  const mailHref = email ? `mailto:${email}` : null;
  const waHref =
    showWhatsApp && phone
      ? buildWhatsAppUrl(phone, buildWhatsAppGreeting(fullName))
      : null;

  if (!telHref && !mailHref && !waHref) return null;

  return (
    <div className="cm-nav-row" role="group" aria-label="Ações de contato">
      {telHref ? (
        <CommercialActionButton
          variant="ghost"
          onClick={() => {
            window.location.href = telHref;
          }}
        >
          <Phone size={16} aria-hidden />
          Ligar
        </CommercialActionButton>
      ) : null}
      {mailHref ? (
        <CommercialActionButton
          variant="ghost"
          onClick={() => {
            window.location.href = mailHref;
          }}
        >
          <Mail size={16} aria-hidden />
          E-mail
        </CommercialActionButton>
      ) : null}
      {waHref ? (
        <CommercialActionButton
          variant="ghost"
          aria-label={CM_HELP.customerDetail.whatsapp}
          onClick={() => {
            window.open(waHref, "_blank", "noopener,noreferrer");
          }}
        >
          <MessageCircle size={16} aria-hidden />
          WhatsApp
        </CommercialActionButton>
      ) : null}
    </div>
  );
}

function ContactFormFields({
  form,
  setForm,
  formError,
}: {
  form: ContactFormState;
  setForm: (updater: (current: ContactFormState) => ContactFormState) => void;
  formError: string | null;
}) {
  return (
    <div className="cm-form-grid">
      {formError ? (
        <div className="cm-form-grid__full">
          <CommercialStateBanner variant="error">{formError}</CommercialStateBanner>
        </div>
      ) : null}
      <CommercialTextField
        label="Nome completo"
        value={form.fullName}
        onChange={(fullName) => setForm((current) => ({ ...current, fullName }))}
        required
        fullWidth
      />
      <CommercialTextField
        label="Cargo ou função"
        value={form.roleTitle}
        onChange={(roleTitle) => setForm((current) => ({ ...current, roleTitle }))}
        fullWidth
      />
      <CommercialSelectField
        label="Canal preferencial"
        value={form.channel}
        options={[...CHANNEL_OPTIONS]}
        onChange={(channel) =>
          setForm((current) => ({
            ...current,
            channel: channel as AccountContactChannel,
            isWhatsApp: channel === "whatsapp" ? true : current.isWhatsApp,
          }))
        }
      />
      <CommercialTextField
        label="E-mail"
        value={form.email}
        onChange={(email) => setForm((current) => ({ ...current, email }))}
        fullWidth
      />
      <CommercialTextField
        label="Telefone E.164"
        hint="Use +, código do país, DDD e número. Ex.: +5547999999999."
        value={form.phoneE164}
        onChange={(phoneE164) => setForm((current) => ({ ...current, phoneE164 }))}
        placeholder="+5547999999999"
        fullWidth
      />
      <NativeCheckboxControl
        checked={form.isWhatsApp}
        onChange={(isWhatsApp) => setForm((current) => ({ ...current, isWhatsApp }))}
        label="Disponível no WhatsApp"
      />
      <NativeCheckboxControl
        checked={form.isPrimary}
        onChange={(isPrimary) => setForm((current) => ({ ...current, isPrimary }))}
        label="Contato principal"
      />
    </div>
  );
}

export function AccountContactsPanel({
  customerCode,
  customerStore,
  refreshKey = 0,
}: AccountContactsPanelProps) {
  const confirm = useCommercialConfirm();
  const { notifySuccess, notifyError } = useCommercialFloatingNotice();
  const [bundle, setBundle] = useState<AccountContactsBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<AccountContact | null>(null);
  const [form, setForm] = useState<ContactFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getAccountContactsBundle(customerCode, customerStore, controller.signal)
      .then((nextBundle) => {
        setBundle(nextBundle);
        setError(null);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(errorMessage(requestError, "Erro ao carregar contatos."));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [customerCode, customerStore, refreshKey]);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(contact: AccountContact) {
    setEditing(contact);
    setForm(formFromContact(contact));
    setFormError(null);
    setFormOpen(true);
  }

  function closeForm(options?: { force?: boolean }) {
    if (saving && !options?.force) return;
    setFormOpen(false);
    setEditing(null);
    setFormError(null);
    setForm(EMPTY_FORM);
  }

  async function copyText(text: string, label: string) {
    const value = text.trim();
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      notifySuccess(`${label} copiado.`);
    } catch {
      notifyError(`Não foi possível copiar ${label.toLowerCase()}.`);
    }
  }

  async function saveContact() {
    const input = inputFromForm(form);
    if (!input.full_name) {
      setFormError("Informe o nome completo.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const saved = editing
        ? await updateAccountContact(customerCode, customerStore, editing.id, input)
        : await createAccountContact(customerCode, customerStore, input);
      setBundle((current) => {
        if (!current) return { totvs_contact: null, items: [saved] };
        const items = editing
          ? current.items.map((item) => (item.id === saved.id ? saved : item))
          : [saved, ...current.items];
        return { ...current, items };
      });
      notifySuccess(editing ? "Contato atualizado." : "Contato adicionado.");
      closeForm({ force: true });
    } catch (requestError: unknown) {
      setFormError(errorMessage(requestError, "Erro ao salvar contato."));
    } finally {
      setSaving(false);
    }
  }

  async function removeContact(contact: AccountContact) {
    const accepted = await confirm({
      title: "Remover contato",
      message: `Remover ${contact.full_name} dos contatos locais desta conta?`,
      confirmLabel: "Remover",
      variant: "danger",
    });
    if (!accepted) return;
    setDeletingId(contact.id);
    setError(null);
    try {
      await deleteAccountContact(customerCode, customerStore, contact.id);
      setBundle((current) =>
        current
          ? { ...current, items: current.items.filter((item) => item.id !== contact.id) }
          : current,
      );
      if (editing?.id === contact.id) closeForm();
      notifySuccess("Contato removido.");
    } catch (requestError: unknown) {
      setError(errorMessage(requestError, "Erro ao remover contato."));
    } finally {
      setDeletingId(null);
    }
  }

  const totvsContact = bundle?.totvs_contact ?? null;
  const totvsPhoneE164 = toBrazilianE164(totvsContact?.phone ?? null);
  const totvsDisplayName = (totvsContact?.full_name || "").trim() || "Nome não informado";
  const formTitle = editing ? "Editar contato" : "Novo contato";

  return (
    <div className="cm-contacts-stack">
      {loading && !bundle ? (
        <CommercialLoadingCard title="Carregando contatos…" variant="panel" />
      ) : null}
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      <SectionCard
        title="Contato do cadastro TOTVS"
        subtitle="Dados oficiais da conta, disponíveis somente para consulta."
        hint={CM_HELP.customerDetail.contactsTotvs}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {totvsContact ? (
          <CommercialDataRecordCard
            leading={<UserRound size={20} aria-hidden />}
            title={totvsDisplayName}
            subtitle="Cadastro SA1 · somente leitura"
            status={
              <CommercialStatusBadge label="TOTVS" variant="info" />
            }
            fields={[
              {
                id: "phone",
                label: "Telefone",
                present: Boolean(totvsContact.phone),
                value: totvsContact.phone ? (
                  <CopyableFieldValue
                    value={totvsContact.phone}
                    copyLabel="telefone"
                    onCopy={copyText}
                  />
                ) : null,
              },
              {
                id: "email",
                label: "E-mail",
                present: Boolean(totvsContact.email),
                value: totvsContact.email ? (
                  <CopyableFieldValue
                    value={totvsContact.email}
                    copyLabel="e-mail"
                    onCopy={copyText}
                  />
                ) : null,
              },
            ]}
            context={
              <ContactActionBar
                fullName={totvsContact.full_name || "cliente"}
                phone={totvsPhoneE164 ?? totvsContact.phone}
                email={totvsContact.email}
                showWhatsApp={looksLikeBrazilianMobile(totvsPhoneE164)}
              />
            }
          />
        ) : (
          <CommercialEmptyState
            title="Sem contato TOTVS"
            message="O cadastro não possui nome, telefone ou e-mail de contato."
          />
        )}
      </SectionCard>

      <SectionCard
        title="Contatos locais"
        subtitle="Contatos complementares mantidos pela equipe comercial."
        hint={CM_HELP.customerDetail.contactsLocal}
        actions={
          formOpen ? (
            <CommercialActionButton variant="ghost" onClick={closeForm} disabled={saving}>
              Fechar formulário
            </CommercialActionButton>
          ) : (
            <CommercialActionButton variant="primary" onClick={openCreate}>
              <Plus size={16} aria-hidden />
              Adicionar contato
            </CommercialActionButton>
          )
        }
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-contacts-stack">
          <SectionCard
            title={formTitle}
            subtitle="Dados complementares da conta mantidos pela equipe comercial."
            collapsible
            open={formOpen}
            onOpenChange={(open) => {
              if (open) {
                if (!formOpen) openCreate();
                return;
              }
              closeForm();
            }}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
            actions={
              formOpen ? (
                <div className="cm-nav-row">
                  <CommercialActionButton
                    variant="ghost"
                    onClick={closeForm}
                    disabled={saving}
                  >
                    Cancelar
                  </CommercialActionButton>
                  <CommercialActionButton
                    variant="primary"
                    onClick={() => void saveContact()}
                    disabled={saving}
                  >
                    {saving ? "Salvando…" : "Salvar contato"}
                  </CommercialActionButton>
                </div>
              ) : undefined
            }
          >
            <ContactFormFields form={form} setForm={setForm} formError={formError} />
          </SectionCard>

          {bundle && bundle.items.length === 0 && !formOpen ? (
            <CommercialEmptyState
              title="Nenhum contato local"
              message="Adicione contatos complementares para ligar, enviar e-mail ou abrir o WhatsApp."
            >
              <CommercialActionButton variant="primary" onClick={openCreate}>
                <Plus size={16} aria-hidden />
                Adicionar contato
              </CommercialActionButton>
            </CommercialEmptyState>
          ) : null}

          {bundle?.items.map((contact) => {
            const statusBadges: ReactNode = (
              <span className="cm-nav-row">
                {contact.is_primary ? (
                  <CommercialStatusBadge label="Principal" variant="success" />
                ) : null}
                {contact.is_whatsapp ? (
                  <CommercialStatusBadge label="WhatsApp" variant="info" />
                ) : null}
              </span>
            );
            return (
              <CommercialDataRecordCard
                key={contact.id}
                leading={<span aria-hidden>{contactInitials(contact.full_name)}</span>}
                title={contact.full_name}
                subtitle={
                  contact.role_title?.trim() ||
                  CHANNEL_LABELS[contact.channel] ||
                  "Contato local"
                }
                status={statusBadges}
                fields={[
                  {
                    id: "channel",
                    label: "Canal",
                    value: CHANNEL_LABELS[contact.channel],
                  },
                  {
                    id: "phone",
                    label: "Telefone",
                    present: Boolean(contact.phone_e164),
                    value: contact.phone_e164 ? (
                      <CopyableFieldValue
                        value={contact.phone_e164}
                        copyLabel="telefone"
                        onCopy={copyText}
                      />
                    ) : null,
                  },
                  {
                    id: "email",
                    label: "E-mail",
                    present: Boolean(contact.email),
                    value: contact.email ? (
                      <CopyableFieldValue
                        value={contact.email}
                        copyLabel="e-mail"
                        onCopy={copyText}
                      />
                    ) : null,
                  },
                ]}
                context={
                  <div className="cm-contacts-card-actions">
                    <ContactActionBar
                      fullName={contact.full_name}
                      phone={contact.phone_e164}
                      email={contact.email}
                      showWhatsApp={contact.is_whatsapp}
                    />
                    <div className="cm-nav-row">
                      <CommercialActionButton
                        variant="ghost"
                        onClick={() => openEdit(contact)}
                      >
                        <Pencil size={16} aria-hidden />
                        Editar
                      </CommercialActionButton>
                      <CommercialActionButton
                        variant="ghost"
                        onClick={() => void removeContact(contact)}
                        disabled={deletingId === contact.id}
                      >
                        <Trash2 size={16} aria-hidden />
                        {deletingId === contact.id ? "Removendo…" : "Remover"}
                      </CommercialActionButton>
                    </div>
                  </div>
                }
              />
            );
          })}
        </div>
      </SectionCard>
    </div>
  );
}
