const TOKEN_KEY = "careerpilot_access_token";

export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
  status: string;
  created_at: string;
};

export type CandidateProfile = {
  id: string;
  headline: string | null;
  preferences_version: number;
};

export type ExperienceEntry = {
  id?: string;
  company?: string | null;
  title?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  summary?: string | null;
  bullets?: string[];
};

export type EducationEntry = {
  id?: string;
  institution?: string | null;
  degree?: string | null;
  specialization?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  score?: string | null;
  score_type?: string | null;
  summary?: string | null;
  details?: string[];
};

export type ProjectEntry = {
  id?: string;
  title?: string | null;
  organization?: string | null;
  url?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  summary?: string | null;
  bullets?: string[];
  technologies?: string[];
};

export type CertificationEntry = {
  id?: string;
  title?: string | null;
  issuer?: string | null;
  date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  url?: string | null;
  summary?: string | null;
};

export type AwardEntry = {
  id?: string;
  title?: string | null;
  issuer?: string | null;
  date?: string | null;
  summary?: string | null;
};

export type ResumeContentJson = {
  schema_version?: string;
  contact?: {
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    location?: string | null;
    links?: string[];
  };
  headline?: string | null;
  summary?: string | null;
  experience?: ExperienceEntry[];
  education?: EducationEntry[];
  skills?: string[];
  projects?: ProjectEntry[];
  certifications?: CertificationEntry[];
  awards?: AwardEntry[];
  languages?: string[];
  hobbies?: string[];
  personal?: {
    job_title?: string | null;
    work_authorization?: string | null;
    notes?: string | null;
  };
  links?: string[];
};

export type ProfileResumePayload = {
  candidate_profile: CandidateProfile;
  content: ResumeContentJson;
};

export type AuthPayload = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
  candidate_profile: CandidateProfile;
};

export type MePayload = {
  user: AuthUser;
  candidate_profile: CandidateProfile | null;
};

export type ApiEnvelope<T> = {
  data: T | null;
  metadata: Record<string, unknown>;
  errors: Array<{ code?: string; message?: string }>;
};

function apiBase(): string {
  // Browser: same-origin via Next.js rewrite. Server: direct API URL.
  if (typeof window !== "undefined") return "";
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<{ status: number; body: ApiEnvelope<T> }> {
  const headers = new Headers(init.headers);
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (!headers.has("Content-Type") && init.body && !isFormData) {
    headers.set("Content-Type", "application/json");
  }
  const token = getStoredToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  let raw: unknown = null;
  const text = await res.text();
  if (!text) {
    return {
      status: res.status,
      body: {
        data: null,
        metadata: {},
        errors:
          res.status >= 200 && res.status < 300
            ? []
            : [{ code: "empty_response", message: `Request failed (${res.status}).` }],
      },
    };
  }
  try {
    raw = JSON.parse(text);
  } catch {
    return {
      status: res.status,
      body: {
        data: null,
        metadata: {},
        errors: [{ code: "invalid_response", message: `Request failed (${res.status}).` }],
      },
    };
  }

  const body = raw as ApiEnvelope<T> & {
    detail?: string | Array<{ msg?: string; loc?: unknown[] }>;
  };

  // Normalize FastAPI validation errors into our envelope shape.
  if ((!body.errors || body.errors.length === 0) && body.detail) {
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
      : String(detail);
    return {
      status: res.status,
      body: {
        data: body.data ?? null,
        metadata: body.metadata ?? {},
        errors: [{ code: "validation_error", message }],
      },
    };
  }

  return {
    status: res.status,
    body: {
      data: body.data ?? null,
      metadata: body.metadata ?? {},
      errors: body.errors ?? [],
    },
  };
}

export async function register(input: {
  email: string;
  password: string;
  display_name?: string;
}) {
  const { status, body } = await apiFetch<AuthPayload>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (status >= 200 && status < 300 && body.data?.access_token) {
    setStoredToken(body.data.access_token);
  }
  return { status, body };
}

export async function login(input: { email: string; password: string }) {
  const { status, body } = await apiFetch<AuthPayload>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (status >= 200 && status < 300 && body.data?.access_token) {
    setStoredToken(body.data.access_token);
  }
  return { status, body };
}

export async function logout() {
  const result = await apiFetch<{ ok: boolean }>("/api/v1/auth/logout", {
    method: "POST",
  });
  setStoredToken(null);
  return result;
}

export async function fetchMe() {
  return apiFetch<MePayload>("/api/v1/me");
}

export type ResumeItem = {
  id: string;
  title: string | null;
  status: string;
  origin?: "uploaded" | "generated";
  source_mime_type: string | null;
  source_checksum: string | null;
  source_object_key: string | null;
  active_version_id: string | null;
  created_at: string;
  updated_at: string;
  content?: ResumeContentJson | null;
  parser?: string | null;
  ai_parse_error?: string | null;
};

export async function listResumes(opts?: {
  origin?: "uploaded" | "generated" | "all";
  sort?: "created_at" | "updated_at";
  order?: "asc" | "desc";
}) {
  const params = new URLSearchParams();
  if (opts?.origin && opts.origin !== "all") params.set("origin", opts.origin);
  if (opts?.sort) params.set("sort", opts.sort);
  if (opts?.order) params.set("order", opts.order);
  const qs = params.toString();
  return apiFetch<{ items: ResumeItem[] }>(`/api/v1/resumes${qs ? `?${qs}` : ""}`);
}

export async function saveResumeFromContent(input: {
  title: string;
  content: ResumeContentJson | Record<string, unknown>;
  parent_resume_id?: string;
  job_posting_id?: string;
}) {
  return apiFetch<ResumeItem>("/api/v1/resumes/from-content", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateResume(
  id: string,
  input: { title?: string; content?: ResumeContentJson | Record<string, unknown> },
) {
  return apiFetch<ResumeItem>(`/api/v1/resumes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function deleteResume(id: string) {
  return apiFetch<null>(`/api/v1/resumes/${id}`, { method: "DELETE" });
}

export async function getMyProfile() {
  return apiFetch<ProfileResumePayload>("/api/v1/me/profile");
}

export async function updateMyProfile(content: ResumeContentJson | Record<string, unknown>) {
  return apiFetch<ProfileResumePayload>("/api/v1/me/profile", {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export async function uploadResume(file: File, title?: string) {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);
  return apiFetch<ResumeItem>("/api/v1/resumes", {
    method: "POST",
    body: form,
  });
}

export async function getResume(id: string) {
  return apiFetch<ResumeItem>(`/api/v1/resumes/${id}`);
}

export async function parseResume(id: string) {
  return apiFetch<ResumeItem>(`/api/v1/resumes/${id}/parse`, { method: "POST" });
}

export type JobItem = {
  id: string;
  title: string;
  description: string | null;
  location: string | null;
  remote_type: string | null;
  compensation: Record<string, unknown> | null;
  requirements: { skills?: string[]; [key: string]: unknown } | null;
  status: string;
  posted_at: string | null;
  canonical_url: string | null;
  company: { id: string; name: string; website: string | null; industry: string | null } | null;
  created_at: string;
  updated_at: string;
};

export type TailorSuggestion = {
  id: string;
  section: string;
  title: string;
  rationale: string;
  path: string;
  before: unknown;
  after: unknown;
  selected_by_default: boolean;
};

export type TailorResult = {
  model_version: string;
  resume_id: string;
  job_posting_id: string;
  job_title: string;
  job_company: string | null;
  job_url: string | null;
  match_preview: {
    score?: number;
    confidence?: number;
    matched_skills?: string[];
    missing_skills?: string[];
    reasons?: string[];
  };
  suggestions: TailorSuggestion[];
  current_content: Record<string, unknown>;
  proposed_content: Record<string, unknown>;
  applied_content?: Record<string, unknown> | null;
};

export async function ingestLinkedInJobUrl(input: {
  url: string;
  description_override?: string;
}) {
  return apiFetch<{ created: boolean; job: JobItem }>("/api/v1/jobs/from-linkedin-url", {
    method: "POST",
    body: JSON.stringify({
      ...input,
      url: canonicalizeLinkedInJobUrl(input.url),
    }),
  });
}

/** Prefer short /jobs/view/{id}/ form so tracking query strings don't blow request limits. */
export function canonicalizeLinkedInJobUrl(url: string): string {
  const text = url.trim();
  const match =
    text.match(/linkedin\.com\/(?:jobs\/view|jobs\/collections\/[^/]+\/)\/(\d{6,})/i) ||
    text.match(/currentJobId=(\d{6,})/i) ||
    text.match(/^(\d{6,})$/);
  if (match?.[1]) {
    return `https://www.linkedin.com/jobs/view/${match[1]}/`;
  }
  return text;
}

export async function tailorResume(
  resumeId: string,
  input: {
    job_posting_id?: string;
    job_url?: string;
    description_override?: string;
    selected_suggestion_ids?: string[];
  },
) {
  return apiFetch<TailorResult>(`/api/v1/resumes/${resumeId}/tailor`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export type CoverLetterResult = {
  model_version: string;
  resume_id: string;
  job_posting_id: string;
  job_title: string;
  job_company: string | null;
  job_url: string | null;
  tone: string;
  recipient: string;
  subject: string;
  text: string;
  highlights: {
    matched_skills?: string[];
    latest_role?: string | null;
    latest_company?: string | null;
  };
};

export async function generateCoverLetter(
  resumeId: string,
  input: {
    job_posting_id?: string;
    job_url?: string;
    description_override?: string;
  },
) {
  return apiFetch<CoverLetterResult>(`/api/v1/resumes/${resumeId}/cover-letter`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export type JobFilters = {
  query?: string;
  q?: string;
  location?: string;
  country?: string;
  remote_type?: string;
  skills?: string[];
  experience_level?: string;
  min_experience_years?: number;
  include_demo?: boolean;
  include_remotive?: boolean;
  include_naukri?: boolean;
  limit?: number;
};

export type JobProvidersStatus = {
  demo: { provider: string; ready: boolean };
  remotive: { provider: string; ready: boolean };
  naukri: {
    provider: string;
    configured: boolean;
    package_present: boolean;
    import_ok: boolean;
    playwright_ok: boolean;
    ready: boolean;
    default_location?: string;
    hint?: string | null;
  };
};

export async function getJobProviders() {
  return apiFetch<JobProvidersStatus>("/api/v1/jobs/providers");
}

export async function listJobs(params?: {
  q?: string;
  location?: string;
  country?: string;
  remote_type?: string;
  skills?: string;
  experience_level?: string;
  min_experience_years?: number;
}) {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.location) search.set("location", params.location);
  if (params?.country) search.set("country", params.country);
  if (params?.remote_type) search.set("remote_type", params.remote_type);
  if (params?.skills) search.set("skills", params.skills);
  if (params?.experience_level) search.set("experience_level", params.experience_level);
  if (params?.min_experience_years != null) {
    search.set("min_experience_years", String(params.min_experience_years));
  }
  const qs = search.toString();
  return apiFetch<{ items: JobItem[]; total: number }>(`/api/v1/jobs${qs ? `?${qs}` : ""}`);
}

export async function discoverJobs(input?: JobFilters) {
  return apiFetch<{
    discovered: number;
    created: number;
    updated: number;
    items: JobItem[];
    warnings?: string[];
  }>("/api/v1/jobs/discover", {
    method: "POST",
    body: JSON.stringify(input ?? { include_demo: true, include_remotive: true, limit: 20 }),
  });
}

export async function getJob(id: string) {
  return apiFetch<JobItem>(`/api/v1/jobs/${id}`);
}

export type MatchItem = {
  id: string;
  score: number;
  confidence: number | null;
  explanation: {
    matched_skills?: string[];
    missing_skills?: string[];
    reasons?: string[];
    [key: string]: unknown;
  } | null;
  features: Record<string, unknown> | null;
  model_version: string;
  resume_version_id: string | null;
  job_posting_id: string;
  job: JobItem | null;
  created_at: string;
  updated_at: string;
};

export async function listMatches(params?: { min_score?: number }) {
  const search = new URLSearchParams();
  if (params?.min_score != null) search.set("min_score", String(params.min_score));
  const qs = search.toString();
  return apiFetch<{ items: MatchItem[]; total: number }>(
    `/api/v1/matches${qs ? `?${qs}` : ""}`,
  );
}

export async function runMatching(input?: {
  resume_id?: string;
  limit?: number;
  min_score?: number;
}) {
  return apiFetch<{
    resume_id: string;
    resume_version_id: string;
    model_version: string;
    scored: number;
    matched: number;
    items: MatchItem[];
  }>("/api/v1/matches/run", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  });
}

export type IntegrationItem = {
  provider: string;
  status: string;
  scopes: string[] | Record<string, unknown> | null;
  external_account_id: string | null;
  last_synced_at: string | null;
  expires_at: string | null;
  connected: boolean;
};

export async function listIntegrations() {
  return apiFetch<{ items: IntegrationItem[] }>("/api/v1/integrations");
}

export async function disconnectLinkedIn() {
  return apiFetch<{ ok: boolean; provider: string }>("/api/v1/integrations/linkedin", {
    method: "DELETE",
  });
}

export async function getLinkedInStatus() {
  return apiFetch<{
    enabled: boolean;
    mock: boolean;
    scopes: string[];
    redirect_uri: string;
  }>("/api/v1/auth/linkedin/status");
}

export async function startLinkedInConnect(): Promise<string | null> {
  const { status, body } = await apiFetch<{ authorize_url: string }>(
    "/api/v1/auth/linkedin/connect?redirect=false",
  );
  if (status >= 200 && status < 300 && body.data?.authorize_url) {
    return body.data.authorize_url;
  }
  return null;
}

export async function runJobDiscoveryAgent(input?: JobFilters) {
  return apiFetch<{
    agent: string;
    agent_version: string;
    query_used: string | null;
    filters_used?: Record<string, unknown>;
    linkedin_connected: boolean;
    linkedin_profile: Record<string, unknown> | null;
    warnings: string[];
    tool_trace: Array<Record<string, unknown>>;
    discovered: number;
    created: number;
    updated: number;
    items: JobItem[];
    confidence: number;
    outcome: string;
    workflow_id?: string;
    workflow_status?: string;
    acp_tasks?: Array<Record<string, unknown>>;
  }>("/api/v1/agents/job-discovery/run", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  });
}

export type ApplicationStatus =
  | "interested"
  | "tailored"
  | "applied"
  | "interview"
  | "rejected"
  | "draft"
  | "cancelled";

export type ApplicationItem = {
  id: string;
  job_posting_id: string;
  status: ApplicationStatus | string;
  title: string | null;
  company: string | null;
  url: string | null;
  idempotency_key: string;
  updated_at: string;
  created_at: string;
};

export async function listApplications() {
  return apiFetch<{ items: ApplicationItem[]; total: number }>("/api/v1/applications");
}

export async function upsertApplication(input: {
  job_posting_id: string;
  status?: ApplicationStatus;
  idempotency_key?: string;
}) {
  return apiFetch<ApplicationItem>("/api/v1/applications", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
  reason?: string,
) {
  return apiFetch<ApplicationItem>(`/api/v1/applications/${applicationId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, reason }),
  });
}

export async function deleteApplication(applicationId: string) {
  return apiFetch<{ ok: boolean }>(`/api/v1/applications/${applicationId}`, {
    method: "DELETE",
  });
}

