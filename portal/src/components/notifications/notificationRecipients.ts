// src/components/notifications/notificationRecipients.ts

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;

export type ParsedRecipient =
  | { kind: "id"; value: string }
  | { kind: "email"; value: string };

export function tokenizeRecipientsInput(raw: string): string[] {
  return raw
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function parseRecipientsBulk(raw: string): {
  parsed: ParsedRecipient[];
  invalid: string[];
} {
  const parsed: ParsedRecipient[] = [];
  const invalid: string[] = [];
  const seen = new Set<string>();

  for (const token of tokenizeRecipientsInput(raw)) {
    const item = parseRecipientInput(token);
    if (!item) {
      invalid.push(token);
      continue;
    }

    const key = `${item.kind}:${item.value}`;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    parsed.push(item);
  }

  return { parsed, invalid };
}

export function parseRecipientInput(raw: string): ParsedRecipient | null {
  const value = raw.trim();
  if (!value) {
    return null;
  }

  if (UUID_RE.test(value)) {
    return { kind: "id", value: value.toLowerCase() };
  }

  if (EMAIL_RE.test(value)) {
    return { kind: "email", value: value.toLowerCase() };
  }

  return null;
}

export function normalizeRecipientList(values: string[]) {
  const userIds = new Set<string>();
  const emails = new Set<string>();

  for (const raw of values) {
    const parsed = parseRecipientInput(raw);
    if (!parsed) {
      continue;
    }

    if (parsed.kind === "id") {
      userIds.add(parsed.value);
    } else {
      emails.add(parsed.value);
    }
  }

  return {
    userIds: Array.from(userIds),
    emails: Array.from(emails),
  };
}
