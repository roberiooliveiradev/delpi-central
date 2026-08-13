import { describe, expect, it } from "vitest";

import type { AccountContact } from "../api/accountContactsApi";
import {
  PROPOSAL_PDF_CONTACT_PROPOSAL,
  PROPOSAL_PDF_CONTACT_TOTVS,
  buildProposalPdfContactOptions,
  defaultProposalPdfContactValue,
  resolveProposalPdfContactSelection,
} from "./resolveProposalPdfContact";

function saved(partial: Partial<AccountContact> & Pick<AccountContact, "id" | "full_name">): AccountContact {
  return {
    customer_code: "0001",
    customer_store: "01",
    role_title: null,
    channel: "email",
    email: null,
    phone_e164: null,
    is_whatsapp: false,
    is_primary: false,
    source: "local",
    created_at: "",
    updated_at: "",
    ...partial,
  };
}

describe("resolveProposalPdfContact", () => {
  const proposalContact = {
    codigo: "1",
    nome: "Ana Proposta",
    email: "ana@cliente.com",
    telefone: null,
    departamento: "",
  };

  it("monta opções proposta + TOTVS distinto + salvos", () => {
    const options = buildProposalPdfContactOptions({
      proposalContact,
      totvsContact: {
        full_name: "Carlos Totvs",
        phone: null,
        email: "carlos@cliente.com",
        source: "totvs",
        read_only: true,
      },
      savedContacts: [saved({ id: "c1", full_name: "Beatriz Salva", email: "bia@cliente.com", is_primary: true })],
    });
    expect(options).toHaveLength(3);
    expect(options[0]?.value).toBe(PROPOSAL_PDF_CONTACT_PROPOSAL);
    expect(options[1]?.value).toBe(PROPOSAL_PDF_CONTACT_TOTVS);
    expect(options[2]?.value).toBe("c1");
  });

  it("não duplica TOTVS igual ao contato da proposta", () => {
    const options = buildProposalPdfContactOptions({
      proposalContact,
      totvsContact: {
        full_name: "Ana Proposta",
        phone: null,
        email: "ana@cliente.com",
        source: "totvs",
        read_only: true,
      },
      savedContacts: [],
    });
    expect(options).toHaveLength(1);
    expect(options[0]?.value).toBe(PROPOSAL_PDF_CONTACT_PROPOSAL);
  });

  it("default preferê contato salvo com mesmo e-mail", () => {
    const options = buildProposalPdfContactOptions({
      proposalContact,
      totvsContact: null,
      savedContacts: [
        saved({ id: "c1", full_name: "Ana Proposta", email: "ana@cliente.com" }),
      ],
    });
    expect(defaultProposalPdfContactValue(options, proposalContact)).toBe("c1");
  });

  it("resolve seleção para overrides", () => {
    const options = buildProposalPdfContactOptions({
      proposalContact,
      totvsContact: null,
      savedContacts: [
        saved({
          id: "c1",
          full_name: "Beatriz",
          email: "bia@cliente.com",
          role_title: "Compras",
          phone_e164: "+5547999000000",
        }),
      ],
    });
    expect(resolveProposalPdfContactSelection(options, "c1")).toEqual({
      nome: "Beatriz",
      email: "bia@cliente.com",
      departamento: "Compras",
      telefone: "+5547999000000",
    });
  });

  it("inclui telefone TOTVS e departamento da proposta nas opções", () => {
    const options = buildProposalPdfContactOptions({
      proposalContact: {
        ...proposalContact,
        departamento: "Engenharia",
        telefone: "4733330000",
      },
      totvsContact: {
        full_name: "Carlos Totvs",
        phone: "+5547888000000",
        email: "carlos@cliente.com",
        source: "totvs",
        read_only: true,
      },
      savedContacts: [],
    });
    expect(options[0]).toMatchObject({
      value: PROPOSAL_PDF_CONTACT_PROPOSAL,
      departamento: "Engenharia",
      telefone: "4733330000",
    });
    expect(options[1]).toMatchObject({
      value: PROPOSAL_PDF_CONTACT_TOTVS,
      telefone: "+5547888000000",
      departamento: "",
    });
  });
});
