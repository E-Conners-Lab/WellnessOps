"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { AuditSession, Observation, SessionProgress } from "@/types";

export default function AuditSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<AuditSession | null>(null);
  const [progress, setProgress] = useState<SessionProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<AuditSession>(`/audits/${sessionId}`),
      api.get<SessionProgress>(`/audits/${sessionId}/progress`),
    ])
      .then(([sessionRes, progressRes]) => {
        setSession(sessionRes.data);
        setProgress(progressRes.data);
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  const advanceStatus = async (target: string) => {
    const res = await api.put<AuditSession>(`/audits/${sessionId}/status`, {
      target_status: target,
    });
    setSession(res.data);
  };

  if (loading || !session || !progress) {
    return (
      <AppShell>
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  const isInProgress = session.status === "in_progress";

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 capitalize">
            {session.audit_tier} Audit
          </h1>
          <p className="text-sm text-gray-500">
            Status: {session.status.replace(/_/g, " ")}
          </p>
        </div>

        {/* Progress bar */}
        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Overall Progress
            </span>
            <span className="text-sm font-bold text-brand-600">
              {progress.completion_percent}%
            </span>
          </div>
          <div className="h-3 w-full rounded-full bg-gray-200">
            <div
              className="h-3 rounded-full bg-brand-500 transition-all duration-300"
              style={{ width: `${progress.completion_percent}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {progress.completed_prompts} answered, {progress.skipped_prompts}{" "}
            skipped of {progress.total_prompts} prompts
          </p>
        </Card>

        {/* Room sections */}
        {isInProgress && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Room Sections
            </h2>
            <div className="space-y-3">
              {progress.sections.map((sec) => {
                const addressed = sec.completed_prompts + sec.skipped_prompts;
                const pct =
                  sec.total_prompts > 0
                    ? Math.round((addressed / sec.total_prompts) * 100)
                    : 0;
                const isDone = pct === 100;

                return (
                  <Link
                    key={sec.room_area}
                    href={`/audit/${sessionId}/field?room=${sec.room_area}`}
                  >
                    <Card
                      className={`cursor-pointer transition-colors ${
                        isDone
                          ? "border-green-200 bg-green-50/30"
                          : "hover:border-brand-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {sec.label}
                          </h3>
                          <p className="text-xs text-gray-500">
                            {sec.completed_prompts}/{sec.total_prompts} answered
                            {sec.skipped_prompts > 0 &&
                              `, ${sec.skipped_prompts} skipped`}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-sm font-bold ${
                              isDone ? "text-green-600" : "text-gray-400"
                            }`}
                          >
                            {pct}%
                          </span>
                        </div>
                      </div>
                    </Card>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* Free-form observations */}
        {(() => {
          const freeform = (session.observations || []).filter(
            (o: Observation) => !o.is_from_structured_flow && !o.skipped
          );
          if (freeform.length === 0) return null;
          return (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Free-Form Observations ({freeform.length})
              </h2>
              <div className="space-y-2">
                {freeform.map((o: Observation) => (
                  <Card key={o.id}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm text-gray-700 flex-1">
                        {o.content}
                      </p>
                      <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 capitalize">
                        {(o.room_area || "uncategorized").replace(/_/g, " ")}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          );
        })()}

        {/* Actions */}
        <div className="flex gap-3">
          {isInProgress && (
            <>
              <Link href={`/audit/${sessionId}/field`}>
                <Button>Continue Field Companion</Button>
              </Link>
              <Link href={`/audit/${sessionId}/freeform`}>
                <Button variant="secondary">Free-Form Capture</Button>
              </Link>
              {(progress.completion_percent > 0 ||
                (session.observations || []).length > 0) && (
                <Button
                  variant="secondary"
                  onClick={() => advanceStatus("observations_complete")}
                >
                  Finish Observations
                </Button>
              )}
            </>
          )}
          {session.status === "observations_complete" && (
            <>
              <Link href={`/audit/${sessionId}/review`}>
                <Button variant="secondary">Review Observations</Button>
              </Link>
              <Link href={`/audit/${sessionId}/scores`}>
                <Button>Generate Scores</Button>
              </Link>
            </>
          )}
          {(session.status === "diagnosis_pending" || session.status === "report_draft") && (
            <>
              <Link href={`/audit/${sessionId}/scores`}>
                <Button variant="secondary">Review Scores</Button>
              </Link>
              <Link href={`/audit/${sessionId}/report`}>
                <Button>View Report</Button>
              </Link>
            </>
          )}
          {session.status === "report_final" && (
            <Link href={`/audit/${sessionId}/report`}>
              <Button>View Final Report</Button>
            </Link>
          )}
        </div>
      </div>
    </AppShell>
  );
}
