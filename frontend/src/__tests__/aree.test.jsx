import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import Lingue from "../i18n/Lingue";
import PaginaAree from "../aree/PaginaAree";

const AREE = [
  {
    id: "sc",
    nome: "Servizio Clienti e front office",
    descrizione: "Sportelli.",
    cartelle_brain: ["15-customer-service"],
    responsabili: [],
    prefissi_domande: ["SC"],
  },
];
const DOMANDE = [
  {
    id: "SC-01",
    domanda: "**Gli sportelli di Cascia sono attivi?**",
    perche: "Il sito li pubblica",
    note: ["sportelli", "manca"],
    percorsi: { sportelli: "15-customer-service/sportelli.md" },
  },
];
const NOTE = [
  { nota: "15-customer-service/sportelli.md", titolo: "Sportelli", stato: "active", aggiornata: "2026-10-12" },
];

function risposta(dati, status = 200) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(dati) });
}

function Dove() {
  const l = useLocation();
  return <p>{`${l.pathname}${l.search}`}</p>;
}

function monta() {
  render(
    <Lingue><MemoryRouter initialEntries={["/aree"]}>
      <Routes>
        <Route path="/aree" element={<PaginaAree />} />
        <Route path="/editor" element={<Dove />} />
      </Routes>
    </MemoryRouter></Lingue>,
  );
}

afterEach(() => vi.restoreAllMocks());

it("shows the open questions of the first area and opens a linked note", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    risposta(url === "/api/aree" ? AREE : url.endsWith("/domande") ? DOMANDE : NOTE),
  );
  monta();
  expect(await screen.findByText("Gli sportelli di Cascia sono attivi?")).toBeInTheDocument();
  expect(screen.getByText("Domande aperte (1)")).toBeInTheDocument();
  expect(screen.getByText("manca").tagName).toBe("SPAN");
  fireEvent.click(screen.getByRole("button", { name: "sportelli" }));
  expect(
    await screen.findByText("/editor?nota=15-customer-service%2Fsportelli.md"),
  ).toBeInTheDocument();
});

it("lists the area notes in their tab", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    risposta(url === "/api/aree" ? AREE : url.endsWith("/domande") ? DOMANDE : NOTE),
  );
  monta();
  fireEvent.mouseDown(await screen.findByRole("tab", { name: /Note \(1\)/ }));
  expect(await screen.findByText("Sportelli")).toBeInTheDocument();
});

it("shows the login error while reading is closed", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    url === "/api/aree"
      ? risposta(AREE)
      : risposta({ detail: "accesso non ancora attivo" }, 401),
  );
  monta();
  expect(await screen.findByText(/accesso non ancora attivo/)).toBeInTheDocument();
});
