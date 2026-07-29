"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Legacy entry — send users into the routed app shell. */
export default function DashboardIndexPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/dashboard/resumes");
  }, [router]);
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12">
      <p className="text-sm text-slate-500">Opening CareerPilot…</p>
    </main>
  );
}
