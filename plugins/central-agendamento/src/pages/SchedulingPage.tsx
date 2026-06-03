import { useMemo, useState } from "react";
import { CalendarPlus, RefreshCw, Settings2 } from "lucide-react";
import type { View } from "react-big-calendar";
import type { SlotInfo } from "react-big-calendar";
import { isSameDay } from "date-fns";

import {
  cancelBooking,
  createBooking,
  createResource,
  fetchResources,
  updateResource,
  type SchedulingResource,
} from "../api/schedulingApi";
import { BookingCalendar, type CalendarEvent } from "../components/BookingCalendar";
import { BookingDetailModal } from "../components/BookingDetailModal";
import { BookingModal } from "../components/BookingModal";
import { ResourceAdminPanel } from "../components/ResourceAdminPanel";
import { ResourceFormModal } from "../components/ResourceFormModal";
import { ResourceSidebar } from "../components/ResourceSidebar";
import { SchedulingPageHeader } from "../components/SchedulingPageHeader";
import { BRANCH_LABELS, branchFromPathname } from "../constants/scheduling";
import { useBranchPermission } from "../hooks/useBranchPermission";
import { useSchedulingData } from "../hooks/useSchedulingData";

type Props = {
  pathname?: string;
};

type ActiveView = "calendar" | "admin";

export function SchedulingPage({ pathname }: Props) {
  const branch = branchFromPathname(pathname);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarView, setCalendarView] = useState<View>("week");
  const [activeView, setActiveView] = useState<ActiveView>("calendar");
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [resourceModalOpen, setResourceModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [slotSelection, setSlotSelection] = useState<{ start: Date; end: Date } | null>(null);
  const [selectedResourceId, setSelectedResourceId] = useState<string | undefined>();
  const [editingResource, setEditingResource] = useState<SchedulingResource | null>(null);
  const [adminResources, setAdminResources] = useState<SchedulingResource[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const { canManage, currentUserId } = useBranchPermission(branch);
  const {
    resources,
    bookings,
    filteredResources,
    loading,
    error,
    selectedTypes,
    selectedResourceIds,
    toggleType,
    toggleResource,
    clearFilters,
    reload,
  } = useSchedulingData(branch, currentDate);

  const bookingsToday = useMemo(
    () => bookings.filter((booking) => isSameDay(new Date(booking.start_at), new Date())),
    [bookings],
  );

  async function loadAdminResources() {
    if (!branch) return;
    const data = await fetchResources(branch, false);
    setAdminResources(data);
  }

  async function openAdminView() {
    setActiveView("admin");
    await loadAdminResources();
  }

  function openBookingModal(start?: Date, end?: Date, resourceId?: string) {
    setSlotSelection(start && end ? { start, end } : null);
    setSelectedResourceId(resourceId);
    setBookingModalOpen(true);
  }

  function handleSelectSlot(slot: SlotInfo) {
    openBookingModal(slot.start, slot.end);
  }

  function handleSelectEvent(event: CalendarEvent) {
    setSelectedEvent(event);
    setDetailModalOpen(true);
  }

  async function handleCreateBooking(payload: {
    resource_id: string;
    title: string;
    notes?: string;
    start_at: string;
    end_at: string;
  }) {
    if (!branch) return;
    setActionLoading(true);
    try {
      await createBooking({ branch_code: branch, ...payload });
      setSuccess("Reserva confirmada com sucesso.");
      await reload();
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCancelBooking() {
    if (!selectedEvent) return;
    setActionLoading(true);
    try {
      await cancelBooking(selectedEvent.id);
      setSuccess("Reserva cancelada.");
      await reload();
    } finally {
      setActionLoading(false);
    }
  }

  async function handleSaveResource(payload: {
    name: string;
    resource_type: SchedulingResource["resource_type"];
    description?: string;
    capacity?: number;
    metadata?: Record<string, unknown>;
  }) {
    if (!branch) return;
    setActionLoading(true);
    try {
      if (editingResource) {
        await updateResource(editingResource.id, payload);
        setSuccess("Recurso atualizado.");
      } else {
        await createResource({ branch_code: branch, ...payload });
        setSuccess("Recurso cadastrado.");
      }
      await Promise.all([reload(), loadAdminResources()]);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleToggleActive(resource: SchedulingResource) {
    setActionLoading(true);
    try {
      await updateResource(resource.id, { active: !resource.active });
      setSuccess(resource.active ? "Recurso desativado." : "Recurso reativado.");
      await Promise.all([reload(), loadAdminResources()]);
    } finally {
      setActionLoading(false);
    }
  }

  if (!branch) {
    return (
      <div className="ca-app">
        <div className="ca-alert ca-alert--error">
          Filial inválida. Use uma rota como /apps/central-agendamento/filial-es.
        </div>
      </div>
    );
  }

  const canCancelSelected =
    Boolean(selectedEvent) &&
    (canManage || selectedEvent?.bookedByUserId === currentUserId);

  return (
    <div className="ca-app">
      <SchedulingPageHeader
        eyebrow={BRANCH_LABELS[branch]}
        title="Central de Agendamento"
        subtitle="Consulte disponibilidade e reserve salas, treinamentos e veículos."
        actions={
          <>
            <button
              type="button"
              className={`ca-btn ca-btn--ghost ${activeView === "calendar" ? "ca-btn--active" : ""}`}
              onClick={() => setActiveView("calendar")}
            >
              Calendário
            </button>
            {canManage ? (
              <button
                type="button"
                className={`ca-btn ca-btn--ghost ${activeView === "admin" ? "ca-btn--active" : ""}`}
                onClick={() => void openAdminView()}
              >
                <Settings2 size={16} />
                Gerenciar recursos
              </button>
            ) : null}
            <button type="button" className="ca-btn ca-btn--ghost" onClick={() => void reload()}>
              <RefreshCw size={16} className={loading ? "ca-spin" : ""} />
              Atualizar
            </button>
            <button
              type="button"
              className="ca-btn ca-btn--primary"
              onClick={() => openBookingModal()}
            >
              <CalendarPlus size={16} />
              Nova reserva
            </button>
          </>
        }
      />

      {success ? (
        <div className="ca-alert ca-alert--success">
          {success}
          <button type="button" className="ca-link-btn" onClick={() => setSuccess(null)}>
            Fechar
          </button>
        </div>
      ) : null}

      {error ? <div className="ca-alert ca-alert--error">{error}</div> : null}

      {activeView === "calendar" ? (
        <div className="ca-layout">
          <ResourceSidebar
            resources={filteredResources}
            bookingsCountToday={bookingsToday.length}
            selectedTypes={selectedTypes}
            selectedResourceIds={selectedResourceIds}
            onToggleType={toggleType}
            onToggleResource={toggleResource}
            onClearFilters={clearFilters}
          />

          <div className="ca-main-panel">
            {loading && resources.length === 0 ? (
              <div className="ca-loading">Carregando calendário...</div>
            ) : (
              <BookingCalendar
                bookings={bookings}
                resources={filteredResources}
                currentDate={currentDate}
                view={calendarView}
                onViewChange={setCalendarView}
                onNavigate={setCurrentDate}
                onSelectEvent={handleSelectEvent}
                onSelectSlot={handleSelectSlot}
              />
            )}
          </div>
        </div>
      ) : (
        <ResourceAdminPanel
          resources={adminResources}
          onCreate={() => {
            setEditingResource(null);
            setResourceModalOpen(true);
          }}
          onEdit={(resource) => {
            setEditingResource(resource);
            setResourceModalOpen(true);
          }}
          onToggleActive={handleToggleActive}
        />
      )}

      <BookingModal
        open={bookingModalOpen}
        branch={branch}
        resources={resources}
        defaultResourceId={selectedResourceId}
        defaultStart={slotSelection?.start}
        defaultEnd={slotSelection?.end}
        loading={actionLoading}
        onClose={() => setBookingModalOpen(false)}
        onSubmit={handleCreateBooking}
      />

      <BookingDetailModal
        open={detailModalOpen}
        event={selectedEvent}
        canCancel={canCancelSelected}
        loading={actionLoading}
        onClose={() => setDetailModalOpen(false)}
        onCancel={handleCancelBooking}
      />

      <ResourceFormModal
        open={resourceModalOpen}
        branch={branch}
        resource={editingResource}
        loading={actionLoading}
        onClose={() => setResourceModalOpen(false)}
        onSubmit={handleSaveResource}
      />
    </div>
  );
}
