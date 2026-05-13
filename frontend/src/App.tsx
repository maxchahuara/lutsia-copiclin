import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App() {
  const [copied, setCopied] = useState(false);
  const summary = "Borrador generado por IA. Revisar antes de usar. Paciente refiere tos desde hace tres días; niega fiebre.";
  async function copySummary() {
    await navigator.clipboard.writeText(summary);
    setCopied(true);
  }
  return <main className="shell">
    <section className="hero">
      <p className="eyebrow">LUTSIA Copiloto Clínico</p>
      <h1>LUTSIA CopiClin</h1>
      <p>Copiloto local-first para transcribir consultas y preparar borradores clínicos copiables.</p>
      <strong>Borrador generado por IA. Revisar antes de usar.</strong>
    </section>
    <section className="card">
      <h2>Prototipo vertical</h2>
      <ol>
        <li>Crear consulta</li><li>Consentimiento</li><li>Grabar/cargar audio</li><li>Transcribir</li><li>Generar nota editable</li>
      </ol>
      <textarea defaultValue={summary} />
      <button onClick={copySummary}>Copiar resumen</button>{copied && <span> Copiado</span>}
    </section>
  </main>
}

createRoot(document.getElementById("root")!).render(<App />);
