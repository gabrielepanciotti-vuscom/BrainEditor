import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "../App";
import { getToken, setToken } from "../auth/sessione";

const ME = {
  nome: "Alice Example",
  email: "alice@example.com",
  ruoli: ["manager"],
  is_admin: false,
};

function risposta(dati, status = 200) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(dati) });
}

const bearer = (init) => init?.headers?.Authorization;

afterEach(() => {
  vi.restoreAllMocks();
  window.sessionStorage.clear();
});

async function compila(login, password) {
  await waitFor(() => expect(document.querySelector("form")).not.toBeNull());
  const [utente, segreto] = document.querySelectorAll("form input");
  fireEvent.change(utente, { target: { value: login } });
  fireEvent.change(segreto, { target: { value: password } });
  fireEvent.submit(document.querySelector("form"));
}

it("opens the portal with a stored valid token", async () => {
  setToken("tok");
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url, init) =>
    url === "/api/auth/me" && bearer(init) === "Bearer tok" ? risposta(ME) : risposta([]),
  );
  render(<App />);
  expect((await screen.findAllByText("Panoramica")).length).toBeGreaterThan(0);
  expect(fetchMock.mock.calls.some(([u]) => u.includes("/sso/"))).toBe(false);
});

it("on 401 exchanges the SSO session and enters without the login form", async () => {
  setToken("scaduto");
  vi.spyOn(globalThis, "fetch").mockImplementation((url, init) => {
    if (url === "/api/auth/sso/scambia") return risposta({ access_token: "sso-tok" });
    if (url === "/api/auth/me")
      return bearer(init) === "Bearer sso-tok" ? risposta(ME) : risposta({ detail: "no" }, 401);
    return risposta([]);
  });
  render(<App />);
  expect((await screen.findAllByText("Panoramica")).length).toBeGreaterThan(0);
  expect(getToken()).toBe("sso-tok");
});

it("asks for the login, then opens the portal with the bearer token", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url, init) => {
    if (url === "/api/auth/sso/scambia") return risposta({}, 404);
    if (url === "/api/auth/login") return risposta({ access_token: "tok", expires_in_minutes: 480 });
    if (url === "/api/auth/me")
      return bearer(init) === "Bearer tok" ? risposta(ME) : risposta({ detail: "no" }, 401);
    return risposta([]);
  });
  render(<App />);
  await compila("alice", "segreta");
  await waitFor(() => expect(getToken()).toBe("tok"));
  expect((await screen.findAllByText("Panoramica")).length).toBeGreaterThan(0);
  const me = fetchMock.mock.calls.filter(([u]) => u === "/api/auth/me").pop();
  expect(bearer(me[1])).toBe("Bearer tok");
});

it("shows the API refusal and stays on the login", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    url === "/api/auth/login"
      ? risposta({ detail: "Credenziali non valide" }, 401)
      : risposta({ detail: "no" }, url.includes("/sso/") ? 404 : 401),
  );
  render(<App />);
  await compila("alice", "sbagliata");
  expect(await screen.findByText("Credenziali non valide")).toBeInTheDocument();
  expect(getToken()).toBeNull();
});

it("explains the gate when the login endpoint does not exist (404)", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) =>
    risposta({ detail: "Not Found" }, url === "/api/auth/me" ? 401 : 404),
  );
  render(<App />);
  await compila("alice", "segreta");
  expect(await screen.findByText(/cancello Life/)).toBeInTheDocument();
});
