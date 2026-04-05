const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Patient {
  id: number;
  patient_code: string;
  name: string;
  gender: string;
  birth_date: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface IsocalRecommendation {
  show: boolean;
  product_name: string;
  description: string;
  permitted_claim: string;
  brand_url: string;
  purchase_url: string;
}

export interface Assessment {
  id: number;
  patient_id: number;
  assess_date: string;
  age_at_assess: number;
  height_cm: number;
  weight_kg: number;
  weight_3m_kg: number | null;
  weight_6m_kg: number | null;
  cc_cm: number | null;
  bmi: number | null;
  wl_pct_3m: number | null;
  wl_pct_6m: number | null;
  mna_q_a: number | null;
  mna_q_b: number | null;
  mna_q_c: number | null;
  mna_q_d: number | null;
  mna_q_e: number | null;
  mna_q_f: number | null;
  mna_total: number | null;
  mna_category: string | null;
  glim_weight_loss: number;
  glim_low_bmi: number;
  glim_muscle: string;
  glim_intake: number;
  glim_inflam: number;
  glim_chronic: number;
  glim_diagnosed: number | null;
  glim_severity: string | null;
  recommendations: string[];
  reasons: string[];
  isocal_recommendation: IsocalRecommendation;
  created_at: string;
}

export interface ChartDataPoint {
  assess_date: string;
  weight_kg: number;
  bmi: number | null;
  mna_total: number | null;
}

export const patientsApi = {
  list: (q?: string) => apiFetch<Patient[]>(`/api/patients${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  get: (id: number) => apiFetch<Patient>(`/api/patients/${id}`),
  create: (data: Partial<Patient>) => apiFetch<Patient>("/api/patients", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Patient>) => apiFetch<Patient>(`/api/patients/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: number) => apiFetch<void>(`/api/patients/${id}`, { method: "DELETE" }),
};

export const assessmentsApi = {
  create: (data: unknown) => apiFetch<Assessment>("/api/assessments", { method: "POST", body: JSON.stringify(data) }),
  get: (id: number) => apiFetch<Assessment>(`/api/assessments/${id}`),
  listForPatient: (patientId: number) => apiFetch<Assessment[]>(`/api/patients/${patientId}/assessments`),
  chartData: (patientId: number) => apiFetch<{ data: ChartDataPoint[] }>(`/api/patients/${patientId}/assessments/chart`),
};

export const exportApi = {
  csvUrl: (patientId: number) => `${API_BASE}/api/export/patients/${patientId}/csv`,
  excelUrl: (patientId: number) => `${API_BASE}/api/export/patients/${patientId}/excel`,
  pdfUrl: (assessmentId: number) => `${API_BASE}/api/assessments/${assessmentId}/pdf`,
};
