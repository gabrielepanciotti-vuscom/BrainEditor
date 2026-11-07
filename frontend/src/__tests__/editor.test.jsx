import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import Lingue from "../i18n/Lingue";
import EditorNota from "../editor/EditorNota";

const NOTA = {
  nota: "01-mercato/prezzo.md",
  contenuto: "---\ntitle: Prezzo\n---\n",
  stato: "active",
  branch: null,
};
const NON_VALIDA = {
  valida: false,
  problemi: [{ regola: "wikilink", messaggio: "1 wikilink verso altre note (minimo 3)" }],
  wikilink_validi: 1,
  righe_corpo: 4,
  classification: "public",
};

function risposta(dati, status = 200) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(dati) });
}

afterEach(() => vi.restoreAllMocks());

it("opens a note, shows the failing rule and blocks the save", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    url.startsWith("/api/validazione/") ? risposta(NON_VALIDA) : risposta(NOTA),
  );
  render(
    <Lingue><MemoryRouter>
      <EditorNota />
    </MemoryRouter></Lingue>,
  );
  fireEvent.change(screen.getByRole("textbox"), { target: { value: NOTA.nota } });
  fireEvent.click(screen.getByRole("button", { name: "Apri" }));

  expect(await screen.findByText(/minimo 3/)).toBeInTheDocument();
  expect(screen.getByText("Versione pubblicata · stato active")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Salva in revisione" })).toBeDisabled();
  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/validazione/01-mercato/prezzo.md",
      expect.objectContaining({ method: "POST" }),
    ),
  );
});

it("shows the login error when reading is not allowed yet", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() =>
    risposta({ detail: "accesso non ancora attivo" }, 401),
  );
  render(
    <Lingue><MemoryRouter>
      <EditorNota />
    </MemoryRouter></Lingue>,
  );
  fireEvent.change(screen.getByRole("textbox"), { target: { value: NOTA.nota } });
  fireEvent.click(screen.getByRole("button", { name: "Apri" }));
  expect(await screen.findByText(/accesso non ancora attivo/)).toBeInTheDocument();
});

it("opens the note passed in the address", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    url.startsWith("/api/validazione/") ? risposta(NON_VALIDA) : risposta(NOTA),
  );
  render(
    <Lingue><MemoryRouter initialEntries={[`/editor?nota=${encodeURIComponent(NOTA.nota)}`]}>
      <EditorNota />
    </MemoryRouter></Lingue>,
  );
  expect(await screen.findByText("Versione pubblicata · stato active")).toBeInTheDocument();
});
