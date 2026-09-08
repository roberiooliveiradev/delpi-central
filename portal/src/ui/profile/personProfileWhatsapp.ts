export type WhatsappSource = "phone" | "mobile" | null;

export function resolveWhatsappSource(data: {
  phone_e164?: string | null;
  mobile_e164?: string | null;
  whatsapp_e164?: string | null;
} | null | undefined): WhatsappSource {
  const whatsapp = (data?.whatsapp_e164 || "").trim();
  if (!whatsapp) return null;
  const phone = (data?.phone_e164 || "").trim();
  const mobile = (data?.mobile_e164 || "").trim();
  if (phone && phone === whatsapp) return "phone";
  if (mobile && mobile === whatsapp) return "mobile";
  if (mobile) return "mobile";
  if (phone) return "phone";
  return "mobile";
}

export function resolveWhatsappE164(
  source: WhatsappSource,
  phone: string,
  mobile: string,
): string | null {
  if (source === "phone") {
    const value = phone.trim();
    return value || null;
  }
  if (source === "mobile") {
    const value = mobile.trim();
    return value || null;
  }
  return null;
}
