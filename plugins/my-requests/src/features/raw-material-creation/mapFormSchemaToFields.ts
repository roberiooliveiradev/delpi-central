export type FormSchemaProperty = {
  type?: string;
  title?: string;
  enum?: string[];
  minLength?: number;
};

export type FormSchema = {
  type?: string;
  required?: string[];
  properties?: Record<string, FormSchemaProperty>;
  additionalProperties?: boolean;
};

export type UiSchema = Record<string, { widget?: string; hint?: string }>;

export type MappedField = {
  name: string;
  label: string;
  required: boolean;
  kind: "text" | "select" | "textarea";
  options?: { value: string; label: string }[];
  hint?: string;
};

/** Maps JSON Schema + ui_schema to kit field descriptors (no React). */
export function mapFormSchemaToFields(
  formSchema: FormSchema | null | undefined,
  uiSchema: UiSchema | null | undefined = {},
): MappedField[] {
  const properties = formSchema?.properties || {};
  const required = new Set(formSchema?.required || []);
  const ui = uiSchema || {};
  const fields: MappedField[] = [];

  for (const [name, prop] of Object.entries(properties)) {
    const title = prop.title || name;
    const enumValues = Array.isArray(prop.enum) ? prop.enum : [];
    const widget = ui[name]?.widget;
    let kind: MappedField["kind"] = "text";
    if (enumValues.length > 0) kind = "select";
    else if (widget === "textarea") kind = "textarea";

    fields.push({
      name,
      label: title,
      required: required.has(name),
      kind,
      options: enumValues.map((value) => ({ value, label: value })),
      hint: ui[name]?.hint,
    });
  }
  return fields;
}

export function emptyValuesFromFields(fields: MappedField[]): Record<string, string> {
  const values: Record<string, string> = {};
  for (const field of fields) {
    values[field.name] = field.kind === "select" && field.options?.[0] ? field.options[0].value : "";
  }
  return values;
}
