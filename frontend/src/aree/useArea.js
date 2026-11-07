import { useEffect, useState } from "react";
import { chiama as leggi } from "../auth/api";

/** Areas of the questionnaire; the first one is selected by default. */
export function useAree() {
  const [aree, setAree] = useState([]);
  const [errore, setErrore] = useState(null);
  useEffect(() => {
    leggi("/api/aree")
      .then(setAree)
      .catch((e) => setErrore(e.message));
  }, []);
  return { aree, errore };
}

/** Notes and open questions of one area. */
export function useArea(areaId) {
  const [note, setNote] = useState([]);
  const [domande, setDomande] = useState([]);
  const [caricamento, setCaricamento] = useState(false);
  const [errore, setErrore] = useState(null);

  useEffect(() => {
    if (!areaId) return undefined;
    let annullato = false;
    setCaricamento(true);
    setErrore(null);
    Promise.all([leggi(`/api/aree/${areaId}/note`), leggi(`/api/aree/${areaId}/domande`)])
      .then(([n, d]) => {
        if (annullato) return;
        setNote(n);
        setDomande(d);
      })
      .catch((e) => {
        if (annullato) return;
        setNote([]);
        setDomande([]);
        setErrore(e.message);
      })
      .finally(() => !annullato && setCaricamento(false));
    return () => {
      annullato = true;
    };
  }, [areaId]);

  return { note, domande, caricamento, errore };
}
