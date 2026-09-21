import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { alertQueueBemClasses } from "../feedback/AlertQueue";
import { EventsSection, createDashboardEventsSection } from "./EventsSection";
import { sectionCardPacBemClasses } from "./SectionCard";

const LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const CLASS_NAMES = {
  section: sectionCardPacBemClasses("cm"),
  queue: alertQueueBemClasses("cm"),
};

describe("EventsSection", () => {
  it("omite a seção sem items nem children", () => {
    const { container } = render(
      <EventsSection
        title="Eventos e interações"
        items={[]}
        classNames={CLASS_NAMES}
        labels={LABELS}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renderiza um evento com ação", () => {
    const onAction = vi.fn();
    render(
      <EventsSection
        title="Eventos e interações"
        items={[
          {
            id: "due",
            title: "Revisões a vencer",
            description: "3 revisões nos próximos 90 dias",
            actionLabel: "Abrir",
            onAction,
          },
        ]}
        classNames={CLASS_NAMES}
        labels={LABELS}
        listAriaLabel="Eventos e interações pendentes"
      />,
    );
    expect(screen.getByText("Eventos e interações")).toBeTruthy();
    expect(screen.getByText("Revisões a vencer")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renderiza vários eventos e children opcionais", () => {
    render(
      <EventsSection
        title="Eventos e interações"
        items={[
          { id: "a", title: "Primeiro" },
          { id: "b", title: "Segundo" },
        ]}
        classNames={CLASS_NAMES}
        labels={LABELS}
      >
        <p>Fila extra</p>
      </EventsSection>,
    );
    expect(screen.getByText("Primeiro")).toBeTruthy();
    expect(screen.getByText("Segundo")).toBeTruthy();
    expect(screen.getByText("Fila extra")).toBeTruthy();
  });

  it("mostra empty quando omitWhenEmpty=false", () => {
    render(
      <EventsSection
        title="Eventos e interações"
        items={[]}
        omitWhenEmpty={false}
        emptyMessage="Nenhum evento"
        classNames={CLASS_NAMES}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("Nenhum evento")).toBeTruthy();
  });

  it("createDashboardEventsSection monta sem classNames manuais", () => {
    const Section = createDashboardEventsSection({ prefix: "ds", labels: LABELS });
    render(
      <Section
        title="Eventos e interações"
        items={[{ id: "one", title: "Sinal real" }]}
      />,
    );
    expect(screen.getByText("Sinal real")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-section-card")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-alert-queue")).toBeTruthy();
  });
});
