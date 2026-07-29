"use client";

import type {
  AwardEntry,
  CertificationEntry,
  EducationEntry,
  ExperienceEntry,
  ProjectEntry,
  ResumeContentJson,
} from "@/lib/api";

function newId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export function emptyExperience(): ExperienceEntry {
  return {
    id: newId("experience"),
    company: null,
    title: null,
    location: null,
    start_date: null,
    end_date: null,
    is_current: false,
    summary: null,
    bullets: [],
  };
}

export function emptyEducation(): EducationEntry {
  return {
    id: newId("education"),
    institution: null,
    degree: null,
    specialization: null,
    location: null,
    start_date: null,
    end_date: null,
    is_current: false,
    score: null,
    score_type: null,
    summary: null,
    details: [],
  };
}

export function emptyProject(): ProjectEntry {
  return {
    id: newId("project"),
    title: null,
    organization: null,
    url: null,
    location: null,
    start_date: null,
    end_date: null,
    is_current: false,
    summary: null,
    bullets: [],
    technologies: [],
  };
}

export function emptyCertification(): CertificationEntry {
  return {
    id: newId("certification"),
    title: null,
    issuer: null,
    date: null,
    expiry_date: null,
    credential_id: null,
    url: null,
    summary: null,
  };
}

export function emptyAward(): AwardEntry {
  return {
    id: newId("award"),
    title: null,
    issuer: null,
    date: null,
    summary: null,
  };
}

type Props = {
  content: ResumeContentJson;
  onChange: (next: ResumeContentJson) => void;
};

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="text-slate-600">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white";

function DateRangeFields({
  start,
  end,
  isCurrent,
  currentLabel,
  onStart,
  onEnd,
  onCurrent,
}: {
  start: string;
  end: string;
  isCurrent: boolean;
  currentLabel: string;
  onStart: (v: string) => void;
  onEnd: (v: string) => void;
  onCurrent: (v: boolean) => void;
}) {
  return (
    <div className="grid sm:grid-cols-3 gap-3 items-end">
      <Field label="Start date">
        <input
          value={start}
          onChange={(e) => onStart(e.target.value)}
          placeholder="Jan 2022"
          className={inputClass}
        />
      </Field>
      <Field label="End date">
        <input
          value={isCurrent ? "" : end}
          onChange={(e) => onEnd(e.target.value)}
          placeholder="Dec 2024"
          disabled={isCurrent}
          className={inputClass + " disabled:bg-slate-50 disabled:text-slate-400"}
        />
      </Field>
      <label className="flex items-center gap-2 text-sm text-slate-700 pb-2">
        <input
          type="checkbox"
          checked={isCurrent}
          onChange={(e) => onCurrent(e.target.checked)}
        />
        {currentLabel}
      </label>
    </div>
  );
}

function EntryCard({
  title,
  onRemove,
  children,
}: {
  title: string;
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-800">{title}</p>
        <button
          type="button"
          onClick={onRemove}
          className="text-xs text-red-600 hover:underline"
        >
          Remove
        </button>
      </div>
      {children}
    </div>
  );
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
    >
      {label}
    </button>
  );
}

export function ProfileStructuredSections({ content, onChange }: Props) {
  const experience = content.experience || [];
  const education = content.education || [];
  const projects = content.projects || [];
  const certifications = content.certifications || [];
  const awards = content.awards || [];

  function updateExperience(index: number, patch: Partial<ExperienceEntry>) {
    const next = experience.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...content, experience: next });
  }

  function updateEducation(index: number, patch: Partial<EducationEntry>) {
    const next = education.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...content, education: next });
  }

  function updateProject(index: number, patch: Partial<ProjectEntry>) {
    const next = projects.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...content, projects: next });
  }

  function updateCertification(index: number, patch: Partial<CertificationEntry>) {
    const next = certifications.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...content, certifications: next });
  }

  function updateAward(index: number, patch: Partial<AwardEntry>) {
    const next = awards.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...content, awards: next });
  }

  return (
    <div className="space-y-8">
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-800">Work experience</legend>
        {experience.length === 0 ? (
          <p className="text-sm text-slate-500">No roles yet. Add your current or past jobs.</p>
        ) : null}
        {experience.map((item, index) => (
          <EntryCard
            key={item.id || `exp-${index}`}
            title={item.title || item.company || `Role ${index + 1}`}
            onRemove={() =>
              onChange({
                ...content,
                experience: experience.filter((_, i) => i !== index),
              })
            }
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Job title">
                <input
                  value={item.title ?? ""}
                  onChange={(e) => updateExperience(index, { title: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Company">
                <input
                  value={item.company ?? ""}
                  onChange={(e) => updateExperience(index, { company: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Location">
                <input
                  value={item.location ?? ""}
                  onChange={(e) => updateExperience(index, { location: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
            </div>
            <DateRangeFields
              start={item.start_date ?? ""}
              end={item.end_date ?? ""}
              isCurrent={Boolean(item.is_current)}
              currentLabel="Currently working here"
              onStart={(v) => updateExperience(index, { start_date: v || null })}
              onEnd={(v) => updateExperience(index, { end_date: v || null })}
              onCurrent={(v) =>
                updateExperience(index, {
                  is_current: v,
                  end_date: v ? null : item.end_date,
                })
              }
            />
            <Field label="Summary">
              <textarea
                rows={3}
                value={item.summary ?? ""}
                onChange={(e) => updateExperience(index, { summary: e.target.value || null })}
                className={inputClass}
              />
            </Field>
            <Field label="Key achievements (one per line)">
              <textarea
                rows={3}
                value={(item.bullets || []).join("\n")}
                onChange={(e) =>
                  updateExperience(index, {
                    bullets: e.target.value
                      .split("\n")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                className={inputClass}
              />
            </Field>
          </EntryCard>
        ))}
        <AddButton
          label="+ Add work experience"
          onClick={() => onChange({ ...content, experience: [...experience, emptyExperience()] })}
        />
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-800">Education</legend>
        {education.length === 0 ? (
          <p className="text-sm text-slate-500">No education entries yet.</p>
        ) : null}
        {education.map((item, index) => (
          <EntryCard
            key={item.id || `edu-${index}`}
            title={item.institution || item.degree || `Education ${index + 1}`}
            onRemove={() =>
              onChange({
                ...content,
                education: education.filter((_, i) => i !== index),
              })
            }
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="College / university">
                <input
                  value={item.institution ?? ""}
                  onChange={(e) =>
                    updateEducation(index, { institution: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Degree">
                <input
                  value={item.degree ?? ""}
                  onChange={(e) => updateEducation(index, { degree: e.target.value || null })}
                  placeholder="B.S., M.Tech, MBA…"
                  className={inputClass}
                />
              </Field>
              <Field label="Specialization / major">
                <input
                  value={item.specialization ?? ""}
                  onChange={(e) =>
                    updateEducation(index, { specialization: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Location">
                <input
                  value={item.location ?? ""}
                  onChange={(e) => updateEducation(index, { location: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Score (CGPA / GPA / %)">
                <input
                  value={item.score ?? ""}
                  onChange={(e) => updateEducation(index, { score: e.target.value || null })}
                  placeholder="8.7"
                  className={inputClass}
                />
              </Field>
              <Field label="Score type">
                <select
                  value={item.score_type ?? ""}
                  onChange={(e) =>
                    updateEducation(index, { score_type: e.target.value || null })
                  }
                  className={inputClass}
                >
                  <option value="">Select…</option>
                  <option value="cgpa">CGPA</option>
                  <option value="gpa">GPA</option>
                  <option value="percentage">Percentage</option>
                  <option value="other">Other</option>
                </select>
              </Field>
            </div>
            <DateRangeFields
              start={item.start_date ?? ""}
              end={item.end_date ?? ""}
              isCurrent={Boolean(item.is_current)}
              currentLabel="Currently studying here"
              onStart={(v) => updateEducation(index, { start_date: v || null })}
              onEnd={(v) => updateEducation(index, { end_date: v || null })}
              onCurrent={(v) =>
                updateEducation(index, {
                  is_current: v,
                  end_date: v ? null : item.end_date,
                })
              }
            />
            <Field label="Summary">
              <textarea
                rows={2}
                value={item.summary ?? ""}
                onChange={(e) => updateEducation(index, { summary: e.target.value || null })}
                className={inputClass}
              />
            </Field>
          </EntryCard>
        ))}
        <AddButton
          label="+ Add education"
          onClick={() => onChange({ ...content, education: [...education, emptyEducation()] })}
        />
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-800">Projects</legend>
        {projects.map((item, index) => (
          <EntryCard
            key={item.id || `proj-${index}`}
            title={item.title || `Project ${index + 1}`}
            onRemove={() =>
              onChange({
                ...content,
                projects: projects.filter((_, i) => i !== index),
              })
            }
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Project title">
                <input
                  value={item.title ?? ""}
                  onChange={(e) => updateProject(index, { title: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Organization / client">
                <input
                  value={item.organization ?? ""}
                  onChange={(e) =>
                    updateProject(index, { organization: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="URL">
                <input
                  value={item.url ?? ""}
                  onChange={(e) => updateProject(index, { url: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Location">
                <input
                  value={item.location ?? ""}
                  onChange={(e) => updateProject(index, { location: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
            </div>
            <DateRangeFields
              start={item.start_date ?? ""}
              end={item.end_date ?? ""}
              isCurrent={Boolean(item.is_current)}
              currentLabel="Currently working on this"
              onStart={(v) => updateProject(index, { start_date: v || null })}
              onEnd={(v) => updateProject(index, { end_date: v || null })}
              onCurrent={(v) =>
                updateProject(index, {
                  is_current: v,
                  end_date: v ? null : item.end_date,
                })
              }
            />
            <Field label="Summary">
              <textarea
                rows={2}
                value={item.summary ?? ""}
                onChange={(e) => updateProject(index, { summary: e.target.value || null })}
                className={inputClass}
              />
            </Field>
            <Field label="Highlights (one per line)">
              <textarea
                rows={3}
                value={(item.bullets || []).join("\n")}
                onChange={(e) =>
                  updateProject(index, {
                    bullets: e.target.value
                      .split("\n")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                className={inputClass}
              />
            </Field>
            <Field label="Technologies (comma-separated)">
              <input
                value={(item.technologies || []).join(", ")}
                onChange={(e) =>
                  updateProject(index, {
                    technologies: e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                className={inputClass}
              />
            </Field>
          </EntryCard>
        ))}
        <AddButton
          label="+ Add project"
          onClick={() => onChange({ ...content, projects: [...projects, emptyProject()] })}
        />
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-800">Certifications</legend>
        {certifications.map((item, index) => (
          <EntryCard
            key={item.id || `cert-${index}`}
            title={item.title || `Certification ${index + 1}`}
            onRemove={() =>
              onChange({
                ...content,
                certifications: certifications.filter((_, i) => i !== index),
              })
            }
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Name">
                <input
                  value={item.title ?? ""}
                  onChange={(e) =>
                    updateCertification(index, { title: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Issuer">
                <input
                  value={item.issuer ?? ""}
                  onChange={(e) =>
                    updateCertification(index, { issuer: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Issued date">
                <input
                  value={item.date ?? ""}
                  onChange={(e) =>
                    updateCertification(index, { date: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Expiry date">
                <input
                  value={item.expiry_date ?? ""}
                  onChange={(e) =>
                    updateCertification(index, { expiry_date: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="Credential ID">
                <input
                  value={item.credential_id ?? ""}
                  onChange={(e) =>
                    updateCertification(index, { credential_id: e.target.value || null })
                  }
                  className={inputClass}
                />
              </Field>
              <Field label="URL">
                <input
                  value={item.url ?? ""}
                  onChange={(e) => updateCertification(index, { url: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
            </div>
            <Field label="Summary">
              <textarea
                rows={2}
                value={item.summary ?? ""}
                onChange={(e) =>
                  updateCertification(index, { summary: e.target.value || null })
                }
                className={inputClass}
              />
            </Field>
          </EntryCard>
        ))}
        <AddButton
          label="+ Add certification"
          onClick={() =>
            onChange({
              ...content,
              certifications: [...certifications, emptyCertification()],
            })
          }
        />
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-800">Awards</legend>
        {awards.map((item, index) => (
          <EntryCard
            key={item.id || `award-${index}`}
            title={item.title || `Award ${index + 1}`}
            onRemove={() =>
              onChange({
                ...content,
                awards: awards.filter((_, i) => i !== index),
              })
            }
          >
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Title">
                <input
                  value={item.title ?? ""}
                  onChange={(e) => updateAward(index, { title: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Issuer / organization">
                <input
                  value={item.issuer ?? ""}
                  onChange={(e) => updateAward(index, { issuer: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
              <Field label="Date">
                <input
                  value={item.date ?? ""}
                  onChange={(e) => updateAward(index, { date: e.target.value || null })}
                  className={inputClass}
                />
              </Field>
            </div>
            <Field label="Summary">
              <textarea
                rows={2}
                value={item.summary ?? ""}
                onChange={(e) => updateAward(index, { summary: e.target.value || null })}
                className={inputClass}
              />
            </Field>
          </EntryCard>
        ))}
        <AddButton
          label="+ Add award"
          onClick={() => onChange({ ...content, awards: [...awards, emptyAward()] })}
        />
      </fieldset>
    </div>
  );
}
