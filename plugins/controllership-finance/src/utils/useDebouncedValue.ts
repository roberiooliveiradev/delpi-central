import { useEffect, useState } from "react";

/**
 * Retorna `value` atrasado por `delayMs` — reinicia a contagem a cada
 * mudança. Usado para filtros digitáveis em consulta automática.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
