import { useState } from "react";
import { ActionButton, BackLink } from "@delpi/plugin-ui/index";

import { createReport, type TravelAccess } from "../api/travelExpensesApi";
import { helpTooltips } from "../content/helpTooltips";
import { navigateTravel } from "../hooks/useTravelRouterPath";
import { writableUnits } from "../security/travelAccess";
import {
  TravelFormActions,
  TravelFormGrid,
  TravelPageHeader,
  TravelPageNotices,
  TravelSectionCard,
} from "../ui/travelUi";

export function NewReportPage({ access }: { access: TravelAccess }) {
  const units = writableUnits(access);
  const [unitCode, setUnitCode] = useState(units[0]?.id || "");
  const [destination, setDestination] = useState("");
  const [purpose, setPurpose] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    if (!unitCode) {
      setError("Selecione a filial da viagem.");
      return;
    }
    setBusy(true);
    try {
      const created = await createReport({
        unitCode,
        destination,
        purpose,
        periodStart: periodStart || null,
        periodEnd: periodEnd || null,
      });
      navigateTravel(`/apps/travel-expenses/reports/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a prestação.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="te-page-stack">
      <TravelPageHeader
        title="Nova prestação"
        subtitle={helpTooltips.hub}
        nav={<BackLink onClick={() => navigateTravel("/apps/travel-expenses")}>Início</BackLink>}
      />
      <TravelPageNotices error={error} onDismissError={() => setError(null)} />
      <TravelSectionCard title="Cabeçalho da viagem">
        <TravelFormGrid>
          <label className="te-field">
            Filial
            <select
              value={unitCode}
              onChange={(event) => setUnitCode(event.target.value as "01" | "02")}
            >
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.label}
                </option>
              ))}
            </select>
          </label>
          <label className="te-field">
            Destino
            <input
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              placeholder={helpTooltips.destination}
            />
          </label>
          <label className="te-field">
            Início
            <input type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} />
          </label>
          <label className="te-field">
            Fim
            <input type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} />
          </label>
          <label className="te-field te-field--wide">
            Motivo
            <textarea value={purpose} onChange={(event) => setPurpose(event.target.value)} rows={3} />
          </label>
        </TravelFormGrid>
        <TravelFormActions>
          <ActionButton variant="primary" onClick={() => void onSubmit()} disabled={busy || !access.canWrite}>
            Criar prestação
          </ActionButton>
        </TravelFormActions>
      </TravelSectionCard>
    </div>
  );
}
