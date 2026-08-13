import { useEffect, useState } from "react";
import { SectionCard } from "@delpi/plugin-ui/index";

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
import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialLoadingCard,
  CommercialSelectField,
  CommercialStateBanner,
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

function ContactLinks({
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
  return (
    <div className="cm-nav-row">
      {phone ? <a href={`tel:${phone}`}>Ligar para {phone}</a> : null}
      {email ? <a href={`mailto:${email}`}>Enviar e-mail</a> : null}
      {showWhatsApp && phone ? (
        <a
          href={buildWhatsAppUrl(phone, buildWhatsAppGreeting(fullName))}
          target="_blank"
          rel="noreferrer"
          title={CM_HELP.customerDetail.whatsapp}
        >
          Abrir WhatsApp
        </a>
      ) : null}
    </div>
  );
}

export function AccountContactsPanel({
  customerCode,
  customerStore,
  refreshKey = 0,
}: AccountContactsPanelProps) {
  const confirm = useCommercialConfirm();
  const [bundle, setBundle] = useState<AccountContactsBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AccountContact | null>(null);
  const [form, setForm] = useState<ContactFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
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
    setDialogOpen(true);
  }

  function openEdit(contact: AccountContact) {
    setEditing(contact);
    setForm(formFromContact(contact));
    setFormError(null);
    setDialogOpen(true);
  }

  function closeDialog() {
    if (saving) return;
    setDialogOpen(false);
    setEditing(null);
    setFormError(null);
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
      setDialogOpen(false);
      setEditing(null);
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
    } catch (requestError: unknown) {
      setError(errorMessage(requestError, "Erro ao remover contato."));
    } finally {
      setDeletingId(null);
    }
  }

  const totvsContact = bundle?.totvs_contact ?? null;
  const totvsPhoneE164 = toBrazilianE164(totvsContact?.phone ?? null);

  return (
    <>
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
          <article>
            <strong>{totvsContact.full_name || "Nome não informado"}</strong>
            {totvsContact.phone ? <p>Telefone: {totvsContact.phone}</p> : null}
            {totvsContact.email ? <p>E-mail: {totvsContact.email}</p> : null}
            <ContactLinks
              fullName={totvsContact.full_name || "cliente"}
              phone={totvsPhoneE164 ?? totvsContact.phone}
              email={totvsContact.email}
              showWhatsApp={looksLikeBrazilianMobile(totvsPhoneE164)}
            />
          </article>
        ) : (
          <p role="status">O cadastro TOTVS não possui nome, telefone ou e-mail de contato.</p>
        )}
      </SectionCard>

      <SectionCard
        title="Contatos locais"
        subtitle="Contatos complementares mantidos pela equipe comercial."
        hint={CM_HELP.customerDetail.contactsLocal}
        actions={
          <CommercialActionButton variant="primary" onClick={openCreate}>
            Adicionar contato
          </CommercialActionButton>
        }
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {bundle && bundle.items.length === 0 ? (
          <p role="status">Nenhum contato local cadastrado.</p>
        ) : null}
        {bundle?.items.map((contact) => (
          <article key={contact.id}>
            <strong>
              {contact.full_name}
              {contact.is_primary ? " · Principal" : ""}
            </strong>
            {contact.role_title ? <p>{contact.role_title}</p> : null}
            <ContactLinks
              fullName={contact.full_name}
              phone={contact.phone_e164}
              email={contact.email}
              showWhatsApp={contact.is_whatsapp}
            />
            <div className="cm-nav-row">
              <CommercialActionButton variant="ghost" onClick={() => openEdit(contact)}>
                Editar
              </CommercialActionButton>
              <CommercialActionButton
                variant="ghost"
                onClick={() => void removeContact(contact)}
                disabled={deletingId === contact.id}
              >
                {deletingId === contact.id ? "Removendo…" : "Remover"}
              </CommercialActionButton>
            </div>
          </article>
        ))}
      </SectionCard>

      <CommercialHostDialog
        open={dialogOpen}
        title={editing ? "Editar contato" : "Novo contato"}
        description="Dados complementares da conta mantidos pela equipe comercial."
        onClose={closeDialog}
        footer={
          <div className="cm-nav-row">
            <CommercialActionButton variant="ghost" onClick={closeDialog} disabled={saving}>
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
        }
      >
        {formError ? (
          <CommercialStateBanner variant="error">{formError}</CommercialStateBanner>
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
        <label>
          <input
            type="checkbox"
            checked={form.isWhatsApp}
            onChange={(event) =>
              setForm((current) => ({ ...current, isWhatsApp: event.target.checked }))
            }
          />
          Disponível no WhatsApp
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.isPrimary}
            onChange={(event) =>
              setForm((current) => ({ ...current, isPrimary: event.target.checked }))
            }
          />
          Contato principal
        </label>
      </CommercialHostDialog>
    </>
  );
}
