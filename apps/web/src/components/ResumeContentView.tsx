"use client";

import type { ResumeContentJson } from "@/lib/api";

function dash(value: string | null | undefined): string {
  const text = value?.trim();
  return text ? text : "—";
}

function dateRange(
  start?: string | null,
  end?: string | null,
  isCurrent?: boolean,
): string {
  const from = start?.trim() || "—";
  if (isCurrent) return `${from} – Present`;
  const to = end?.trim() || "—";
  return `${from} – ${to}`;
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3 border-t border-slate-100 pt-4 first:border-t-0 first:pt-0">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {children}
    </section>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <div className="mt-0.5 text-sm text-slate-800 whitespace-pre-wrap">{value}</div>
    </div>
  );
}

function EntryCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4 space-y-3">
      <div>
        <p className="text-sm font-medium text-slate-900">{title}</p>
        {subtitle ? <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p> : null}
      </div>
      {children}
    </div>
  );
}

export function ResumeContentView({ content }: { content: ResumeContentJson }) {
  const contact = content.contact || {};
  const links = contact.links?.length ? contact.links : content.links || [];
  const experience = content.experience || [];
  const education = content.education || [];
  const projects = content.projects || [];
  const certifications = content.certifications || [];
  const awards = content.awards || [];
  const skills = content.skills || [];
  const hobbies = content.hobbies || [];

  return (
    <div className="space-y-6">
      <Section title="Contact header">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Full name" value={dash(contact.name)} />
          <Field label="Phone" value={dash(contact.phone)} />
          <Field label="Email" value={dash(contact.email)} />
          <Field label="Location" value={dash(contact.location)} />
        </div>
        <Field
          label="Links"
          value={
            links.length
              ? links.map((l, i) => <div key={`link-${i}`}>{l}</div>)
              : "—"
          }
        />
      </Section>

      <Section title="Professional summary">
        <Field
          label="Job title / headline"
          value={dash(content.headline || content.personal?.job_title)}
        />
        <Field label="Summary" value={dash(content.summary)} />
      </Section>

      <Section title="Skills & hobbies">
        <Field label="Skills" value={skills.length ? skills.join(", ") : "—"} />
        <Field label="Hobbies" value={hobbies.length ? hobbies.join(", ") : "—"} />
      </Section>

      <Section title="Work experience">
        {experience.length === 0 ? (
          <p className="text-sm text-slate-500">No work experience listed.</p>
        ) : (
          experience.map((item, index) => (
            <EntryCard
              key={item.id || `exp-${index}`}
              title={item.title || "Untitled role"}
              subtitle={[item.company, item.location].filter(Boolean).join(" · ") || undefined}
            >
              <Field
                label="Dates"
                value={dateRange(item.start_date, item.end_date, item.is_current)}
              />
              <Field label="Summary" value={dash(item.summary)} />
              {(item.bullets || []).length > 0 ? (
                <Field
                  label="Achievements"
                  value={
                    <ul className="list-disc pl-5 space-y-1">
                      {(item.bullets || []).map((b, i) => (
                        <li key={`exp-bullet-${index}-${i}`}>{b}</li>
                      ))}
                    </ul>
                  }
                />
              ) : null}
            </EntryCard>
          ))
        )}
      </Section>

      <Section title="Education">
        {education.length === 0 ? (
          <p className="text-sm text-slate-500">No education listed.</p>
        ) : (
          education.map((item, index) => (
            <EntryCard
              key={item.id || `edu-${index}`}
              title={item.institution || "Institution"}
              subtitle={[item.degree, item.specialization].filter(Boolean).join(" · ") || undefined}
            >
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="Location" value={dash(item.location)} />
                <Field
                  label="Dates"
                  value={dateRange(item.start_date, item.end_date, item.is_current)}
                />
                <Field
                  label="Score"
                  value={
                    item.score
                      ? `${item.score}${item.score_type ? ` (${item.score_type.toUpperCase()})` : ""}`
                      : "—"
                  }
                />
              </div>
              <Field label="Summary" value={dash(item.summary)} />
            </EntryCard>
          ))
        )}
      </Section>

      <Section title="Projects">
        {projects.length === 0 ? (
          <p className="text-sm text-slate-500">No projects listed.</p>
        ) : (
          projects.map((item, index) => (
            <EntryCard
              key={item.id || `proj-${index}`}
              title={item.title || "Untitled project"}
              subtitle={
                [item.organization, item.location].filter(Boolean).join(" · ") || undefined
              }
            >
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="URL" value={dash(item.url)} />
                <Field
                  label="Dates"
                  value={dateRange(item.start_date, item.end_date, item.is_current)}
                />
              </div>
              <Field label="Summary" value={dash(item.summary)} />
              {(item.technologies || []).length > 0 ? (
                <Field label="Technologies" value={(item.technologies || []).join(", ")} />
              ) : null}
              {(item.bullets || []).length > 0 ? (
                <Field
                  label="Highlights"
                  value={
                    <ul className="list-disc pl-5 space-y-1">
                      {(item.bullets || []).map((b, i) => (
                        <li key={`proj-bullet-${index}-${i}`}>{b}</li>
                      ))}
                    </ul>
                  }
                />
              ) : null}
            </EntryCard>
          ))
        )}
      </Section>

      <Section title="Certifications">
        {certifications.length === 0 ? (
          <p className="text-sm text-slate-500">No certifications listed.</p>
        ) : (
          certifications.map((item, index) => (
            <EntryCard
              key={item.id || `cert-${index}`}
              title={item.title || "Certification"}
              subtitle={item.issuer || undefined}
            >
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="Issued" value={dash(item.date)} />
                <Field label="Expires" value={dash(item.expiry_date)} />
                <Field label="Credential ID" value={dash(item.credential_id)} />
                <Field label="URL" value={dash(item.url)} />
              </div>
              <Field label="Summary" value={dash(item.summary)} />
            </EntryCard>
          ))
        )}
      </Section>

      <Section title="Awards">
        {awards.length === 0 ? (
          <p className="text-sm text-slate-500">No awards listed.</p>
        ) : (
          awards.map((item, index) => (
            <EntryCard
              key={item.id || `award-${index}`}
              title={item.title || "Award"}
              subtitle={[item.issuer, item.date].filter(Boolean).join(" · ") || undefined}
            >
              <Field label="Summary" value={dash(item.summary)} />
            </EntryCard>
          ))
        )}
      </Section>
    </div>
  );
}
