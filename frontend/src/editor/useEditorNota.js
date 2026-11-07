import { useCallback, useEffect, useState } from "react";
import { chiama } from "../auth/api";

const RITARDO_VALIDAZIONE_MS = 400;

const urlNota = (base, nota) => `${base}/${nota.split("/").map(encodeURIComponent).join("/")}`;

/** Load, live-validate and save one brain note (path relative to brain/). */
export function useEditorNota() {
  const [nota, setNota] = useState("");
  const [contenuto, setContenuto] = useState("");
  const [info, setInfo] = useState(null);
  const [esito, setEsito] = useState(null);
  const [caricamento, setCaricamento] = useState(false);
  const [salvataggio, setSalvataggio] = useState(false);
  const [errore, setErrore] = useState(null);
  const [commit, setCommit] = useState(null);

  const apri = useCallback(async (percorso) => {
    setCaricamento(true);
    setErrore(null);
    setCommit(null);
    try {
      const dati = await chiama(urlNota("/api/note", percorso));
      setNota(dati.nota);
      setContenuto(dati.contenuto);
      setInfo({ stato: dati.stato, branch: dati.branch });
    } catch (e) {
      setErrore(e.message);
    } finally {
      setCaricamento(false);
    }
  }, []);

  // Live check while typing: the same rules the save enforces.
  useEffect(() => {
    if (!nota) return undefined;
    let annullato = false;
    const t = setTimeout(async () => {
      try {
        const dati = await chiama(urlNota("/api/validazione", nota), {
          method: "POST",
          body: JSON.stringify({ contenuto }),
        });
        if (!annullato) setEsito(dati);
      } catch (e) {
        if (!annullato) setErrore(e.message);
      }
    }, RITARDO_VALIDAZIONE_MS);
    return () => {
      annullato = true;
      clearTimeout(t);
    };
  }, [nota, contenuto]);

  const salva = useCallback(
    async (messaggio) => {
      setSalvataggio(true);
      setErrore(null);
      try {
        const dati = await chiama(urlNota("/api/note", nota), {
          method: "PUT",
          body: JSON.stringify({ contenuto, messaggio }),
        });
        setCommit(dati);
        setInfo({ stato: dati.stato, branch: dati.branch });
      } catch (e) {
        setErrore(e.message);
        if (e.problemi.length) setEsito((x) => ({ ...x, valida: false, problemi: e.problemi }));
      } finally {
        setSalvataggio(false);
      }
    },
    [nota, contenuto],
  );

  return {
    nota,
    contenuto,
    setContenuto,
    info,
    esito,
    caricamento,
    salvataggio,
    errore,
    commit,
    apri,
    salva,
  };
}
