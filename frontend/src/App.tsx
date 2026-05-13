import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Patient = {
  id: string;
  full_name: string;
  identifier?: string | null;
  birth_date?: string | null;
  contact?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

type Consultation = {
  id: string;
  title: string;
  consent_confirmed: boolean;
  patient_label?: string | null;
  patient_id?: string | null;
  status?: string;
  created_at: string;
  updated_at: string;
};

type TranscriptSegment = {
  id: string;
  speaker_label: string;
  start_time: number;
  end_time: number;
  text: string;
};

type Transcript = {
  provider: string;
  language: string;
  segments: TranscriptSegment[];
  quality_warnings?: string[];
};

type ClinicalNote = {
  metadata?: {
    quality_warnings?: string[];
    missing_information?: string[];
  };
  resumen_breve: string;
  motivo_consulta: string;
  anamnesis: {
    enfermedad_actual: string;
    antecedentes_personales: string;
    medicamentos_habituales: string;
    alergias: string;
    revision_por_sistemas: string;
  };
  examen_fisico_mencionado: string;
  resultados_mencionados: string;
  plan_mencionado: {
    medicacion: string[];
    examenes: string[];
    educacion: string[];
    seguimiento: string;
  };
  pendientes: string[];
  incertidumbres: string[];
  bloques_copiables: {
    resumen_para_medico: string;
    anamnesis_compacta: string;
    soap?: {
      subjetivo?: string;
      objetivo?: string;
      analisis?: string;
      plan?: string;
    };
  };
};

type AuthStatus = {
  available: boolean;
  logged_in: boolean;
  detail: string;
};

type SetupStatus = {
  setup_completed: boolean;
  ready_for_real_use: boolean;
  codex: AuthStatus;
};

type WhisperModel = {
  id: string;
  name: string;
  installed: boolean;
  selected: boolean;
  speed: string;
  quality: string;
};

type ModelsResponse = {
  selected: string;
  models: WhisperModel[];
};

type LoginSession = {
  session_id: string;
  message: string;
  auth_url: string | null;
  user_code: string | null;
  expires_in_minutes: number;
  status: string;
  logged_in: boolean;
};

type Section = "home" | "patients" | "capture" | "notes" | "settings";
type ProcessStage = "idle" | "transcribing" | "organizing";

const apiBase = import.meta.env.DEV ? "/api" : "";

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatApiError(detail.detail, response.status));
  }
  return response.json() as Promise<T>;
}

function formatApiError(detail: unknown, status: number) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Solicitud incompleta. Revisa los datos enviados o el archivo de audio.";
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message?: unknown }).message || "No se pudo completar la solicitud.");
  }
  return `No se pudo completar la solicitud (${status}).`;
}

function StatusPill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

function Brand() {
  return (
    <div className="brand-mark compact">
      <span>LC</span>
      <div>
        <strong>LUTSIA CopiCLin</strong>
        <small>Copiloto Clínico</small>
      </div>
    </div>
  );
}

function App() {
  const [section, setSection] = useState<Section>("home");
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [models, setModels] = useState<WhisperModel[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [currentConsultation, setCurrentConsultation] = useState<Consultation | null>(null);
  const [selectedNoteConsultationId, setSelectedNoteConsultationId] = useState("");
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [note, setNote] = useState<ClinicalNote | null>(null);
  const [status, setStatus] = useState("Preparando LUTSIA CopiCLin...");
  const [processStage, setProcessStage] = useState<ProcessStage>("idle");
  const [busy, setBusy] = useState(false);
  const [recordingState, setRecordingState] = useState<"idle" | "recording" | "paused" | "processing">("idle");
  const [showPatientForm, setShowPatientForm] = useState(false);
  const [newPatient, setNewPatient] = useState({ full_name: "", identifier: "", birth_date: "", contact: "", notes: "" });
  const [loginSession, setLoginSession] = useState<LoginSession | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const selectedModel = useMemo(() => models.find((model) => model.selected), [models]);
  const selectedPatient = patients.find((patient) => patient.id === selectedPatientId) || null;
  const noteConsultationsForSelectedPatient = useMemo(
    () => getPatientNoteConsultations(consultations, selectedPatientId),
    [consultations, selectedPatientId],
  );
  const noteText = note?.bloques_copiables.resumen_para_medico || note?.resumen_breve || "";

  async function refreshAll() {
    const [setupPayload, modelPayload, patientPayload, consultationPayload] = await Promise.all([
      api<SetupStatus>("/setup/status"),
      api<ModelsResponse>("/transcription/models"),
      api<Patient[]>("/patients"),
      api<Consultation[]>("/consultations"),
    ]);
    setSetup(setupPayload);
    setModels(modelPayload.models);
    setPatients(patientPayload);
    setConsultations(consultationPayload);
    if (setupPayload.ready_for_real_use) {
      setStatus("Listo para capturar entrevistas autorizadas.");
    } else {
      setStatus("Inicia sesion con OpenAI Codex y verifica Whisper para usar la herramienta.");
    }
    if (!selectedPatientId && patientPayload.length) setSelectedPatientId(patientPayload[0].id);
    return setupPayload;
  }

  useEffect(() => {
    refreshAll().catch((error) => setStatus(error instanceof Error ? error.message : "No se pudo cargar el sistema."));
  }, []);

  useEffect(() => {
    if (!loginSession?.session_id || loginSession.status === "completed") return;
    const timer = window.setInterval(async () => {
      try {
        const session = await api<LoginSession>(`/auth/codex/login/session/${loginSession.session_id}`);
        setLoginSession(session);
        if (session.logged_in || session.status === "completed") {
          await api("/setup/complete", { method: "POST" });
          await refreshAll();
          setLoginSession(null);
          window.clearInterval(timer);
        }
      } catch {
        window.clearInterval(timer);
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [loginSession]);

  useEffect(() => {
    if (section !== "notes" || !selectedPatientId) return;
    const selectedNoteBelongsToPatient = noteConsultationsForSelectedPatient.some(
      (consultation) => consultation.id === selectedNoteConsultationId,
    );
    if (selectedNoteBelongsToPatient) return;
    const latest = noteConsultationsForSelectedPatient[0];
    if (latest) {
      void loadStructuredNote(latest.id);
      return;
    }
    setSelectedNoteConsultationId("");
    setCurrentConsultation(null);
    setNote(null);
    setTranscript(null);
  }, [section, selectedPatientId, selectedNoteConsultationId, noteConsultationsForSelectedPatient]);

  async function startLogin() {
    setBusy(true);
    setCopiedCode(false);
    try {
      const session = await api<LoginSession>("/auth/codex/login/start", { method: "POST" });
      setLoginSession(session);
      setStatus(session.message);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo iniciar sesion.");
    } finally {
      setBusy(false);
    }
  }

  async function createPatient(event: React.FormEvent) {
    event.preventDefault();
    if (!newPatient.full_name.trim()) {
      setStatus("Escribe el nombre del paciente.");
      return;
    }
    setBusy(true);
    try {
      const created = await api<Patient>("/patients", {
        method: "POST",
        body: JSON.stringify({
          full_name: newPatient.full_name.trim(),
          identifier: newPatient.identifier.trim() || null,
          birth_date: newPatient.birth_date || null,
          contact: newPatient.contact.trim() || null,
          notes: newPatient.notes.trim() || null,
        }),
      });
      setPatients((current) => [created, ...current]);
      setSelectedPatientId(created.id);
      setNewPatient({ full_name: "", identifier: "", birth_date: "", contact: "", notes: "" });
      setShowPatientForm(false);
      setStatus("Paciente creado. Ya puedes iniciar una captura autorizada.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo crear el paciente.");
    } finally {
      setBusy(false);
    }
  }

  async function startCapture() {
    if (!selectedPatient) {
      setStatus("Primero crea o selecciona un paciente.");
      setSection("patients");
      return;
    }
    if (!consentConfirmed) {
      setStatus("Registra el consentimiento antes de iniciar la grabacion.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setStatus("Este navegador no permite grabacion de audio desde la app.");
      return;
    }

    setBusy(true);
    setNote(null);
    setTranscript(null);
    try {
      const created = await api<Consultation>("/consultations", {
        method: "POST",
        body: JSON.stringify({
          title: `Entrevista - ${selectedPatient.full_name}`,
          consent_confirmed: true,
          patient_id: selectedPatient.id,
          patient_label: selectedPatient.full_name,
        }),
      });
      setCurrentConsultation(created);
      setConsultations((current) => [created, ...current]);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const preferredType = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"].find((type) =>
        MediaRecorder.isTypeSupported(type),
      );
      const recorder = new MediaRecorder(stream, preferredType ? { mimeType: preferredType } : undefined);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || preferredType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        recorderRef.current = null;
        setRecordingState("processing");
        void processAudio(blob, created.id);
      };
      recorder.start(1000);
      setRecordingState("recording");
      setSection("capture");
      setStatus("Grabacion activa. Finaliza cuando termine la entrevista.");
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      recorderRef.current = null;
      setRecordingState("idle");
      setStatus(error instanceof Error ? error.message : "No se pudo iniciar la captura.");
    } finally {
      setBusy(false);
    }
  }

  async function processAudio(blob: Blob, consultationId: string) {
    setBusy(true);
    try {
      if (!blob.size) throw new Error("La grabacion quedo vacia. Revisa el microfono e intenta nuevamente.");
      const formData = new FormData();
      const extension = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
      formData.append("file", blob, `entrevista-${consultationId}.${extension}`);
      setProcessStage("transcribing");
      setStatus("Transcribiendo la entrevista con Whisper local.");
      await api(`/consultations/${consultationId}/audio/upload`, { method: "POST", body: formData });

      const generatedTranscript = await api<Transcript>(`/consultations/${consultationId}/transcribe`, { method: "POST" });
      setTranscript(generatedTranscript);
      if (!generatedTranscript.segments.length) {
        throw new Error("Whisper no detecto voz clara. Revisa microfono, volumen y ruido ambiente.");
      }

      setProcessStage("organizing");
      setStatus("Organizando la informacion transcrita para revision medica.");
      const generatedNote = await api<ClinicalNote>(`/consultations/${consultationId}/generate-note`, { method: "POST" });
      setNote(generatedNote);
      setSelectedNoteConsultationId(consultationId);
      setProcessStage("idle");
      setStatus("Entrevista organizada. Revisa el contenido antes de usarlo.");
      await refreshAll();
    } catch (error) {
      setProcessStage("idle");
      setStatus(error instanceof Error ? error.message : "No se pudo completar el flujo.");
    } finally {
      setBusy(false);
      setRecordingState("idle");
    }
  }

  function pauseCapture() {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.pause();
      setRecordingState("paused");
      setStatus("Grabacion pausada.");
    }
  }

  function resumeCapture() {
    if (recorderRef.current?.state === "paused") {
      recorderRef.current.resume();
      setRecordingState("recording");
      setStatus("Grabacion reanudada.");
    }
  }

  function finishCapture() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      setStatus("Finalizando y preparando audio...");
      recorderRef.current.stop();
    }
  }

  async function copyNote() {
    if (!noteText) return;
    await navigator.clipboard.writeText(noteText);
    setStatus("Resumen estructurado copiado.");
  }

  async function loadStructuredNote(consultationId: string) {
    setBusy(true);
    try {
      const consultation = consultations.find((item) => item.id === consultationId) || null;
      const [loadedNote, loadedTranscript] = await Promise.all([
        api<ClinicalNote | null>(`/consultations/${consultationId}/note`),
        api<Transcript>(`/consultations/${consultationId}/transcript`),
      ]);
      setSelectedNoteConsultationId(consultationId);
      setCurrentConsultation(consultation);
      setNote(loadedNote);
      setTranscript(loadedTranscript);
      setStatus(loadedNote ? "Nota cargada para revision." : "Esta entrevista aun no tiene nota estructurada.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo cargar la nota.");
    } finally {
      setBusy(false);
    }
  }

  async function selectPatientForNotes(patientId: string) {
    setSelectedPatientId(patientId);
    setSelectedNoteConsultationId("");
    const latest = getPatientNoteConsultations(consultations, patientId)[0];
    if (latest) {
      await loadStructuredNote(latest.id);
      return;
    }
    setCurrentConsultation(null);
    setNote(null);
    setTranscript(null);
    setStatus(patientId ? "Este paciente aun no tiene notas estructuradas." : "Selecciona un paciente para ver sus notas.");
  }

  async function copyLoginCode() {
    if (!loginSession?.user_code) return;
    await navigator.clipboard.writeText(loginSession.user_code);
    setCopiedCode(true);
  }

  const nav: Array<[Section, string]> = [
    ["home", "Inicio"],
    ["patients", "Pacientes"],
    ["capture", "Captura y transcripcion"],
    ["notes", "Notas estructuradas"],
    ["settings", "Configuracion"],
  ];

  return (
    <>
      <main className="clinical-shell">
        <aside className="sidebar">
          <Brand />
          <nav aria-label="Navegacion principal">
            {nav.map(([id, label]) => (
              <button key={id} className={section === id ? "nav-item active" : "nav-item"} onClick={() => setSection(id)}>
                {label}
              </button>
            ))}
          </nav>
          {!setup?.ready_for_real_use && (
            <button className="quiet-button full" disabled={busy} onClick={startLogin}>Iniciar sesion OpenAI</button>
          )}
        </aside>

        <section className="clinical-main">
          <header className="clinical-topbar">
            <div>
              <p className="eyebrow">Herramienta de apoyo al medico</p>
              <h1>{nav.find(([id]) => id === section)?.[1]}</h1>
            </div>
            <div className="topbar-tools">
              <StatusPill tone={setup?.ready_for_real_use ? "success" : "warning"}>
                {setup?.ready_for_real_use ? "Sistema listo" : "Configuracion pendiente"}
              </StatusPill>
              <StatusPill tone="info">Whisper {selectedModel?.name || "Small"}</StatusPill>
              <button onClick={() => setSection("capture")}>Nueva entrevista</button>
            </div>
          </header>

          <WorkspaceStatus processStage={processStage} status={status} />

          {section === "home" && (
            <Home
              consultations={consultations}
              note={note}
              patients={patients}
              setSection={setSection}
              startCapture={startCapture}
              transcript={transcript}
            />
          )}
          {section === "patients" && (
            <Patients
              busy={busy}
              createPatient={createPatient}
              newPatient={newPatient}
              patients={patients}
              selectedPatientId={selectedPatientId}
              setNewPatient={setNewPatient}
              setSelectedPatientId={setSelectedPatientId}
              setShowPatientForm={setShowPatientForm}
              showPatientForm={showPatientForm}
            />
          )}
          {section === "capture" && (
            <Capture
              busy={busy}
              consentConfirmed={consentConfirmed}
              currentConsultation={currentConsultation}
              finishCapture={finishCapture}
              note={note}
              pauseCapture={pauseCapture}
              patients={patients}
              recordingState={recordingState}
              resumeCapture={resumeCapture}
              selectedPatientId={selectedPatientId}
              setConsentConfirmed={setConsentConfirmed}
              setSelectedPatientId={setSelectedPatientId}
              startCapture={startCapture}
              transcript={transcript}
            />
          )}
          {section === "notes" && (
            <Notes
              busy={busy}
              consultations={noteConsultationsForSelectedPatient}
              copyNote={copyNote}
              note={note}
              onPatientChange={selectPatientForNotes}
              onSelectConsultation={loadStructuredNote}
              patients={patients}
              selectedConsultationId={selectedNoteConsultationId}
              selectedPatientId={selectedPatientId}
              transcript={transcript}
            />
          )}
          {section === "settings" && <Settings models={models} setup={setup} startLogin={startLogin} />}
        </section>
      </main>

      {loginSession && (
        <LoginModal
          closeLoginModal={() => setLoginSession(null)}
          copiedCode={copiedCode}
          copyLoginCode={copyLoginCode}
          loginSession={loginSession}
          refreshSetup={refreshAll}
        />
      )}
    </>
  );
}

function WorkspaceStatus({ processStage, status }: { processStage: ProcessStage; status: string }) {
  if (status.includes("[{")) return null;
  if (processStage === "transcribing") {
    return (
      <p className="workspace-status processing" aria-live="polite">
        Transcribiendo entrevista con Whisper
        <AnimatedDots />
      </p>
    );
  }
  if (processStage === "organizing") {
    return (
      <p className="workspace-status processing" aria-live="polite">
        Organizando informacion para revision medica
        <AnimatedDots />
      </p>
    );
  }
  return <p className="workspace-status" aria-live="polite">{status}</p>;
}

function AnimatedDots() {
  return (
    <span className="animated-dots" aria-hidden="true">
      <span>.</span>
      <span>.</span>
      <span>.</span>
    </span>
  );
}

function getPatientNoteConsultations(consultations: Consultation[], patientId: string) {
  if (!patientId) return [];
  return consultations
    .filter((consultation) => consultation.patient_id === patientId && consultation.status === "note_generated")
    .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime());
}

function Home({
  consultations,
  note,
  patients,
  setSection,
  startCapture,
  transcript,
}: {
  consultations: Consultation[];
  note: ClinicalNote | null;
  patients: Patient[];
  setSection: (section: Section) => void;
  startCapture: () => void;
  transcript: Transcript | null;
}) {
  return (
    <section className="dashboard-grid">
      <div className="metric-row three">
        <article className="metric-card"><span>Pacientes</span><strong>{patients.length}</strong><small>registrados en esta PC</small></article>
        <article className="metric-card"><span>Entrevistas</span><strong>{consultations.length}</strong><small>capturas guardadas</small></article>
        <article className="metric-card"><span>Ultima transcripcion</span><strong>{transcript?.segments.length || 0}</strong><small>segmentos detectados</small></article>
      </div>
      <section className="work-card wide">
        <div className="card-head">
          <div>
            <h2>Flujo principal</h2>
            <p>Graba una entrevista autorizada, transcribe con Whisper local y organiza la informacion para revision medica.</p>
          </div>
          <button onClick={startCapture}>Iniciar captura</button>
        </div>
      </section>
      <section className="work-card">
        <h2>Paciente</h2>
        <p>{patients.length ? "Selecciona un paciente y registra consentimiento antes de grabar." : "No hay pacientes creados todavia."}</p>
        <button className="secondary" onClick={() => setSection("patients")}>Gestionar pacientes</button>
      </section>
      <section className="work-card">
        <h2>Ultima nota</h2>
        <p>{note?.resumen_breve || "Aun no hay una entrevista organizada."}</p>
        <button className="secondary" onClick={() => setSection("notes")}>Ver nota</button>
      </section>
    </section>
  );
}

function Patients({
  busy,
  createPatient,
  newPatient,
  patients,
  selectedPatientId,
  setNewPatient,
  setSelectedPatientId,
  setShowPatientForm,
  showPatientForm,
}: {
  busy: boolean;
  createPatient: (event: React.FormEvent) => void;
  newPatient: { full_name: string; identifier: string; birth_date: string; contact: string; notes: string };
  patients: Patient[];
  selectedPatientId: string;
  setNewPatient: React.Dispatch<React.SetStateAction<{ full_name: string; identifier: string; birth_date: string; contact: string; notes: string }>>;
  setSelectedPatientId: (id: string) => void;
  setShowPatientForm: (show: boolean) => void;
  showPatientForm: boolean;
}) {
  return (
    <section className="work-card">
      <div className="card-head">
        <div>
          <h2>Pacientes reales</h2>
          <p>La lista inicia vacia. Crea solo pacientes que vayas a atender.</p>
        </div>
        <button onClick={() => setShowPatientForm(!showPatientForm)}>{showPatientForm ? "Cerrar" : "Crear paciente"}</button>
      </div>

      {showPatientForm && (
        <form className="patient-form" onSubmit={createPatient}>
          <label>Nombre completo<input value={newPatient.full_name} onChange={(event) => setNewPatient((current) => ({ ...current, full_name: event.target.value }))} /></label>
          <label>Identificador<input value={newPatient.identifier} onChange={(event) => setNewPatient((current) => ({ ...current, identifier: event.target.value }))} /></label>
          <label>Fecha de nacimiento<input type="date" value={newPatient.birth_date} onChange={(event) => setNewPatient((current) => ({ ...current, birth_date: event.target.value }))} /></label>
          <label>Contacto<input value={newPatient.contact} onChange={(event) => setNewPatient((current) => ({ ...current, contact: event.target.value }))} /></label>
          <label className="wide-field">Notas administrativas<textarea value={newPatient.notes} onChange={(event) => setNewPatient((current) => ({ ...current, notes: event.target.value }))} /></label>
          <button disabled={busy}>Guardar paciente</button>
        </form>
      )}

      <div className="patient-grid">
        {patients.map((patient) => (
          <article className={patient.id === selectedPatientId ? "patient-card selected" : "patient-card"} key={patient.id}>
            <div className="card-head">
              <h3>{patient.full_name}</h3>
              <StatusPill tone={patient.id === selectedPatientId ? "success" : "neutral"}>{patient.id === selectedPatientId ? "Seleccionado" : "Disponible"}</StatusPill>
            </div>
            <p>{patient.identifier || "Sin identificador"}{patient.birth_date ? ` - ${patient.birth_date}` : ""}</p>
            <button className="secondary" onClick={() => setSelectedPatientId(patient.id)}>Seleccionar</button>
          </article>
        ))}
      </div>
      {!patients.length && <p className="empty-state">No hay pacientes creados.</p>}
    </section>
  );
}

function Capture({
  busy,
  consentConfirmed,
  currentConsultation,
  finishCapture,
  note,
  pauseCapture,
  patients,
  recordingState,
  resumeCapture,
  selectedPatientId,
  setConsentConfirmed,
  setSelectedPatientId,
  startCapture,
  transcript,
}: {
  busy: boolean;
  consentConfirmed: boolean;
  currentConsultation: Consultation | null;
  finishCapture: () => void;
  note: ClinicalNote | null;
  pauseCapture: () => void;
  patients: Patient[];
  recordingState: "idle" | "recording" | "paused" | "processing";
  resumeCapture: () => void;
  selectedPatientId: string;
  setConsentConfirmed: (value: boolean) => void;
  setSelectedPatientId: (id: string) => void;
  startCapture: () => void;
  transcript: Transcript | null;
}) {
  const recordingTone = recordingState === "recording" ? "danger" : recordingState === "paused" ? "warning" : recordingState === "processing" ? "info" : "neutral";
  const recordingLabel = recordingState === "recording" ? "Grabando" : recordingState === "paused" ? "Pausado" : recordingState === "processing" ? "Procesando" : "Inactivo";

  return (
    <section className="encounter-layout focused">
      <aside className="context-panel">
        <h2>Antes de grabar</h2>
        <label>Paciente
          <select value={selectedPatientId} onChange={(event) => setSelectedPatientId(event.target.value)}>
            <option value="">Seleccionar paciente</option>
            {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.full_name}</option>)}
          </select>
        </label>
        <label className="check-row">
          <input checked={consentConfirmed} type="checkbox" onChange={(event) => setConsentConfirmed(event.target.checked)} />
          Confirmo que el paciente autorizo la grabacion.
        </label>
        <p>La IA no emite diagnosticos ni decisiones. Solo organiza lo transcrito para revision del medico.</p>
      </aside>

      <section className="capture-center">
        <div className="capture-toolbar">
          <StatusPill tone={recordingTone}>{recordingLabel}</StatusPill>
          <StatusPill>Whisper local</StatusPill>
          {currentConsultation && <StatusPill tone="info">Consulta {currentConsultation.id.slice(0, 8)}</StatusPill>}
          <button disabled={busy || recordingState !== "idle"} onClick={startCapture}>Iniciar grabacion</button>
          <button className="secondary" disabled={recordingState !== "recording"} onClick={pauseCapture}>Pausar</button>
          <button className="secondary" disabled={recordingState !== "paused"} onClick={resumeCapture}>Reanudar</button>
          <button className="secondary" disabled={!["recording", "paused"].includes(recordingState)} onClick={finishCapture}>Finalizar y transcribir</button>
        </div>

        <div className="transcript-panel">
          <div className="card-head">
            <h2>Transcripcion</h2>
            <StatusPill tone={transcript?.segments.length ? "success" : "neutral"}>{transcript?.segments.length || 0} segmentos</StatusPill>
          </div>
          <div className="transcript-list">
            {transcript?.segments.map((segment) => (
              <p key={segment.id}><strong>{formatTime(segment.start_time)}</strong> {segment.text}</p>
            ))}
            {!transcript?.segments.length && <p>Finaliza una grabacion para ver la transcripcion.</p>}
          </div>
        </div>

        <div className="note-editor compact-note">
          <div className="card-head">
            <h2>Informacion organizada</h2>
            <StatusPill tone={note ? "success" : "neutral"}>{note ? "Lista para revisar" : "Pendiente"}</StatusPill>
          </div>
          <textarea readOnly value={note?.bloques_copiables.resumen_para_medico || note?.resumen_breve || "Aqui aparecera el resumen estructurado de la entrevista."} />
        </div>
      </section>
    </section>
  );
}

function Notes({
  busy,
  consultations,
  copyNote,
  note,
  onPatientChange,
  onSelectConsultation,
  patients,
  selectedConsultationId,
  selectedPatientId,
  transcript,
}: {
  busy: boolean;
  consultations: Consultation[];
  copyNote: () => void;
  note: ClinicalNote | null;
  onPatientChange: (patientId: string) => void;
  onSelectConsultation: (consultationId: string) => void;
  patients: Patient[];
  selectedConsultationId: string;
  selectedPatientId: string;
  transcript: Transcript | null;
}) {
  return (
    <section className="notes-layout">
      <aside className="work-card note-index">
        <h2>Paciente</h2>
        <select value={selectedPatientId} onChange={(event) => onPatientChange(event.target.value)}>
          <option value="">Seleccionar paciente</option>
          {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.full_name}</option>)}
        </select>

        <div className="note-history-head">
          <h3>Notas por fecha</h3>
          <StatusPill tone={consultations.length ? "success" : "neutral"}>{consultations.length}</StatusPill>
        </div>
        <div className="note-history-list">
          {consultations.map((consultation) => (
            <button
              className={consultation.id === selectedConsultationId ? "note-history-item active" : "note-history-item"}
              disabled={busy}
              key={consultation.id}
              onClick={() => onSelectConsultation(consultation.id)}
            >
              <strong>{formatDateTime(consultation.created_at)}</strong>
              <span>{consultation.title}</span>
            </button>
          ))}
        </div>
        {!selectedPatientId && <p className="empty-state">Selecciona un paciente para ver sus notas.</p>}
        {selectedPatientId && !consultations.length && <p className="empty-state">Este paciente aun no tiene notas estructuradas.</p>}
      </aside>

      <article className="work-card">
        <div className="card-head">
          <h2>Nota estructurada</h2>
          <button disabled={!note} onClick={copyNote}>Copiar</button>
        </div>
        {note ? (
          <div className="structured-note">
            <h3>Motivo</h3><p>{note.motivo_consulta}</p>
            <h3>Resumen</h3><p>{note.resumen_breve}</p>
            <h3>Historia referida</h3><p>{note.anamnesis.enfermedad_actual}</p>
            <h3>Antecedentes mencionados</h3><p>{note.anamnesis.antecedentes_personales}</p>
            <h3>Medicamentos y alergias mencionadas</h3><p>{note.anamnesis.medicamentos_habituales} - {note.anamnesis.alergias}</p>
            <h3>Pendientes de revision</h3><p>{note.pendientes.join(". ") || "No mencionado"}</p>
            <h3>Informacion faltante</h3><p>{note.metadata?.missing_information?.join(". ") || "No mencionado"}</p>
          </div>
        ) : (
          <p className="empty-state">No hay nota todavia. Graba y procesa una entrevista.</p>
        )}
      </article>
      <article className="work-card">
        <h2>Transcripcion fuente</h2>
        <div className="transcript-list">
          {transcript?.segments.map((segment) => <p key={segment.id}>{segment.text}</p>)}
          {!transcript?.segments.length && <p>No hay transcripcion fuente.</p>}
        </div>
      </article>
    </section>
  );
}

function Settings({ models, setup, startLogin }: { models: WhisperModel[]; setup: SetupStatus | null; startLogin: () => void }) {
  return (
    <section className="settings-grid">
      <article className="work-card">
        <h2>OpenAI Codex</h2>
        <p>{setup?.codex.logged_in ? "Sesion conectada para organizar transcripciones." : "Pendiente de inicio de sesion."}</p>
        <button disabled={setup?.codex.logged_in} onClick={startLogin}>Iniciar sesion</button>
      </article>
      <article className="work-card">
        <h2>Whisper local</h2>
        <div className="entity-list">
          {models.map((model) => <StatusPill key={model.id} tone={model.selected ? "success" : model.installed ? "info" : "neutral"}>{model.name}</StatusPill>)}
        </div>
      </article>
    </section>
  );
}

function LoginModal({
  closeLoginModal,
  copiedCode,
  copyLoginCode,
  loginSession,
  refreshSetup,
}: {
  closeLoginModal: () => void;
  copiedCode: boolean;
  copyLoginCode: () => void;
  loginSession: LoginSession;
  refreshSetup: () => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="login-modal" role="dialog" aria-modal="true" aria-labelledby="login-title">
        <button className="icon-button" onClick={closeLoginModal} aria-label="Cerrar">x</button>
        <p className="eyebrow">OpenAI Codex</p>
        <h2 id="login-title">Inicia sesion</h2>
        <p>Abre la pagina oficial de OpenAI y escribe este codigo cuando se solicite.</p>
        <div className="code-box">
          <span>Codigo de un solo uso</span>
          <strong>{loginSession.user_code || "Preparando..."}</strong>
        </div>
        <div className="modal-actions">
          <a className={`button-link ${!loginSession.auth_url ? "disabled-link" : ""}`} href={loginSession.auth_url || undefined} target="_blank" rel="noreferrer">Abrir OpenAI</a>
          <button className="secondary" disabled={!loginSession.user_code} onClick={copyLoginCode}>{copiedCode ? "Copiado" : "Copiar codigo"}</button>
          <button className="secondary" onClick={refreshSetup}>Ya termine</button>
        </div>
        <p className="modal-note">El codigo vence en {loginSession.expires_in_minutes} minutos. No lo compartas.</p>
        <p className="modal-status">{loginSession.message}</p>
      </section>
    </div>
  );
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) return "00:00";
  const mins = Math.floor(seconds / 60).toString().padStart(2, "0");
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Fecha no disponible";
  return date.toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

createRoot(document.getElementById("root")!).render(<App />);
