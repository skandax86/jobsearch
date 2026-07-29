export type DashboardNavItem = {
  href: string;
  id: string;
  label: string;
  blurb: string;
  group: "workspace" | "jobs";
};

export const DASHBOARD_NAV: DashboardNavItem[] = [
  {
    id: "boards",
    href: "/dashboard/boards",
    label: "Job boards",
    blurb: "LinkedIn & Naukri MCP",
    group: "workspace",
  },
  {
    id: "profile",
    href: "/dashboard/profile",
    label: "Profile",
    blurb: "Contact, career & skills",
    group: "workspace",
  },
  {
    id: "resumes",
    href: "/dashboard/resumes",
    label: "Resumes",
    blurb: "Uploaded & generated",
    group: "workspace",
  },
  {
    id: "tailor",
    href: "/dashboard/tailor",
    label: "Tailor resume",
    blurb: "LinkedIn job tweaks",
    group: "workspace",
  },
  {
    id: "discovery",
    href: "/dashboard/discovery",
    label: "Job discovery",
    blurb: "Search & ingest",
    group: "jobs",
  },
  {
    id: "matches",
    href: "/dashboard/matches",
    label: "Job matches",
    blurb: "Score & gaps",
    group: "jobs",
  },
  {
    id: "tracker",
    href: "/dashboard/tracker",
    label: "Job tracker",
    blurb: "Application pipeline",
    group: "jobs",
  },
];

export function emptyResumeContent() {
  return {
    schema_version: "1.1",
    contact: { name: null, email: null, phone: null, location: null, links: [] as string[] },
    headline: null as string | null,
    summary: null as string | null,
    experience: [] as Record<string, unknown>[],
    education: [] as Record<string, unknown>[],
    skills: [] as string[],
    projects: [] as Record<string, unknown>[],
    certifications: [] as Record<string, unknown>[],
    awards: [] as Record<string, unknown>[],
    languages: [] as string[],
    hobbies: [] as string[],
    personal: {
      job_title: null as string | null,
      work_authorization: null as string | null,
      notes: null as string | null,
    },
    links: [] as string[],
  };
}

export function formatDateTime(value: string): string {
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

export function resumeOriginLabel(resume: {
  origin?: string | null;
  source_object_key?: string | null;
}): string {
  return resume.origin || (resume.source_object_key ? "uploaded" : "generated");
}
