import type { ApiError } from "../api/httpClient";
import { ItpStateBanner } from "./itPortalUi";

/** Erros de validação devolvidos pela BFF (campo → mensagem), anunciados ao leitor de tela. */
export function FormErrors({
  error,
  fieldLabels,
}: {
  error: ApiError | null;
  fieldLabels: Record<string, string>;
}) {
  if (!error) return null;
  const fields = Object.entries(error.fieldErrors);
  return (
    <ItpStateBanner variant="error">
      <div role="alert" className="itp-state-content">
        <p className="itp-state-title">{error.message}</p>
        {fields.length > 0 ? (
          <ul className="itp-form-errors">
            {fields.map(([field, message]) => (
              <li key={field}>
                <strong>{fieldLabels[field] ?? field}:</strong> {message}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </ItpStateBanner>
  );
}
