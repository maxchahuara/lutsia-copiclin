import React, { useEffect, useState } from "react";
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

type SetupStep = {
  id: string;
  title: string;
  ok: boolean;
  required: boolean;
  detail: string;
  action?: {
    command?: string;
    environment?: Record<string, string>;
    notes?: string[];
  };
};

type SetupStatus = {
  setup_completed: boolean;
  ready_for_real_use: boolean;
  can_run_demo: boolean;
  required_steps: SetupStep[];
  optional_steps: SetupStep[];
  warnings: string[];
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

function StepCard({ step }: { step: SetupStep }) {
  const command = step.action?.command;
  const env = step.action?.environment || {};
  const fullCommand = command
    ? `${Object.entries(env).map(([key, value]) => `${key}=${JSON.stringify(value)}`).join(" ")}${Object.keys(env).length ? " " : ""}${command}`
    : "";

  return (
    <article className={`step ${step.ok ? "ok" : "missing"}`}>
      <div className="step-head">
        <strong>{step.ok ? "✓" : "!"} {step.title}</strong>
        <span>{step.required ? "requerido" : "opcional"}</span>
      </div>
      <p>{step.detail}</p>
      {fullCommand && <code>{fullCommand}</code>}
      {step.action?.notes?.map((note) => <p className="muted" key={note}>{note}</p>)}
    </article>
  );
}

function App() {
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [note, setNote] = useState<ClinicalNote | null>(null);
  const [status, setStatus] = useState("Verificando configuración inicial…");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showWorkspace, setShowWorkspace] = useState(false);

  async function refreshSetup() {
    const payload = await api<SetupStatus>("/setup/status");
    setSetup(payload);
    setShowWorkspace(payload.ready_for_real_use || payload.setup_completed);
    setStatus(payload.ready_for_real_use ? "Configuración lista para uso real." : "Faltan pasos de configuración antes del uso real.");
  }

  useEffect(() => {
    refreshSetup().catch((error) => setStatus(error instanceof Error ? error.message : "No se pudo verificar configuración."));
  }, []);

  async function markSetupReviewed() {
    setBusy(true);
    try {
      await api("/setup/complete", { method: "POST" });
      await refreshSetup();
      setShowWorkspace(true);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo completar configuración.");
    } finally {
      setBusy(false);
    }
  }

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

  const setupMissing = setup && !setup.ready_for_real_use;

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">LUTSIA Copiloto Clínico</p>
        <h1>LUTSIA CopiClin</h1>
        <p>Copiloto local-first para transcribir consultas y preparar borradores clínicos copiables.</p>
        <strong>Borrador generado por IA. Revisar antes de usar. No es HCE ni herramienta diagnóstica.</strong>
      </section>

      {setup && setupMissing && (
        <section className="card warning-card">
          <h2>Configuración inicial obligatoria</h2>
          <p>Antes de usar CopiClin en serio, verifica cuenta Codex/OpenAI y transcripción local.</p>
          {setup.warnings.map((warning) => <p className="warning" key={warning}>{warning}</p>)}
          <div className="steps">
            {setup.required_steps.map((step) => <StepCard key={step.id} step={step} />)}
            {setup.optional_steps.map((step) => <StepCard key={step.id} step={step} />)}
          </div>
          <button disabled={busy} onClick={refreshSetup}>Volver a verificar</button>
          <button disabled={busy} onClick={markSetupReviewed}>Entiendo, continuar solo para demo/pruebas</button>
          <p className="muted">CopiClin no marcará “uso real listo” hasta que los pasos requeridos estén OK.</p>
        </section>
      )}

      {showWorkspace && (
        <>
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
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
