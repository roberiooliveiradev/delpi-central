import { useMutation, useQuery } from "@tanstack/react-query";
import { ShieldAlert } from "lucide-react";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Server } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { formatDateTime } from "../../app/format";
import { ItpActionButton, ItpSectionCard, ItpTextAreaField } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { SECRET_WARNING } from "../../content/labels";
import { useInvalidateInventory } from "./ServerFormModal";

const NOTE_FIELD_LABELS = { body: "Nota" };

export function ServerNotesSection({ server }: { server: Server }) {
  const { capabilities, notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const canCreate = capabilities?.can_create_notes === true && !server.archived;
  const [body, setBody] = useState("");

  const notesQuery = useQuery({
    queryKey: queryKeys.notes(server.id),
    queryFn: ({ signal }) => itPortalApi.listNotes(server.id, signal),
  });

  const mutation = useMutation({
    mutationFn: (text: string) => itPortalApi.createNote(server.id, text),
    onSuccess: () => {
      setBody("");
      invalidate();
      notifySuccess("Nota registrada.");
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (body.trim()) mutation.mutate(body);
  };

  return (
    <ItpSectionCard
      title="Notas técnicas"
      subtitle="Registro cronológico; notas não podem ser editadas nem excluídas."
    >
      {canCreate ? (
        <form className="itp-form" onSubmit={submit} noValidate>
          <p className="itp-secret-warning" role="note">
            <ShieldAlert size={16} strokeWidth={1.75} aria-hidden="true" />
            <span>{SECRET_WARNING}</span>
          </p>
          <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={NOTE_FIELD_LABELS} />
          <ItpTextAreaField
            label="Nova nota"
            value={body}
            onChange={setBody}
            rows={3}
            maxLength={4000}
            fullWidth
            disabled={mutation.isPending}
          />
          <div className="itp-form-actions">
            <ItpActionButton variant="primary" type="submit" disabled={mutation.isPending || !body.trim()}>
              {mutation.isPending ? "Registrando…" : "Registrar nota"}
            </ItpActionButton>
          </div>
        </form>
      ) : null}

      {notesQuery.isPending ? (
        <LoadingBlock title="Carregando notas" />
      ) : notesQuery.error ? (
        <QueryErrorState error={toApiError(notesQuery.error)} onRetry={() => void notesQuery.refetch()} />
      ) : notesQuery.data.length === 0 ? (
        <p className="itp-muted">Nenhuma nota registrada.</p>
      ) : (
        <ol className="itp-timeline" aria-label="Notas técnicas">
          {notesQuery.data.map((note) => (
            <li key={note.id} className="itp-timeline-item">
              <p className="itp-timeline-meta">
                <strong>{note.author_name}</strong> · <time dateTime={note.created_at}>{formatDateTime(note.created_at)}</time>
              </p>
              <p className="itp-prewrap">{note.body}</p>
            </li>
          ))}
        </ol>
      )}
    </ItpSectionCard>
  );
}
