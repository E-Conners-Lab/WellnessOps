"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { AuditSession, Observation } from "@/types";

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<AuditSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AuditSession>(`/audits/${sessionId}`).then((res) => {
      setSession(res.data);
      setLoading(false);
    });
  }, [sessionId]);

  if (loading || !session) {
    return (
      <AppShell>
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  const observations = session.observations || [];

  // Group observations by room_area
  const grouped: Record<string, Observation[]> = {};
  for (const obs of observations) {
    if (!grouped[obs.room_area]) grouped[obs.room_area] = [];
    grouped[obs.room_area].push(obs);
  }

  const answered = observations.filter((o) => !o.skipped && o.content);
  const skipped = observations.filter((o) => o.skipped);

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Review Observations
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {answered.length} observations, {skipped.length} skipped
          </p>
        </div>

        {Object.entries(grouped).map(([room, obs]) => (
          <div key={room}>
            <h2 className="text-lg font-semibold text-gray-900 mb-2 capitalize">
              {room.replace(/_/g, " ")}
            </h2>
            <div className="space-y-2">
              {obs.map((o) => (
                <Card
                  key={o.id}
                  className={o.skipped ? "opacity-50" : ""}
                >
                  {o.skipped ? (
                    <p className="text-sm text-gray-400 italic">Skipped</p>
                  ) : (
                    <p className="text-sm text-gray-700">{o.content}</p>
                  )}
                  {o.prompt_key && (
                    <p className="mt-1 text-xs text-gray-400">
                      {o.prompt_key}
                    </p>
                  )}
                </Card>
              ))}
            </div>
          </div>
        ))}

        <div className="flex gap-3 pt-4 border-t">
          <Button
            variant="secondary"
            onClick={() => router.push(`/audit/${sessionId}`)}
          >
            Back to Session
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
