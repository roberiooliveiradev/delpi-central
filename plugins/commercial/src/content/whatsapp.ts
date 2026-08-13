import whatsappContent from "./whatsapp.json";

export function buildWhatsAppGreeting(fullName: string): string {
  return whatsappContent.greeting.replace("{full_name}", fullName.trim());
}

export function buildWhatsAppUrl(e164: string, text: string): string {
  const digits = e164.replace(/\D/g, "");
  return `https://wa.me/${digits}?text=${encodeURIComponent(text)}`;
}
