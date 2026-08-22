export const PIX_KEY_TYPES = [
  { id: "cpf", label: "CPF" },
  { id: "cnpj", label: "CNPJ" },
  { id: "email", label: "E-mail" },
  { id: "phone", label: "Telefone" },
  { id: "random", label: "Chave aleatória" },
] as const;

export type PixKeyTypeId = (typeof PIX_KEY_TYPES)[number]["id"];

export const PIX_KEY_TYPE_LABELS: Record<PixKeyTypeId, string> = {
  cpf: "CPF",
  cnpj: "CNPJ",
  email: "E-mail",
  phone: "Telefone",
  random: "Chave aleatória",
};

export function formatPixKeyDisplay(keyType?: string | null, keyValue?: string | null) {
  const type = String(keyType || "").trim();
  const value = String(keyValue || "").trim();
  if (!type || !value) return null;
  const label = PIX_KEY_TYPE_LABELS[type as PixKeyTypeId] || type;
  return { label, value };
}
