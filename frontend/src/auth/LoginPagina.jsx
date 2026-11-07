import { useState } from "react";
import { Alert, Button, Card, CardBody, CardHeader, CardTitle, Field, Input } from "@suite/design-system";
import { useT } from "../i18n/useT";
import { useAuth } from "./authContext";

export default function LoginPagina() {
  const { login } = useAuth();
  const t = useT();
  const [utente, setUtente] = useState("");
  const [password, setPassword] = useState("");
  const [errore, setErrore] = useState("");
  const [invio, setInvio] = useState(false);

  const accedi = async (e) => {
    e.preventDefault();
    setErrore("");
    setInvio(true);
    try {
      await login(utente, password);
    } catch (err) {
      // 404: no local auth provider, access goes through the Life gate.
      setErrore(err.status === 404 ? t("auth.gateOnly") : err.message);
      setInvio(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t("app.name")}</CardTitle>
          <p className="text-sm text-muted">{t("auth.subtitle")}</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={accedi} className="flex flex-col gap-4">
            <Field label={t("auth.login")} htmlFor="login">
              <Input value={utente} onChange={(e) => setUtente(e.target.value)} autoComplete="username" />
            </Field>
            <Field label={t("auth.password")} htmlFor="password">
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </Field>
            {errore && <Alert variant="danger">{errore}</Alert>}
            <Button type="submit" loading={invio} className="w-full">
              {t("auth.submit")}
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
