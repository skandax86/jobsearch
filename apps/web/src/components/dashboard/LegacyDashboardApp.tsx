"use client";

import Link from "next/link";
import { FormEvent, Suspense, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ProfileStructuredSections } from "@/components/ProfileStructuredSections";
import {
  deleteResume,
  discoverJobs,
  fetchMe,
  generateCoverLetter,
  getJobProviders,
  getMyProfile,
  getResume,
  ingestLinkedInJobUrl,
  listJobs,
  listMatches,
  listResumes,
  logout,
  parseResume,
  runJobDiscoveryAgent,
  runMatching,
  saveResumeFromContent,
  tailorResume,
  updateMyProfile,
  updateResume,
  uploadResume,
  type CoverLetterResult,
  type JobItem,
  type JobProvidersStatus,
  type MatchItem,
  type MePayload,
  type ResumeContentJson,
  type ResumeItem,
  type TailorResult,
} from "@/lib/api";

function formatDateTime(value: string): string {
  try {
    return new Date(value).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function resumeOriginLabel(resume: ResumeItem): string {
  return resume.origin || (resume.source_object_key ? "uploaded" : "generated");
}

function emptyResumeContent(): ResumeContentJson {
  return {
    schema_version: "1.1",
    contact: { name: null, email: null, phone: null, location: null, links: [] },
    headline: null,
    summary: null,
    experience: [],
    education: [],
    skills: [],
    projects: [],
    certifications: [],
    awards: [],
    languages: [],
    hobbies: [],
    personal: { job_title: null, work_authorization: null, notes: null },
    links: [],
  };
}

function formatResumePane(content: Record<string, unknown> | null | undefined): string {
  if (!content) return "—";
  const headline = typeof content.headline === "string" ? content.headline : "";
  const summary = typeof content.summary === "string" ? content.summary : "";
  const skills = Array.isArray(content.skills)
    ? content.skills.filter((s): s is string => typeof s === "string")
    : [];
  const experience = Array.isArray(content.experience) ? content.experience : [];
  const expLines = experience.slice(0, 2).map((item) => {
    if (!item || typeof item !== "object") return "";
    const row = item as Record<string, unknown>;
    const title = typeof row.title === "string" ? row.title : "";
    const company = typeof row.company === "string" ? row.company : "";
    const bullets = Array.isArray(row.bullets)
      ? row.bullets.filter((b): b is string => typeof b === "string")
      : [];
    return [`${title}${company ? ` @ ${company}` : ""}`, ...bullets.map((b) => `• ${b}`)].join(
      "\n",
    );
  });
  return [
    headline && `Headline: ${headline}`,
    summary && `Summary: ${summary}`,
    skills.length ? `Skills: ${skills.join(", ")}` : "",
    expLines.filter(Boolean).join("\n\n"),
  ]
    .filter(Boolean)
    .join("\n\n");
}


export type DashboardSection =
  | "boards"
  | "profile"
  | "resumes"
  | "tailor"
  | "discovery"
  | "matches"
  | "tracker";

type TrackerStatus = "interested" | "tailored" | "applied" | "interview" | "rejected";
type TrackedJob = {
  id: string;
  title: string;
  company: string | null;
  url: string | null;
  status: TrackerStatus;
  updatedAt: string;
};

const TRACKER_KEY = "careerpilot_job_tracker";

function readTrackedJobs(): TrackedJob[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(TRACKER_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as TrackedJob[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeTrackedJobs(items: TrackedJob[]) {
  window.localStorage.setItem(TRACKER_KEY, JSON.stringify(items));
}

export function LegacyDashboardSection({ section }: { section: DashboardSection }) {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
      <DashboardContent section={section} />
    </Suspense>
  );
}

function DashboardContent({ section }: { section: DashboardSection }) {
  const router = useRouter();

  useEffect(() => {
    if (section === "resumes") {
      router.replace("/dashboard/resumes");
    }
  }, [section, router]);

  const [me, setMe] = useState<MePayload | null>(null);
  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selected, setSelected] = useState<ResumeItem | null>(null);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [jobsTotal, setJobsTotal] = useState(0);
  const [jobQuery, setJobQuery] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobCountry, setJobCountry] = useState("");
  const [jobRemoteType, setJobRemoteType] = useState("");
  const [jobSkills, setJobSkills] = useState("");
  const [jobExperience, setJobExperience] = useState("");
  const [jobMinYears, setJobMinYears] = useState("");
  const [includeDemo, setIncludeDemo] = useState(true);
  const [includeRemotive, setIncludeRemotive] = useState(true);
  const [includeNaukri, setIncludeNaukri] = useState(false);
  const [naukriStatus, setNaukriStatus] = useState<JobProvidersStatus["naukri"] | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null);
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [matchesTotal, setMatchesTotal] = useState(0);
  const [selectedMatch, setSelectedMatch] = useState<MatchItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [matchesError, setMatchesError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [matching, setMatching] = useState(false);
  const [parsingId, setParsingId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [agentTrace, setAgentTrace] = useState<string | null>(null);
  const [runningAgent, setRunningAgent] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [linkedinDesc, setLinkedinDesc] = useState("");
  const [tailorError, setTailorError] = useState<string | null>(null);
  const [tailoring, setTailoring] = useState(false);
  const [fetchingLinkedIn, setFetchingLinkedIn] = useState(false);
  const [tailor, setTailor] = useState<TailorResult | null>(null);
  const [selectedSuggestionIds, setSelectedSuggestionIds] = useState<string[]>([]);
  const [appliedContent, setAppliedContent] = useState<Record<string, unknown> | null>(null);
  const [coverLetter, setCoverLetter] = useState<CoverLetterResult | null>(null);
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  const [profileContent, setProfileContent] = useState<ResumeContentJson>(emptyResumeContent());
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);
  const [createResumeOpen, setCreateResumeOpen] = useState(false);
  const [createResumeTitle, setCreateResumeTitle] = useState("");
  const [creatingResume, setCreatingResume] = useState(false);
  const [createResumeMessage, setCreateResumeMessage] = useState<string | null>(null);
  const [resumeOriginFilter, setResumeOriginFilter] = useState<"all" | "uploaded" | "generated">(
    "all",
  );
  const [resumeSort, setResumeSort] = useState<"created_at" | "updated_at">("created_at");
  const [resumeOrder, setResumeOrder] = useState<"asc" | "desc">("desc");
  const [saveResumeOpen, setSaveResumeOpen] = useState(false);
  const [saveResumeTitle, setSaveResumeTitle] = useState("");
  const [savingResume, setSavingResume] = useState(false);
  const [saveResumeMessage, setSaveResumeMessage] = useState<string | null>(null);
  const [resumePanel, setResumePanel] = useState<"view" | "edit" | null>(null);
  const [editResumeTitle, setEditResumeTitle] = useState("");
  const [editResumeContent, setEditResumeContent] = useState<ResumeContentJson>(emptyResumeContent());
  const [resumeActionError, setResumeActionError] = useState<string | null>(null);
  const [deletingResumeId, setDeletingResumeId] = useState<string | null>(null);
  const [savingEditResume, setSavingEditResume] = useState(false);
  const [pendingParseId, setPendingParseId] = useState<string | null>(null);
  const [uploadNotice, setUploadNotice] = useState<string | null>(null);

  const loadResumes = useCallback(async () => {
    const { status, body } = await listResumes({
      origin: resumeOriginFilter,
      sort: resumeSort,
      order: resumeOrder,
    });
    if (status >= 200 && status < 300 && body.data) {
      setResumes(body.data.items);
      setSelected((current) => {
        if (!current) return current;
        const updated = body.data?.items.find((item) => item.id === current.id);
        return updated ?? current;
      });
    }
  }, [resumeOriginFilter, resumeSort, resumeOrder]);

  const loadProfile = useCallback(async () => {
    const { status, body } = await getMyProfile();
    if (status >= 200 && status < 300 && body.data?.content) {
      setProfileContent({ ...emptyResumeContent(), ...body.data.content });
    }
  }, []);

  const buildJobFilters = useCallback(() => {
    const skills = jobSkills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const minYears = jobMinYears.trim() ? Number(jobMinYears) : undefined;
    return {
      query: jobQuery || undefined,
      location: jobLocation || undefined,
      country: jobCountry || undefined,
      remote_type: jobRemoteType || undefined,
      skills: skills.length ? skills : undefined,
      experience_level: jobExperience || undefined,
      min_experience_years:
        minYears != null && !Number.isNaN(minYears) ? minYears : undefined,
      include_demo: includeDemo,
      include_remotive: includeRemotive,
      include_naukri: includeNaukri,
      limit: 20,
    };
  }, [
    jobQuery,
    jobLocation,
    jobCountry,
    jobRemoteType,
    jobSkills,
    jobExperience,
    jobMinYears,
    includeDemo,
    includeRemotive,
    includeNaukri,
  ]);

  const loadJobs = useCallback(async () => {
    const filters = buildJobFilters();
    const { status, body } = await listJobs({
      q: filters.query,
      location: filters.location,
      country: filters.country,
      remote_type: filters.remote_type,
      skills: filters.skills?.join(","),
      experience_level: filters.experience_level,
      min_experience_years: filters.min_experience_years,
    });
    if (status >= 200 && status < 300 && body.data) {
      setJobs(body.data.items);
      setJobsTotal(body.data.total);
    }
  }, [buildJobFilters]);

  const loadMatches = useCallback(async () => {
    const { status, body } = await listMatches();
    if (status >= 200 && status < 300 && body.data) {
      setMatches(body.data.items);
      setMatchesTotal(body.data.total);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { status, body } = await fetchMe();
        if (cancelled) return;
        if (status === 401) {
          router.replace("/login");
          return;
        }
        if (status >= 200 && status < 300 && body.data) {
          setMe(body.data);
          const providers = await getJobProviders();
          if (!cancelled && providers.status >= 200 && providers.status < 300 && providers.body.data) {
            setNaukriStatus(providers.body.data.naukri);
            if (providers.body.data.naukri.ready) {
              setIncludeNaukri(true);
              setJobLocation(
                (prev) => prev || providers.body.data!.naukri.default_location || "Bengaluru",
              );
              setJobCountry((prev) => prev || "india");
            }
          }
          await Promise.all([loadJobs(), loadMatches(), loadProfile()]);
        } else {
          setError(body.errors[0]?.message ?? "Failed to load profile.");
        }
      } catch {
        if (!cancelled) setError("Unable to reach the API.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, loadJobs, loadMatches, loadProfile]);

  useEffect(() => {
    if (!me) return;
    void loadResumes();
  }, [me, loadResumes]);

  useEffect(() => {
    const pending = resumes.some((r) => r.status === "parsing");
    if (!pending) return;
    const timer = window.setInterval(() => {
      void loadResumes();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [resumes, loadResumes]);

  useEffect(() => {
    if (!pendingParseId) return;
    const item = resumes.find((r) => r.id === pendingParseId);
    if (!item) return;
    if (item.status === "extracted" || item.status === "needs_review") {
      setPendingParseId(null);
      setUploadNotice(
        item.status === "needs_review"
          ? "Extraction saved with limited fields — review and fill what’s missing."
          : "Extraction saved as a resume record. Review and edit any details.",
      );
      void (async () => {
        await onEditResume(item);
      })();
    } else if (item.status === "parse_failed") {
      setPendingParseId(null);
      setUploadError("Could not extract text from that file. You can still try Re-parse.");
    }
  }, [resumes, pendingParseId]);

  useEffect(() => {
    if (selected || resumes.length === 0) return;
    const withContent = resumes.find((r) => r.content);
    if (withContent) setSelected(withContent);
  }, [resumes, selected]);


  useEffect(() => {
    setTrackedJobs(readTrackedJobs());
  }, []);

  function upsertTrackedJob(
    job: { id: string; title: string; company?: string | null; url?: string | null },
    status: TrackerStatus = "interested",
  ) {
    setTrackedJobs((prev) => {
      const next: TrackedJob[] = [
        {
          id: job.id,
          title: job.title,
          company: job.company ?? null,
          url: job.url ?? null,
          status,
          updatedAt: new Date().toISOString(),
        },
        ...prev.filter((item) => item.id !== job.id),
      ];
      writeTrackedJobs(next);
      return next;
    });
  }

  function updateTrackedStatus(id: string, status: TrackerStatus) {
    setTrackedJobs((prev) => {
      const next = prev.map((item) =>
        item.id === id ? { ...item, status, updatedAt: new Date().toISOString() } : item,
      );
      writeTrackedJobs(next);
      return next;
    });
  }

  function removeTrackedJob(id: string) {
    setTrackedJobs((prev) => {
      const next = prev.filter((item) => item.id !== id);
      writeTrackedJobs(next);
      return next;
    });
  }

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  async function onUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setUploadError("Choose a PDF or Word file first.");
      return;
    }
    setUploadError(null);
    setUploadNotice(null);
    setUploading(true);
    try {
      const { status, body } = await uploadResume(file);
      if (status >= 200 && status < 300 && body.data) {
        setFile(null);
        setSelected(body.data);
        setPendingParseId(body.data.id);
        setUploadNotice("Uploaded — extracting into the standard resume schema…");
        await loadResumes();
      } else {
        setUploadError(body.errors[0]?.message ?? "Upload failed.");
      }
    } catch {
      setUploadError("Unable to reach the API.");
    } finally {
      setUploading(false);
    }
  }

  async function onSelect(resume: ResumeItem) {
    setSelected(resume);
    try {
      const { status, body } = await getResume(resume.id);
      if (status >= 200 && status < 300 && body.data) {
        setSelected(body.data);
      }
    } catch {
      // Keep list selection if detail fetch fails.
    }
  }

  async function onParse(resumeId: string) {
    setParsingId(resumeId);
    setUploadError(null);
    try {
      const { status, body } = await parseResume(resumeId);
      if (status >= 200 && status < 300 && body.data) {
        setSelected(body.data);
        await loadResumes();
      } else {
        setUploadError(body.errors[0]?.message ?? "Parse failed.");
      }
    } catch {
      setUploadError("Unable to reach the API.");
    } finally {
      setParsingId(null);
    }
  }

  async function onViewResume(resume: ResumeItem) {
    setResumeActionError(null);
    setResumePanel("view");
    await onSelect(resume);
  }

  async function onEditResume(resume: ResumeItem) {
    setResumeActionError(null);
    setResumePanel("edit");
    await onSelect(resume);
    const { status, body } = await getResume(resume.id);
    const data = status >= 200 && status < 300 && body.data ? body.data : resume;
    setSelected(data);
    setEditResumeTitle(data.title || "");
    setEditResumeContent({ ...emptyResumeContent(), ...(data.content || {}) });
  }

  async function onSaveEditedResume(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    const title = editResumeTitle.trim();
    if (!title) {
      setResumeActionError("Resume name is required.");
      return;
    }
    setSavingEditResume(true);
    setResumeActionError(null);
    try {
      const { status, body } = await updateResume(selected.id, {
        title,
        content: editResumeContent,
      });
      if (status >= 200 && status < 300 && body.data) {
        setSelected(body.data);
        setResumePanel("view");
        await loadResumes();
      } else {
        setResumeActionError(body.errors[0]?.message ?? "Could not save resume.");
      }
    } catch {
      setResumeActionError("Unable to reach the API.");
    } finally {
      setSavingEditResume(false);
    }
  }

  async function onDeleteResume(resume: ResumeItem) {
    const name = resume.title || "this resume";
    if (!window.confirm(`Delete “${name}”? This cannot be undone.`)) return;
    setDeletingResumeId(resume.id);
    setResumeActionError(null);
    try {
      const { status, body } = await deleteResume(resume.id);
      if (status >= 200 && status < 300) {
        if (selected?.id === resume.id) {
          setSelected(null);
          setResumePanel(null);
        }
        await loadResumes();
      } else {
        setResumeActionError(body.errors[0]?.message ?? "Could not delete resume.");
      }
    } catch {
      setResumeActionError("Unable to reach the API.");
    } finally {
      setDeletingResumeId(null);
    }
  }

  async function onDiscover(event: FormEvent) {
    event.preventDefault();
    setJobsError(null);
    setDiscovering(true);
    try {
      const { status, body } = await discoverJobs(buildJobFilters());
      if (status >= 200 && status < 300 && body.data) {
        await loadJobs();
        if (body.data.warnings?.length) {
          setJobsError(body.data.warnings.join(" "));
        }
        if (body.data.items[0]) setSelectedJob(body.data.items[0]);
      } else {
        setJobsError(body.errors[0]?.message ?? "Job discovery failed.");
      }
    } catch {
      setJobsError("Unable to reach the API.");
    } finally {
      setDiscovering(false);
    }
  }

  async function onSearchJobs(event: FormEvent) {
    event.preventDefault();
    setJobsError(null);
    await loadJobs();
  }

  async function onRunMatching() {
    setMatchesError(null);
    setMatching(true);
    try {
      const { status, body } = await runMatching({
        resume_id: selected?.id,
        limit: 50,
        min_score: 0,
      });
      if (status >= 200 && status < 300 && body.data) {
        setMatches(body.data.items);
        setMatchesTotal(body.data.matched);
        setSelectedMatch(body.data.items[0] ?? null);
      } else {
        setMatchesError(body.errors[0]?.message ?? "Matching failed.");
      }
    } catch {
      setMatchesError("Unable to reach the API.");
    } finally {
      setMatching(false);
    }
  }

  async function onRunJobDiscoveryAgent() {
    setJobsError(null);
    setAgentTrace(null);
    setRunningAgent(true);
    try {
      const { status, body } = await runJobDiscoveryAgent(buildJobFilters());
      if (status >= 200 && status < 300 && body.data) {
        await loadJobs();
        const warnings = body.data.warnings?.join(" ") || "";
        setAgentTrace(
          `Agent ${body.data.agent} ${body.data.agent_version}: ` +
            `Tools: ${body.data.tool_trace.map((t) => String(t.tool)).join(" → ")}. ${warnings}`,
        );
        if (body.data.items[0]) setSelectedJob(body.data.items[0]);
      } else {
        setJobsError(body.errors[0]?.message ?? "Agent run failed.");
      }
    } catch {
      setJobsError("Unable to reach the API.");
    } finally {
      setRunningAgent(false);
    }
  }

  async function onFetchLinkedInJob() {
    setTailorError(null);
    setFetchingLinkedIn(true);
    try {
      const { status, body } = await ingestLinkedInJobUrl({
        url: linkedinUrl.trim(),
        description_override: linkedinDesc.trim() || undefined,
      });
      if (status >= 200 && status < 300 && body.data) {
        const job = body.data.job;
        setSelectedJob(job);
        setCoverLetter(null);
        if (job.description?.trim()) {
          setLinkedinDesc(job.description);
        }
        if (job.canonical_url) {
          setLinkedinUrl(job.canonical_url);
        }
        upsertTrackedJob(
          {
            id: job.id,
            title: job.title,
            company: job.company?.name ?? null,
            url: job.canonical_url,
          },
          "interested",
        );
        await loadJobs();
      } else {
        setTailorError(body.errors[0]?.message ?? "Could not fetch LinkedIn job.");
      }
    } catch {
      setTailorError("Unable to reach the API.");
    } finally {
      setFetchingLinkedIn(false);
    }
  }

  async function onSuggestTailor() {
    const resume =
      selected?.content
        ? selected
        : resumes.find((item) => item.content) ?? selected;
    if (!resume?.id || !resume.content) {
      setTailorError("Upload and parse a resume in the Resumes module first, then come back here.");
      return;
    }
    if (resume.id !== selected?.id) {
      setSelected(resume);
    }
    setTailorError(null);
    setTailoring(true);
    setAppliedContent(null);
    try {
      const { status, body } = await tailorResume(resume.id, {
        job_posting_id: selectedJob?.id,
        job_url: !selectedJob ? linkedinUrl.trim() || undefined : undefined,
        description_override: linkedinDesc.trim() || selectedJob?.description || undefined,
      });
      if (status >= 200 && status < 300 && body.data) {
        setTailor(body.data);
        setSelectedSuggestionIds(
          body.data.suggestions.filter((s) => s.selected_by_default).map((s) => s.id),
        );
        // Show proposed side-by-side immediately (before explicit Apply).
        setAppliedContent(null);
        if (body.data.job_posting_id) {
          setSelectedJob((prev) =>
            prev && prev.id === body.data!.job_posting_id
              ? {
                  ...prev,
                  title: body.data!.job_title,
                  description: linkedinDesc.trim() || prev.description,
                  canonical_url: body.data!.job_url ?? prev.canonical_url,
                }
              : {
                  id: body.data!.job_posting_id,
                  title: body.data!.job_title,
                  description: linkedinDesc.trim() || null,
                  location: null,
                  remote_type: null,
                  compensation: null,
                  requirements: null,
                  status: "normalized",
                  posted_at: null,
                  canonical_url: body.data!.job_url,
                  company: body.data!.job_company
                    ? {
                        id: "temp",
                        name: body.data!.job_company,
                        website: null,
                        industry: null,
                      }
                    : null,
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                },
          );
        }
        // Scroll comparison into view on next paint.
        window.setTimeout(() => {
          document.getElementById("tailor-comparison")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 50);
      } else {
        setTailorError(body.errors[0]?.message ?? "Could not generate suggestions.");
      }
    } catch {
      setTailorError("Unable to reach the API.");
    } finally {
      setTailoring(false);
    }
  }

  async function onApplySuggestions() {
    if (!selected?.id || !tailor) return;
    setTailorError(null);
    setTailoring(true);
    setSaveResumeMessage(null);
    try {
      const { status, body } = await tailorResume(selected.id, {
        job_posting_id: tailor.job_posting_id,
        selected_suggestion_ids: selectedSuggestionIds,
      });
      if (status >= 200 && status < 300 && body.data) {
        const applied = body.data.applied_content ?? body.data.proposed_content;
        setAppliedContent(applied);
        setTailor(body.data);
        upsertTrackedJob(
          {
            id: body.data.job_posting_id,
            title: body.data.job_title,
            company: body.data.job_company,
            url: body.data.job_url,
          },
          "tailored",
        );
        const defaultName = [body.data.job_company, body.data.job_title]
          .filter(Boolean)
          .join(" ")
          .trim();
        setSaveResumeTitle(defaultName || "Tailored resume");
        setSaveResumeOpen(true);
      } else {
        setTailorError(body.errors[0]?.message ?? "Could not apply suggestions.");
      }
    } catch {
      setTailorError("Unable to reach the API.");
    } finally {
      setTailoring(false);
    }
  }

  async function onSaveAppliedResume(e: FormEvent) {
    e.preventDefault();
    if (!appliedContent || !selected?.id || !tailor) return;
    const title = saveResumeTitle.trim();
    if (!title) {
      setSaveResumeMessage("Enter a resume name.");
      return;
    }
    setSavingResume(true);
    setSaveResumeMessage(null);
    try {
      const { status, body } = await saveResumeFromContent({
        title,
        content: appliedContent,
        parent_resume_id: selected.id,
        job_posting_id: tailor.job_posting_id,
      });
      if (status >= 200 && status < 300 && body.data) {
        setSaveResumeOpen(false);
        setSaveResumeMessage(`Saved “${body.data.title}” under Resumes.`);
        await loadResumes();
        router.push("/dashboard/resumes");
      } else {
        setSaveResumeMessage(body.errors[0]?.message ?? "Could not save resume.");
      }
    } catch {
      setSaveResumeMessage("Unable to reach the API.");
    } finally {
      setSavingResume(false);
    }
  }

  async function onSaveProfile(e: FormEvent) {
    e.preventDefault();
    setProfileError(null);
    setProfileSaved(false);
    setProfileSaving(true);
    try {
      const { status, body } = await updateMyProfile(profileContent);
      if (status >= 200 && status < 300 && body.data?.content) {
        setProfileContent({ ...emptyResumeContent(), ...body.data.content });
        setProfileSaved(true);
        const meRes = await fetchMe();
        if (meRes.status >= 200 && meRes.status < 300 && meRes.body.data) {
          setMe(meRes.body.data);
        }
      } else {
        setProfileError(body.errors[0]?.message ?? "Could not save profile.");
      }
    } catch {
      setProfileError("Unable to reach the API.");
    } finally {
      setProfileSaving(false);
    }
  }

  function openCreateResumeFromProfile() {
    setCreateResumeMessage(null);
    const hint =
      profileContent.headline ||
      profileContent.personal?.job_title ||
      profileContent.contact?.name ||
      "My resume";
    setCreateResumeTitle(String(hint));
    setCreateResumeOpen(true);
  }

  async function onCreateResumeFromProfile(e: FormEvent) {
    e.preventDefault();
    const title = createResumeTitle.trim();
    if (!title) {
      setCreateResumeMessage("Enter a resume name.");
      return;
    }
    setCreatingResume(true);
    setCreateResumeMessage(null);
    setProfileError(null);
    try {
      let contentToSave = profileContent;
      const profileRes = await updateMyProfile(profileContent);
      if (profileRes.status >= 200 && profileRes.status < 300 && profileRes.body.data?.content) {
        contentToSave = { ...emptyResumeContent(), ...profileRes.body.data.content };
        setProfileContent(contentToSave);
        setProfileSaved(true);
      }

      const { status, body } = await saveResumeFromContent({
        title,
        content: contentToSave,
      });
      if (status >= 200 && status < 300 && body.data) {
        setCreateResumeOpen(false);
        setCreateResumeMessage(`Created “${body.data.title}” in Resumes.`);
        await loadResumes();
        router.push("/dashboard/resumes");
        setSelected(body.data);
        setResumePanel("view");
      } else {
        setCreateResumeMessage(body.errors[0]?.message ?? "Could not create resume.");
      }
    } catch {
      setCreateResumeMessage("Unable to reach the API.");
    } finally {
      setCreatingResume(false);
    }
  }

  async function onGenerateCoverLetter() {
    const resume =
      selected?.content
        ? selected
        : resumes.find((item) => item.content) ?? selected;
    if (!resume?.id || !resume.content) {
      setTailorError("Upload and parse a resume in the Resumes module first, then come back here.");
      return;
    }
    if (!selectedJob && !linkedinUrl.trim() && !linkedinDesc.trim()) {
      setTailorError("Fetch a LinkedIn job first (or paste a URL / description).");
      return;
    }
    if (resume.id !== selected?.id) {
      setSelected(resume);
    }
    setTailorError(null);
    setGeneratingCoverLetter(true);
    try {
      const { status, body } = await generateCoverLetter(resume.id, {
        job_posting_id: selectedJob?.id,
        job_url: !selectedJob ? linkedinUrl.trim() || undefined : undefined,
        description_override: linkedinDesc.trim() || selectedJob?.description || undefined,
      });
      if (status >= 200 && status < 300 && body.data) {
        setCoverLetter(body.data);
        window.setTimeout(() => {
          document.getElementById("cover-letter-preview")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 50);
      } else {
        setTailorError(body.errors[0]?.message ?? "Could not generate cover letter.");
      }
    } catch {
      setTailorError("Unable to reach the API.");
    } finally {
      setGeneratingCoverLetter(false);
    }
  }

  function toggleSuggestion(id: string) {
    setSelectedSuggestionIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
    setAppliedContent(null);
  }

  return (
    <div className="space-y-6">
            {loading ? <p className="text-sm text-slate-500">Loading…</p> : null}
            {error ? <p className="text-sm text-red-600">{error}</p> : null}

            {section === "profile" ? (
              <form
                onSubmit={(e) => void onSaveProfile(e)}
                className="rounded-xl border border-slate-200 bg-white p-6 space-y-6"
              >
                <div>
                  <h2 className="text-lg font-semibold">Profile</h2>
                  <p className="text-sm text-slate-600">
                    Same JSON backbone as uploaded and tailored resumes — contact, summary,
                    experience, education, skills, plus optional sections.
                  </p>
                  {me ? (
                    <p className="mt-2 text-sm text-slate-500">
                      Account: {me.user.display_name || "—"} · {me.user.email}
                    </p>
                  ) : null}
                </div>

                <fieldset className="space-y-3">
                  <legend className="text-sm font-semibold text-slate-800">Contact header</legend>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {(
                      [
                        ["name", "Full name"],
                        ["phone", "Phone"],
                        ["email", "Professional email"],
                        ["location", "Location"],
                      ] as const
                    ).map(([key, label]) => (
                      <label key={key} className="block text-sm">
                        <span className="text-slate-600">{label}</span>
                        <input
                          value={profileContent.contact?.[key] ?? ""}
                          onChange={(e) =>
                            setProfileContent((prev) => ({
                              ...prev,
                              contact: { ...prev.contact, [key]: e.target.value || null },
                            }))
                          }
                          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                        />
                      </label>
                    ))}
                  </div>
                  <label className="block text-sm">
                    <span className="text-slate-600">LinkedIn / profile links (one per line)</span>
                    <textarea
                      rows={2}
                      value={(profileContent.contact?.links || profileContent.links || []).join(
                        "\n",
                      )}
                      onChange={(e) => {
                        const links = e.target.value
                          .split("\n")
                          .map((s) => s.trim())
                          .filter(Boolean);
                        setProfileContent((prev) => ({
                          ...prev,
                          links,
                          contact: { ...prev.contact, links },
                        }));
                      }}
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                </fieldset>

                <fieldset className="space-y-3">
                  <legend className="text-sm font-semibold text-slate-800">
                    Professional summary
                  </legend>
                  <label className="block text-sm">
                    <span className="text-slate-600">Job title / headline</span>
                    <input
                      value={profileContent.headline ?? profileContent.personal?.job_title ?? ""}
                      onChange={(e) =>
                        setProfileContent((prev) => ({
                          ...prev,
                          headline: e.target.value || null,
                          personal: { ...prev.personal, job_title: e.target.value || null },
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="text-slate-600">Summary (2–3 sentences)</span>
                    <textarea
                      rows={4}
                      value={profileContent.summary ?? ""}
                      onChange={(e) =>
                        setProfileContent((prev) => ({
                          ...prev,
                          summary: e.target.value || null,
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                </fieldset>

                <fieldset className="space-y-3">
                  <legend className="text-sm font-semibold text-slate-800">Skills & hobbies</legend>
                  <label className="block text-sm">
                    <span className="text-slate-600">Skills (comma-separated)</span>
                    <textarea
                      rows={2}
                      value={(profileContent.skills || []).join(", ")}
                      onChange={(e) =>
                        setProfileContent((prev) => ({
                          ...prev,
                          skills: e.target.value
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="text-slate-600">Hobbies / interests (comma-separated)</span>
                    <input
                      value={(profileContent.hobbies || []).join(", ")}
                      onChange={(e) =>
                        setProfileContent((prev) => ({
                          ...prev,
                          hobbies: e.target.value
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                        }))
                      }
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                </fieldset>

                <ProfileStructuredSections
                  content={profileContent}
                  onChange={setProfileContent}
                />

                {profileError ? <p className="text-sm text-red-600">{profileError}</p> : null}
                {profileSaved && !createResumeOpen ? (
                  <p className="text-sm text-emerald-700">Profile saved.</p>
                ) : null}
                {createResumeMessage && !createResumeOpen ? (
                  <p className="text-sm text-emerald-700">{createResumeMessage}</p>
                ) : null}

                <div className="flex flex-wrap gap-2">
                  <button
                    type="submit"
                    disabled={profileSaving || creatingResume}
                    className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
                  >
                    {profileSaving ? "Saving…" : "Save profile"}
                  </button>
                  <button
                    type="button"
                    onClick={openCreateResumeFromProfile}
                    disabled={creatingResume}
                    className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
                  >
                    Create resume
                  </button>
                </div>

                {createResumeOpen ? (
                  <div className="rounded-lg border border-brand-200 bg-brand-50/50 p-4 space-y-3">
                    <p className="text-sm font-medium text-slate-800">Create resume from profile</p>
                    <p className="text-xs text-slate-600">
                      Saves your current profile as a generated resume row (same JSON schema). Name
                      it something you’ll recognize — e.g. “base resume” or “data engineer 2026”.
                    </p>
                    <label className="block text-sm">
                      <span className="text-slate-600">Resume name</span>
                      <input
                        value={createResumeTitle}
                        onChange={(e) => setCreateResumeTitle(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white"
                        placeholder="base resume"
                        autoFocus
                      />
                    </label>
                    {createResumeMessage ? (
                      <p className="text-sm text-red-600">{createResumeMessage}</p>
                    ) : null}
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={(e) => void onCreateResumeFromProfile(e)}
                        disabled={creatingResume}
                        className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
                      >
                        {creatingResume ? "Creating…" : "Save to Resumes"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setCreateResumeOpen(false)}
                        className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-white"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : null}
              </form>
            ) : null}
            {section === "boards" ? (
<div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
          <div>
            <h2 className="text-lg font-semibold">Job boards (Cursor MCP)</h2>
            <p className="text-sm text-slate-600">
              Personal LinkedIn and Naukri access runs in Cursor MCP, not this dashboard.
            </p>
          </div>
          <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
            <li>
              LinkedIn: enable <code className="text-xs">mcp-server-linkedin</code> (already
              logged in via <code className="text-xs">uvx … --login</code>)
            </li>
            <li>
              Naukri: fill <code className="text-xs">.env.naukri</code>, enable{" "}
              <code className="text-xs">naukri-mcp</code>, then search/apply from Agent chat
            </li>
          </ul>
        </div>
            ) : null}
            {section === "resumes" ? (
              <p className="text-sm text-slate-500">Opening Resumes…</p>
            ) : null}
            {section === "tailor" ? (
<div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div>
            <h2 className="text-lg font-semibold">Tailor resume for a LinkedIn job</h2>
            <p className="text-sm text-slate-600">
              Paste a LinkedIn job link, fetch the posting, then suggest tweaks and compare
              current vs suggested side by side (no PDF edits yet).
            </p>
          </div>

          <div className="space-y-3">
            <label className="block text-sm">
              <span className="text-slate-600">Resume to tailor</span>
              <select
                value={selected?.id ?? ""}
                onChange={(e) => {
                  const next = resumes.find((item) => item.id === e.target.value);
                  if (next) void onSelect(next);
                }}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                <option value="">Select a parsed resume…</option>
                {resumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {(resume.title || "Untitled") +
                      (resume.content ? "" : " (not parsed yet)")}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">LinkedIn job URL</span>
              <input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://www.linkedin.com/jobs/view/4252026496/"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void onFetchLinkedInJob()}
                disabled={fetchingLinkedIn || !linkedinUrl.trim()}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
              >
                {fetchingLinkedIn ? "Fetching…" : "Fetch job"}
              </button>
              <button
                type="button"
                onClick={() => void onSuggestTailor()}
                disabled={
                  tailoring ||
                  (!selected?.content && !resumes.some((r) => r.content)) ||
                  (!selectedJob && !linkedinUrl.trim() && !linkedinDesc.trim())
                }
                className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
              >
                {tailoring ? "Working…" : "Suggest resume tweaks"}
              </button>
              <button
                type="button"
                onClick={() => void onGenerateCoverLetter()}
                disabled={
                  generatingCoverLetter ||
                  (!selected?.content && !resumes.some((r) => r.content)) ||
                  (!selectedJob && !linkedinUrl.trim() && !linkedinDesc.trim())
                }
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
              >
                {generatingCoverLetter ? "Generating…" : "Generate cover letter"}
              </button>
            </div>
            {selectedJob ? (
              <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 space-y-2 text-sm">
                <p className="text-slate-600">
                  Target job: <span className="font-medium text-slate-900">{selectedJob.title}</span>
                  {selectedJob.company?.name ? ` · ${selectedJob.company.name}` : ""}
                  {selectedJob.location ? ` · ${selectedJob.location}` : ""}
                </p>
                {selectedJob.requirements?.skills?.length ? (
                  <p className="text-slate-600">
                    Skills detected:{" "}
                    <span className="text-slate-800">
                      {selectedJob.requirements.skills.slice(0, 12).join(", ")}
                    </span>
                  </p>
                ) : null}
              </div>
            ) : null}
            <label className="block text-sm">
              <span className="text-slate-600">
                Job description{" "}
                <span className="text-slate-400">
                  (filled after Fetch — edit if you want to override)
                </span>
              </span>
              <textarea
                value={linkedinDesc}
                onChange={(e) => setLinkedinDesc(e.target.value)}
                rows={10}
                placeholder="Click Fetch job to load the LinkedIn posting here…"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
              />
            </label>
            {tailorError ? <p className="text-sm text-red-600">{tailorError}</p> : null}
          </div>

          {tailor ? (
            <div id="tailor-comparison" className="space-y-4 border-t border-slate-100 pt-4">
              <div className="text-sm text-slate-600 space-y-1">
                <p>
                  Suggestions for <span className="font-medium">{tailor.job_title}</span>
                  {tailor.job_company ? ` at ${tailor.job_company}` : ""}
                </p>
                <p>
                  Match preview:{" "}
                  {Math.round((tailor.match_preview.score ?? 0) * 100)}% · missing skills:{" "}
                  {(tailor.match_preview.missing_skills || []).slice(0, 8).join(", ") || "none"}
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <h3 className="text-sm font-semibold mb-2">Current resume</h3>
                  <pre className="whitespace-pre-wrap text-xs text-slate-700 max-h-96 overflow-auto">
                    {formatResumePane(tailor.current_content)}
                  </pre>
                </div>
                <div className="rounded-lg border border-brand-200 bg-brand-50/40 p-3">
                  <h3 className="text-sm font-semibold mb-2">
                    {appliedContent ? "Applied changes" : "Suggested resume"}
                  </h3>
                  <pre className="whitespace-pre-wrap text-xs text-slate-700 max-h-96 overflow-auto">
                    {formatResumePane(appliedContent ?? tailor.proposed_content)}
                  </pre>
                </div>
              </div>

              <ul className="space-y-2">
                {tailor.suggestions.map((suggestion) => (
                  <li
                    key={suggestion.id}
                    className="rounded-lg border border-slate-100 px-3 py-2 text-sm"
                  >
                    <label className="flex gap-3 items-start cursor-pointer">
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={selectedSuggestionIds.includes(suggestion.id)}
                        onChange={() => toggleSuggestion(suggestion.id)}
                      />
                      <span>
                        <span className="font-medium">{suggestion.title}</span>
                        <span className="block text-slate-600">{suggestion.rationale}</span>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                onClick={() => void onApplySuggestions()}
                disabled={tailoring || selectedSuggestionIds.length === 0}
                className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
              >
                {tailoring ? "Applying…" : "Apply selected changes"}
              </button>
              {saveResumeMessage && !saveResumeOpen ? (
                <p className="text-sm text-emerald-700">{saveResumeMessage}</p>
              ) : null}
              {saveResumeOpen ? (
                <form
                  onSubmit={(e) => void onSaveAppliedResume(e)}
                  className="rounded-lg border border-brand-200 bg-brand-50/50 p-4 space-y-3"
                >
                  <p className="text-sm font-medium text-slate-800">Save as new resume</p>
                  <p className="text-xs text-slate-600">
                    Stores the applied JSON under Resumes (generated). Name it something you’ll
                    recognize later — e.g. “google data engineer”.
                  </p>
                  <label className="block text-sm">
                    <span className="text-slate-600">Resume name</span>
                    <input
                      value={saveResumeTitle}
                      onChange={(e) => setSaveResumeTitle(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white"
                      placeholder="google data engineer"
                      autoFocus
                    />
                  </label>
                  {saveResumeMessage ? (
                    <p className="text-sm text-red-600">{saveResumeMessage}</p>
                  ) : null}
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="submit"
                      disabled={savingResume}
                      className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
                    >
                      {savingResume ? "Saving…" : "Save resume"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setSaveResumeOpen(false)}
                      className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-white"
                    >
                      Skip for now
                    </button>
                  </div>
                </form>
              ) : null}
              <p className="text-xs text-slate-500">
                Applying updates the preview. Saving creates a generated resume in the Resumes
                module — the original upload stays unchanged.
              </p>
            </div>
          ) : null}

          {coverLetter ? (
            <div id="cover-letter-preview" className="space-y-3 border-t border-slate-100 pt-4">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold">Cover letter</h3>
                  <p className="text-sm text-slate-600">
                    {coverLetter.subject}
                    {coverLetter.job_company ? ` · ${coverLetter.job_company}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    void navigator.clipboard.writeText(coverLetter.text);
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium hover:bg-slate-50"
                >
                  Copy
                </button>
              </div>
              {coverLetter.highlights?.matched_skills?.length ? (
                <p className="text-xs text-slate-500">
                  Emphasized skills: {coverLetter.highlights.matched_skills.join(", ")}
                </p>
              ) : null}
              <textarea
                value={coverLetter.text}
                onChange={(e) =>
                  setCoverLetter((prev) => (prev ? { ...prev, text: e.target.value } : prev))
                }
                rows={16}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-mono"
              />
              <p className="text-xs text-slate-500">
                Draft only — edit freely. Nothing is written to your resume PDF.
              </p>
            </div>
          ) : null}
        </div>
            ) : null}
            {section === "discovery" ? (
              <>
<div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div>
            <h2 className="text-lg font-semibold">Job discovery</h2>
            <p className="text-sm text-slate-600">
              Search saved jobs or discover new ones (demo, Remotive, optional Naukri).
            </p>
          </div>

          <form onSubmit={onDiscover} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="search"
                value={jobQuery}
                onChange={(e) => setJobQuery(e.target.value)}
                placeholder="Keywords — e.g. data engineer"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={(e) => void onSearchJobs(e as unknown as FormEvent)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
              >
                Search
              </button>
              <button
                type="submit"
                disabled={discovering}
                className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
              >
                {discovering ? "Discovering…" : "Discover"}
              </button>
              <button
                type="button"
                onClick={() => void onRunJobDiscoveryAgent()}
                disabled={runningAgent}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
              >
                {runningAgent ? "Agent running…" : "Run agent"}
              </button>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-slate-700">
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeDemo}
                  onChange={(e) => setIncludeDemo(e.target.checked)}
                />
                Demo
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeRemotive}
                  onChange={(e) => setIncludeRemotive(e.target.checked)}
                />
                Remotive
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeNaukri}
                  onChange={(e) => setIncludeNaukri(e.target.checked)}
                  disabled={naukriStatus != null && !naukriStatus.ready}
                />
                Naukri
                {naukriStatus?.ready ? (
                  <span className="text-xs text-emerald-700">ready</span>
                ) : (
                  <span className="text-xs text-slate-500">
                    {naukriStatus?.hint || "not configured"}
                  </span>
                )}
              </label>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <label className="text-xs text-slate-500 space-y-1">
                <span>Location</span>
                <input
                  type="text"
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                  placeholder="e.g. Remote, Bengaluru"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Country</span>
                <select
                  value={jobCountry}
                  onChange={(e) => setJobCountry(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="us">United States</option>
                  <option value="india">India</option>
                  <option value="uk">United Kingdom</option>
                  <option value="canada">Canada</option>
                  <option value="germany">Germany</option>
                  <option value="worldwide">Worldwide / Anywhere</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Remote type</span>
                <select
                  value={jobRemoteType}
                  onChange={(e) => setJobRemoteType(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Skills (comma-separated)</span>
                <input
                  type="text"
                  value={jobSkills}
                  onChange={(e) => setJobSkills(e.target.value)}
                  placeholder="e.g. Python, Spark, SQL"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Experience level</span>
                <select
                  value={jobExperience}
                  onChange={(e) => setJobExperience(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="junior">Junior / entry</option>
                  <option value="mid">Mid</option>
                  <option value="senior">Senior</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Min years (optional)</span>
                <input
                  type="number"
                  min={0}
                  max={40}
                  value={jobMinYears}
                  onChange={(e) => setJobMinYears(e.target.value)}
                  placeholder="e.g. 5"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
            </div>
            <p className="text-xs text-slate-500">
              Filters apply to Search (catalog) and Discover / Run agent. For Naukri,
              prefer Location + Min years; leave Experience level on Any (title
              heuristics like “junior” hide most Naukri listings).
            </p>
          </form>
          {jobsError ? <p className="text-sm text-red-600">{jobsError}</p> : null}
          {agentTrace ? <p className="text-xs text-slate-500">{agentTrace}</p> : null}
          <p className="text-xs text-slate-500">{jobsTotal} jobs in catalog</p>

          {jobs.length === 0 ? (
            <p className="text-sm text-slate-500">
              No jobs yet. Click Discover to ingest demo and remote listings.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
              {jobs.map((job) => (
                <li key={job.id}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-3 hover:bg-slate-50"
                    onClick={() => {
                      setSelectedJob(job);
                      upsertTrackedJob(
                        {
                          id: job.id,
                          title: job.title,
                          company: job.company?.name ?? null,
                          url: job.canonical_url,
                        },
                        "interested",
                      );
                    }}
                  >
                    <div className="flex justify-between gap-4 text-sm">
                      <div>
                        <p className="font-medium">{job.title}</p>
                        <p className="text-slate-600">
                          {job.company?.name || "Unknown company"}
                          {job.location ? ` · ${job.location}` : ""}
                        </p>
                      </div>
                      <div className="text-right text-slate-500">
                        <p className="capitalize">{job.remote_type || "—"}</p>
                        <p className="text-xs capitalize">{job.status}</p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedJob ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <h2 className="text-lg font-semibold">{selectedJob.title}</h2>
            <p className="text-sm text-slate-600">
              {selectedJob.company?.name || "Unknown company"}
              {selectedJob.location ? ` · ${selectedJob.location}` : ""}
              {selectedJob.remote_type ? ` · ${selectedJob.remote_type}` : ""}
            </p>
            {selectedJob.requirements?.skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Skills:</span>{" "}
                {selectedJob.requirements.skills.slice(0, 12).join(", ")}
              </p>
            ) : null}
            {selectedJob.canonical_url ? (
              <a
                href={selectedJob.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-brand-600 hover:underline"
              >
                Open posting
              </a>
            ) : null}
            {selectedJob.description ? (
              <div
                className="prose prose-sm max-w-none max-h-80 overflow-auto rounded-lg bg-slate-50 p-3 text-sm text-slate-700"
                dangerouslySetInnerHTML={{
                  __html: selectedJob.description.slice(0, 8000),
                }}
              />
            ) : (
              <p className="text-sm text-slate-500">No description available.</p>
            )}
          </div>
        ) : null}
              </>
            ) : null}
            {section === "matches" ? (
              <>
<div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Job matches</h2>
              <p className="text-sm text-slate-600">
                Score discovered jobs against your parsed resume (explainable heuristic).
              </p>
            </div>
            <button
              type="button"
              onClick={() => void onRunMatching()}
              disabled={matching}
              className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            >
              {matching ? "Scoring…" : "Run matching"}
            </button>
          </div>
          {matchesError ? <p className="text-sm text-red-600">{matchesError}</p> : null}
          <p className="text-xs text-slate-500">{matchesTotal} saved matches</p>

          {matches.length === 0 ? (
            <p className="text-sm text-slate-500">
              No matches yet. Parse a resume, discover jobs, then run matching.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
              {matches.map((match) => (
                <li key={match.id}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-3 hover:bg-slate-50"
                    onClick={() => setSelectedMatch(match)}
                  >
                    <div className="flex justify-between gap-4 text-sm">
                      <div>
                        <p className="font-medium">{match.job?.title || "Job"}</p>
                        <p className="text-slate-600">
                          {match.job?.company?.name || "Unknown company"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-brand-700">
                          {Math.round(match.score * 100)}%
                        </p>
                        <p className="text-xs text-slate-500">{match.model_version}</p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedMatch ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <h2 className="text-lg font-semibold">
              Match · {Math.round(selectedMatch.score * 100)}%
            </h2>
            <p className="text-sm text-slate-600">
              {selectedMatch.job?.title}
              {selectedMatch.job?.company?.name
                ? ` · ${selectedMatch.job.company.name}`
                : ""}
            </p>
            {selectedMatch.explanation?.matched_skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Matched:</span>{" "}
                {selectedMatch.explanation.matched_skills.join(", ")}
              </p>
            ) : null}
            {selectedMatch.explanation?.missing_skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Gaps:</span>{" "}
                {selectedMatch.explanation.missing_skills.join(", ")}
              </p>
            ) : null}
            {selectedMatch.explanation?.reasons?.length ? (
              <ul className="text-sm text-slate-700 list-disc pl-5 space-y-1">
                {selectedMatch.explanation.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
              </>
            ) : null}

            {section === "tracker" ? (
              <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
                <div>
                  <h2 className="text-lg font-semibold">Job tracker</h2>
                  <p className="text-sm text-slate-600">
                    Track roles you fetch, tailor, or shortlist. Status is saved in this browser
                    for now.
                  </p>
                </div>
                {trackedJobs.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No tracked jobs yet. Fetch a LinkedIn job or apply tailor suggestions to add
                    one.
                  </p>
                ) : (
                  <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
                    {trackedJobs.map((job) => (
                      <li
                        key={job.id}
                        className="px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3 justify-between text-sm"
                      >
                        <div>
                          <p className="font-medium">{job.title}</p>
                          <p className="text-slate-600">{job.company || "Unknown company"}</p>
                          {job.url ? (
                            <a
                              href={job.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-brand-600 hover:underline"
                            >
                              Open posting
                            </a>
                          ) : null}
                        </div>
                        <div className="flex items-center gap-2">
                          <select
                            value={job.status}
                            onChange={(e) =>
                              updateTrackedStatus(job.id, e.target.value as TrackerStatus)
                            }
                            className="rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                          >
                            <option value="interested">Interested</option>
                            <option value="tailored">Tailored</option>
                            <option value="applied">Applied</option>
                            <option value="interview">Interview</option>
                            <option value="rejected">Rejected</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => removeTrackedJob(job.id)}
                            className="text-xs text-slate-500 hover:text-red-600"
                          >
                            Remove
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : null}
    </div>
  );
}
