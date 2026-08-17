import type {
  AccountContact,
  TotvsAccountContact,
} from "../api/accountContactsApi";
import type { ProposalDocumentContact } from "../types/proposalsDocument";

/** Valor do select: contato já gravado no documento da proposta. */
export const PROPOSAL_PDF_CONTACT_PROPOSAL = "__proposal__";
/** Valor do select: contato TOTVS do cadastro da conta. */
export const PROPOSAL_PDF_CONTACT_TOTVS = "__totvs__";

export type ProposalPdfContactOption = {
  value: string;
  label: string;
  nome: string;
  email: string;
  departamento: string;
  telefone: string;
};

function normalize(value: string | null | undefined): string {
  return (value ?? "").trim();
}

function labelFor(nome: string, email: string, suffix?: string): string {
  const base = email ? `${nome} · ${email}` : nome;
  return suffix ? `${base} (${suffix})` : base;
}

export function buildProposalPdfContactOptions(input: {
  proposalContact: ProposalDocumentContact | null | undefined;
  totvsContact: TotvsAccountContact | null | undefined;
  savedContacts: readonly AccountContact[];
}): ProposalPdfContactOption[] {
  const options: ProposalPdfContactOption[] = [];
  const proposalNome = normalize(input.proposalContact?.nome);
  const proposalEmail = normalize(input.proposalContact?.email);
  const proposalDepartamento = normalize(input.proposalContact?.departamento);
  const proposalTelefone = normalize(input.proposalContact?.telefone);
  if (proposalNome || proposalEmail) {
    options.push({
      value: PROPOSAL_PDF_CONTACT_PROPOSAL,
      label: labelFor(
        proposalNome || "Contato da proposta",
        proposalEmail,
        "proposta",
      ),
      nome: proposalNome,
      email: proposalEmail,
      departamento: proposalDepartamento,
      telefone: proposalTelefone,
    });
  }

  const totvsNome = normalize(input.totvsContact?.full_name);
  const totvsEmail = normalize(input.totvsContact?.email);
  const totvsTelefone = normalize(input.totvsContact?.phone);
  const totvsDistinct =
    (totvsNome || totvsEmail) &&
    (totvsNome !== proposalNome || totvsEmail !== proposalEmail);
  if (totvsDistinct) {
    options.push({
      value: PROPOSAL_PDF_CONTACT_TOTVS,
      label: labelFor(totvsNome || "Contato TOTVS", totvsEmail, "TOTVS"),
      nome: totvsNome,
      email: totvsEmail,
      departamento: "",
      telefone: totvsTelefone,
    });
  }

  for (const contact of input.savedContacts) {
    const nome = normalize(contact.full_name);
    const email = normalize(contact.email);
    if (!nome && !email) continue;
    const primary = contact.is_primary ? "principal" : "salvo";
    options.push({
      value: contact.id,
      label: labelFor(nome || "Contato", email, primary),
      nome,
      email,
      departamento: normalize(contact.role_title),
      telefone: normalize(contact.phone_e164),
    });
  }

  return options;
}

/** Preferência: contato salvo com mesmo e-mail/nome; senão proposta; senão 1ª opção. */
export function defaultProposalPdfContactValue(
  options: readonly ProposalPdfContactOption[],
  proposalContact: ProposalDocumentContact | null | undefined,
): string {
  if (options.length === 0) return "";
  const nome = normalize(proposalContact?.nome);
  const email = normalize(proposalContact?.email);
  const matchedSaved = options.find(
    (option) =>
      option.value !== PROPOSAL_PDF_CONTACT_PROPOSAL &&
      option.value !== PROPOSAL_PDF_CONTACT_TOTVS &&
      ((email && option.email.toLowerCase() === email.toLowerCase()) ||
        (nome && option.nome.toLowerCase() === nome.toLowerCase())),
  );
  if (matchedSaved) return matchedSaved.value;
  if (options.some((option) => option.value === PROPOSAL_PDF_CONTACT_PROPOSAL)) {
    return PROPOSAL_PDF_CONTACT_PROPOSAL;
  }
  return options[0]?.value ?? "";
}

export function resolveProposalPdfContactSelection(
  options: readonly ProposalPdfContactOption[],
  selectedValue: string,
): {
  nome: string;
  email: string;
  departamento: string;
  telefone: string;
} | null {
  const selected = options.find((option) => option.value === selectedValue);
  if (!selected) return null;
  return {
    nome: selected.nome,
    email: selected.email,
    departamento: selected.departamento,
    telefone: selected.telefone,
  };
}
