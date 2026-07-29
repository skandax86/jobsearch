"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function TailorPage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Workspace" }, { label: "Tailor resume" }]}
      title="Tailor resume"
      description="LinkedIn job tweaks, suggestions, and cover letters."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="tailor" />
      </Suspense>
    </DashboardShell>
  );
}
