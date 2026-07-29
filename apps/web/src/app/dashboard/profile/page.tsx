"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function ProfilePage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Workspace" }, { label: "Profile" }]}
      title="Profile"
      description="Contact, career, experience, education, and skills."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="profile" />
      </Suspense>
    </DashboardShell>
  );
}
