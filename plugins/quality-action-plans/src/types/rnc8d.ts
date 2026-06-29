export type Rnc8dClassification = {
  receipt?: boolean;
  production?: boolean;
  end_customer?: boolean;
};

export type Rnc8dNcDescription = {
  characteristic?: string;
  specified?: string;
  verified?: string;
  observations?: string;
};

export type Rnc8dContainmentRow = {
  area: "end_customer" | "client_plant" | "supplier";
  quantity?: string;
  action_plan?: string;
  responsible?: string;
  date?: string;
};

export type Rnc8dEffectiveness = {
  resolved_how?: string;
  ok_material_date?: string;
  new_parts_identification?: string;
  verification_responsible?: string;
  verification_date?: string;
};

export type Rnc8dPreventive = {
  how_avoid_future?: string;
  other_processes_products?: string;
  evaluation_responsible?: string;
  evaluation_completion_date?: string;
};

export type Rnc8dDocumentationRow = {
  document?: string;
  responsible?: string;
  date?: string;
};

export type Rnc8dTemplatePayload = {
  classification?: Rnc8dClassification;
  supplier_name?: string;
  material_specification?: string;
  purchase_order?: string;
  invoice_number?: string;
  invoice_date?: string;
  defective_quantity?: string;
  return_invoice_number?: string;
  contact_phone?: string;
  contact_fax?: string;
  client_batch?: string;
  batch_quantity?: string;
  disposition?: string;
  rejected_quantity?: string;
  report_date?: string;
  observations?: string;
  return_by?: string;
  attention_to?: string;
  attention_email?: string;
  nc_description?: Rnc8dNcDescription;
  containment?: Rnc8dContainmentRow[];
  effectiveness?: Rnc8dEffectiveness;
  preventive?: Rnc8dPreventive;
  documentation_updates?: Rnc8dDocumentationRow[];
  client_closure_note?: string;
};

export type TeamMember = {
  id?: string;
  member_name: string;
  department?: string;
  is_leader?: boolean;
  sort_order?: number;
};

export type PlanEvidence = {
  id: string;
  type: string;
  file_name?: string | null;
  section?: string;
  description?: string | null;
  mime_type?: string | null;
  size_bytes?: number | null;
  knowledge_visible?: boolean;
  action_id?: string | null;
  uploaded_by?: string;
  uploaded_by_name?: string | null;
  uploaded_by_email?: string | null;
  created_at?: string;
};

export type Rnc8dReportPayload = {
  client_nc_registry?: string;
  customer_name?: string;
  customer_contact?: string;
  product_code?: string;
  product_description?: string;
  batch_number?: string;
  reported_problem?: string;
  template_payload?: Rnc8dTemplatePayload;
  team_members?: TeamMember[];
};

export function emptyRnc8dPayload(): Rnc8dTemplatePayload {
  return {
    classification: { end_customer: true },
    nc_description: {
      characteristic: "Dimensional / Especificações / Componentes",
      specified: "Conforme Padrão (OK/NOK)",
    },
    containment: [
      { area: "end_customer" },
      { area: "client_plant" },
      { area: "supplier" },
    ],
    effectiveness: {},
    preventive: {},
    documentation_updates: [{}, {}, {}, {}],
  };
}
