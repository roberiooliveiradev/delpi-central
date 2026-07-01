import type { Rnc8dReportPayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";

export type DelpiContactArea = "comercial" | "qualidade" | "pcp" | "engenharia" | "outro";

export const DELPI_CONTACT_AREA_OPTIONS: Array<{ value: DelpiContactArea; label: string }> = [
  { value: "comercial", label: "Comercial" },
  { value: "qualidade", label: "Qualidade" },
  { value: "pcp", label: "PCP" },
  { value: "engenharia", label: "Engenharia" },
  { value: "outro", label: "Outro" },
];

export type PlanContactRolesSource = {
  customer_contact?: string | null;
  customer_contact_email?: string | null;
  customer_contact_phone?: string | null;
  delpi_contact_name?: string | null;
  delpi_contact_area?: string | null;
  delpi_sales_rep?: string | null;
  delpi_quality_contact?: string | null;
  template_payload?: Rnc8dReportPayload["template_payload"];
  contact_roles?: {
    customer_contact?: string | null;
    customer_contact_email?: string | null;
    customer_contact_phone?: string | null;
    delpi_contact_name?: string | null;
    delpi_contact_area?: string | null;
    delpi_sales_rep?: string | null;
    delpi_quality_contact?: string | null;
    delpi_contact_phone?: string | null;
  };
};

export function hydrateContactRolesFromPlan(plan: PlanContactRolesSource): Pick<
  Rnc8dReportPayload,
  | "customer_contact"
  | "customer_contact_email"
  | "customer_contact_phone"
  | "delpi_contact_name"
  | "delpi_contact_area"
  | "delpi_sales_rep"
  | "delpi_quality_contact"
> {
  const payload = plan.template_payload ?? emptyRnc8dPayload();
  const roles = plan.contact_roles;

  if (roles) {
    return {
      customer_contact: roles.customer_contact ?? "",
      customer_contact_email: roles.customer_contact_email ?? "",
      customer_contact_phone: roles.customer_contact_phone ?? "",
      delpi_contact_name: roles.delpi_contact_name ?? "",
      delpi_contact_area: roles.delpi_contact_area ?? "",
      delpi_sales_rep: roles.delpi_sales_rep ?? "",
      delpi_quality_contact: roles.delpi_quality_contact ?? "",
    };
  }

  const attentionTo = payload.attention_to?.trim() ?? "";
  const legacyCustomer = plan.customer_contact?.trim() ?? "";
  const delpiExplicit = plan.delpi_contact_name?.trim() ?? "";

  let customerContact = legacyCustomer || attentionTo;
  let delpiContact = delpiExplicit;

  if (!delpiContact && attentionTo && legacyCustomer && attentionTo !== legacyCustomer) {
    delpiContact = legacyCustomer;
    customerContact = attentionTo;
  }

  return {
    customer_contact: customerContact,
    customer_contact_email:
      plan.customer_contact_email?.trim() ?? payload.attention_email?.trim() ?? "",
    customer_contact_phone:
      plan.customer_contact_phone?.trim() ?? payload.customer_contact_phone?.trim() ?? "",
    delpi_contact_name: delpiContact,
    delpi_contact_area: plan.delpi_contact_area?.trim() ?? "",
    delpi_sales_rep: plan.delpi_sales_rep?.trim() ?? "",
    delpi_quality_contact: plan.delpi_quality_contact?.trim() ?? "",
  };
}

export function syncLegacyAttentionFields(payload: Rnc8dReportPayload): Rnc8dReportPayload {
  const template = { ...(payload.template_payload ?? emptyRnc8dPayload()) };
  const customerContact = payload.customer_contact?.trim();
  const customerEmail = payload.customer_contact_email?.trim();
  const customerPhone = payload.customer_contact_phone?.trim();

  if (customerContact) {
    template.attention_to = customerContact;
  }
  if (customerEmail) {
    template.attention_email = customerEmail;
  }
  if (customerPhone) {
    template.customer_contact_phone = customerPhone;
  }

  return {
    ...payload,
    template_payload: template,
  };
}
