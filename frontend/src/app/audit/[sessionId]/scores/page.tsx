"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, APIError } from "@/lib/api";
import type { SessionProgress } from "@/types";

interface CategoryScore {
  id: string;
  category_key: string;
  category_name: string;
  score: number;
  ai_generated_score: number | null;
  status_label: string;
  what_observed: string | null;
  why_it_matters: string | null;
  how_to_close_gap: string | null;
  practitioner_override: boolean;
  override_notes: string | null;
}

interface PatternMatch {
  pattern_id: string;
  text: string;
  metadata: Record<string, string>;
  relevance: number;
  insight: string;
}

const scoreColor = (score: number) => {
  if (score >= 8) return "text-green-600 bg-green-50";
  if (score >= 6) return "text-yellow-600 bg-yellow-50";
  if (score >= 4) return "text-orange-600 bg-orange-50";
  return "text-red-600 bg-red-50";
};

export default function ScoresPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [scores, setScores] = useState<CategoryScore[]>([]);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [overrideId, setOverrideId] = useState<string | null>(null);
  const [overrideScore, setOverrideScore] = useState(5);
  const [overrideNotes, setOverrideNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<Record<string, PatternMatch[]>>({});
  const [progress, setProgress] = useState<SessionProgress | null>(null);
  const [showSkipWarning, setShowSkipWarning] = useState(false);

  const loadScores = () => {
    Promise.all([
      api.get<CategoryScore[]>(`/audits/${sessionId}/scores`),
      api.get<SessionProgress>(`/audits/${sessionId}/progress`),
    ])
      .then(([scoresRes, progressRes]) => {
        setScores(scoresRes.data);
        setProgress(progressRes.data);
        if (scoresRes.data.length > 0) {
          api.get<Record<string, PatternMatch[]>>(`/audits/${sessionId}/patterns`)
            .then((p) => setPatterns(p.data))
            .catch(() => {});
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(loadScores, [sessionId]);

  const handleGenerateClick = () => {
    // Check if there are unanswered prompts
    if (progress && progress.total_prompts > 0) {
      const unanswered = progress.total_prompts - progress.completed_prompts - progress.skipped_prompts;
      if (unanswered > 0) {
        setShowSkipWarning(true);
        return;
      }
    }
    runGeneration();
  };

  const runGeneration = async () => {
    setShowSkipWarning(false);
    setGenerating(true);
    setError(null);
    try {
      const res = await api.longPost<CategoryScore[]>(`/audits/${sessionId}/scores/generate`);
      setScores(res.data);
      // Reload patterns
      api.get<Record<string, PatternMatch[]>>(`/audits/${sessionId}/patterns`)
        .then((p) => setPatterns(p.data))
        .catch(() => {});
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Score generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleOverride = async (categoryKey: string) => {
    try {
      const res = await api.put<CategoryScore>(
        `/audits/${sessionId}/scores/${categoryKey}/override`,
        { score: overrideScore, override_notes: overrideNotes || null }
      );
      setScores((prev) => prev.map((s) => (s.category_key === categoryKey ? res.data : s)));
      setOverrideId(null);
      setOverrideNotes("");
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Override failed");
    }
  };

  const overall = scores.length > 0
    ? Math.round((scores.reduce((s, c) => s + c.score, 0) / (scores.length * 10)) * 100)
    : 0;

  const overallLabel = overall >= 90 ? "Thriving" : overall >= 75 ? "Intentional" : overall >= 60 ? "Developing" : overall >= 45 ? "Misaligned" : "Survival Mode";

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Score Review</h1>
          <Button onClick={handleGenerateClick} loading={generating}>
            {scores.length > 0 ? "Regenerate Scores" : "Generate Scores"}
          </Button>
        </div>

        {/* Unanswered prompts warning */}
        {showSkipWarning && progress && (
          <Card className="border-amber-300 bg-amber-50">
            <h3 className="font-semibold text-amber-800 mb-2">
              Unanswered Prompts Detected
            </h3>
            <p className="text-sm text-amber-700 mb-3">
              You have{" "}
              <strong>
                {progress.total_prompts - progress.completed_prompts - progress.skipped_prompts}
              </strong>{" "}
              unanswered prompts out of {progress.total_prompts} total.
              Categories without observations will not be scored.
            </p>

            {/* Sections with gaps -- each tappable to jump to that section */}
            <div className="space-y-2 mb-4">
              {progress.sections
                .filter((s) => {
                  const unanswered = s.total_prompts - s.completed_prompts - s.skipped_prompts;
                  return unanswered > 0;
                })
                .map((s) => {
                  const unanswered = s.total_prompts - s.completed_prompts - s.skipped_prompts;
                  return (
                    <Link
                      key={s.room_area}
                      href={`/audit/${sessionId}/field?room=${s.room_area}`}
                    >
                      <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm hover:bg-amber-100 transition-colors cursor-pointer">
                        <span className="font-medium text-amber-800">
                          {s.label}
                        </span>
                        <span className="text-amber-600">
                          {unanswered} unanswered →
                        </span>
                      </div>
                    </Link>
                  );
                })}
            </div>

            <div className="flex gap-3">
              <Button
                size="sm"
                onClick={runGeneration}
              >
                Proceed Anyway
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSkipWarning(false)}
              >
                Cancel
              </Button>
            </div>
          </Card>
        )}

        {generating && (
          <Card className="text-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent mx-auto mb-3" />
            <p className="text-sm text-gray-600">
              Generating scores with your local LLM. This takes 30-60 seconds
              as each category is scored individually.
            </p>
          </Card>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        {scores.length > 0 && (
          <Card className="text-center">
            <div className="text-5xl font-bold text-brand-600">{overall}</div>
            <div className="text-lg text-brand-700">{overallLabel}</div>
            <div className="text-sm text-gray-500">out of 100</div>
            <div className="text-xs text-gray-400 mt-1">Based on {scores.length} observed categories</div>
          </Card>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
          </div>
        ) : scores.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-gray-500">No scores yet. Click Generate Scores to start the diagnosis.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {scores.map((s) => (
              <Card key={s.id}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`rounded-full px-3 py-1 text-lg font-bold ${scoreColor(s.score)}`}>
                        {s.score}/10
                      </span>
                      <div>
                        <h3 className="font-semibold text-gray-900">{s.category_name}</h3>
                        <span className="text-xs text-gray-500">{s.status_label}</span>
                      </div>
                    </div>
                    {/* Score bar */}
                    <div className="h-2 w-full rounded-full bg-gray-200 mb-3">
                      <div
                        className={`h-2 rounded-full transition-all ${s.score >= 7 ? "bg-green-500" : s.score >= 4 ? "bg-yellow-500" : "bg-red-500"}`}
                        style={{ width: `${s.score * 10}%` }}
                      />
                    </div>
                    {s.what_observed && (
                      <p className="text-sm text-gray-700 mb-1"><strong>What I observed:</strong> {s.what_observed}</p>
                    )}
                    {s.why_it_matters && (
                      <p className="text-sm text-gray-700 mb-1"><strong>Why it matters:</strong> {s.why_it_matters}</p>
                    )}
                    {s.how_to_close_gap && (
                      <p className="text-sm text-gray-700 mb-1"><strong>How to close the gap:</strong> {s.how_to_close_gap}</p>
                    )}
                    {s.practitioner_override && s.override_notes && (
                      <p className="text-sm text-purple-700 mt-2"><strong>the practitioner's note:</strong> {s.override_notes}</p>
                    )}
                    {/* Pattern matches from past audits */}
                    {patterns[s.category_key] && patterns[s.category_key].length > 0 && (
                      <div className="mt-3 border-t pt-3">
                        <p className="text-xs font-semibold text-indigo-600 mb-1">Similar patterns from past audits:</p>
                        {patterns[s.category_key].map((p) => (
                          <div key={p.pattern_id} className="rounded bg-indigo-50 p-2 mb-1 text-xs text-indigo-800">
                            <p>{p.text}</p>
                            {p.insight && <p className="mt-1 text-indigo-600 italic">{p.insight}</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      setOverrideId(s.category_key);
                      setOverrideScore(s.score);
                      setOverrideNotes(s.override_notes || "");
                    }}
                    className="ml-3 shrink-0 text-xs text-gray-400 hover:text-brand-600"
                  >
                    Override
                  </button>
                </div>

                {overrideId === s.category_key && (
                  <div className="mt-3 border-t pt-3 space-y-2">
                    <div className="flex items-center gap-3">
                      <label className="text-sm text-gray-600">Score:</label>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={overrideScore}
                        onChange={(e) => setOverrideScore(Number(e.target.value))}
                        className="flex-1"
                      />
                      <span className="font-bold text-brand-600 w-8 text-center">{overrideScore}</span>
                    </div>
                    <textarea
                      value={overrideNotes}
                      onChange={(e) => setOverrideNotes(e.target.value)}
                      placeholder="Override notes (optional)"
                      rows={2}
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleOverride(s.category_key)}>Save Override</Button>
                      <Button size="sm" variant="ghost" onClick={() => setOverrideId(null)}>Cancel</Button>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}

        {scores.length > 0 && (
          <div className="flex gap-3">
            <Button onClick={() => router.push(`/audit/${sessionId}/report`)}>
              Generate Report
            </Button>
            <Button variant="secondary" onClick={() => router.push(`/audit/${sessionId}`)}>
              Back to Session
            </Button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
