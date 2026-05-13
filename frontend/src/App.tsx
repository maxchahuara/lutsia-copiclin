import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Consultation = {
  id: string;
  title: string;
  consent_confirmed: boolean;
};

type ClinicalNote = {
  resumen_breve: string;
  motivo_consulta: string;
  bloques_copiables: {
    resumen_para_medico: string;
    anamnesis_compacta: string;
  };
};

const apiBase = import.meta.env.DEV ? "/api" : "";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof detail.detail === "string" ? detail.detail : JSON.stringify(detail.detail));
  }
  return response.json() as Promise<T>;
}

function App() {
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [note, setNote] = useState<ClinicalNote | null>(null);
  const [status, setStatus] = useState("Listo para iniciar una consulta local.");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function runDemoFlow() {
    setBusy(true);
    setCopied(false);
    try {
      await api("/settings", {
        method: "PUT",
        body: JSON.stringify({ llm_provider: "mock", transcription_provider: "mock" }),
      });
      const created = await api<Consultation>("/consultations", {
        method: "POST",
        body: JSON.stringify({ title: "Consulta de prueba", consent_confirmed: true }),
      });
      setConsultation(created);
      await api(`/consultations/${created.id}/transcribe`, { method: "POST" });
      const generated = await api<ClinicalNote>(`/consultations/${created.id}/generate-note`, {
        method: "POST",
      });
      setNote(generated);
      setStatus("Demo local generado. En producción el médico debe revisar y editar antes de copiar.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Error desconocido");
    } finally {
      setBusy(false);
    }
  }

  async function copySummary() {
    if (!note) return;
    await navigator.clipboard.writeText(note.bloques_copiables.resumen_para_medico || note.resumen_breve);
    setCopied(true);
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">LUTSIA Copiloto Clínico</p>
        <h1>LUTSIA CopiClin</h1>
        <p>Copiloto local-first para transcribir consultas y preparar borradores clínicos copiables.</p>
        <strong>Borrador generado por IA. Revisar antes de usar. No es HCE ni herramienta diagnóstica.</strong>
      </section>

      <section className="card">
        <h2>Flujo vertical local</h2>
        <ol>
          <li>Crear consulta con consentimiento.</li>
          <li>Transcribir audio localmente o con proveedor configurado.</li>
          <li>Generar borrador clínico editable y copiable.</li>
        </ol>
        <button disabled={busy} onClick={runDemoFlow}>
          {busy ? "Procesando…" : "Probar demo local"}
        </button>
        <p className="status">{status}</p>
        {consultation && <p className="muted">Consulta local: {consultation.id}</p>}
      </section>

      <section className="card">
        <h2>Nota editable</h2>
        <textarea
          value={note?.bloques_copiables.resumen_para_medico || note?.resumen_breve || "Ejecuta la demo para generar un borrador."}
          onChange={(event) =>
            setNote((current) =>
              current
                ? {
                    ...current,
                    bloques_copiables: {
                      ...current.bloques_copiables,
                      resumen_para_medico: event.target.value,
                    },
                  }
                : current,
            )
          }
        />
        <button disabled={!note} onClick={copySummary}>Copiar resumen</button>
        {copied && <span> Copiado</span>}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
