const IDEMPOTENCY_PATTERN = /^[A-Za-z0-9._:-]{8,200}$/;

export function readJson<T>(storage: Storage, key: string): T | null {
  const raw = storage.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function writeJson(storage: Storage, key: string, value: unknown): void {
  storage.setItem(key, JSON.stringify(value));
}

export function idempotencyKey(storage: Storage, key: string, create: () => string): string {
  const current = storage.getItem(key);
  if (current && IDEMPOTENCY_PATTERN.test(current)) return current;
  const next = create();
  if (!IDEMPOTENCY_PATTERN.test(next)) {
    throw new Error("Idempotency-Key inválida.");
  }
  storage.setItem(key, next);
  return next;
}

export function clearKey(storage: Storage, key: string): void {
  storage.removeItem(key);
}
