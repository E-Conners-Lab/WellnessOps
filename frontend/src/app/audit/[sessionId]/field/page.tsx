"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { PhotoCapture } from "@/components/ui/PhotoCapture";
import { api } from "@/lib/api";
import type {
  Observation,
  AuditSession,
  RoomSection,
  SessionProgress,
} from "@/types";

export default function FieldCompanionPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = params.sessionId as string;
  const initialRoom = searchParams.get("room");

  const [sections, setSections] = useState<RoomSection[]>([]);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [sectionIdx, setSectionIdx] = useState(0);
  const [promptIdx, setPromptIdx] = useState(0);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState<SessionProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load sections, observations, and progress
  useEffect(() => {
    Promise.all([
      api.get<RoomSection[]>(`/audits/${sessionId}/prompts`),
      api.get<AuditSession>(`/audits/${sessionId}`),
      api.get<SessionProgress>(`/audits/${sessionId}/progress`),
    ]).then(([sectionsRes, sessionRes, progressRes]) => {
      setSections(sectionsRes.data);
      setObservations(sessionRes.data.observations || []);
      setProgress(progressRes.data);

      // Navigate to the requested room and find first unanswered prompt
      const obs = sessionRes.data.observations || [];
      const answeredKeys = new Set(
        obs.filter((o) => o.prompt_key && (o.content || o.skipped)).map((o) => o.prompt_key)
      );

      if (initialRoom) {
        const secIdx = sectionsRes.data.findIndex(
          (s) => s.room_area === initialRoom
        );
        if (secIdx >= 0) {
          setSectionIdx(secIdx);
          // Find first unanswered prompt in this section
          const section = sectionsRes.data[secIdx];
          const firstUnanswered = section.prompts.findIndex(
            (p) => !answeredKeys.has(p.key)
          );
          if (firstUnanswered >= 0) {
            setPromptIdx(firstUnanswered);
          }
        }
      }

      setLoading(false);
    });
  }, [sessionId, initialRoom]);

  const currentSection = sections[sectionIdx];
  const currentPrompt = currentSection?.prompts[promptIdx];

  // Find existing observation for current prompt
  const existingObs = observations.find(
    (o) => o.prompt_key === currentPrompt?.key
  );

  // Load existing text when navigating to a prompt
  useEffect(() => {
    if (existingObs && !existingObs.skipped) {
      setText(existingObs.content || "");
    } else {
      setText("");
    }
  }, [existingObs, currentPrompt?.key]);

  // Auto-save with 2-second debounce
  const saveObservation = useCallback(
    async (content: string, skipped = false) => {
      if (!currentPrompt) return;
      setSaving(true);

      try {
        if (existingObs) {
          // Update existing
          const res = await api.put<Observation>(
            `/observations/${existingObs.id}`,
            { content: content || null, skipped }
          );
          setObservations((prev) =>
            prev.map((o) => (o.id === existingObs.id ? res.data : o))
          );
        } else {
          // Create new
          const res = await api.post<Observation>(
            `/audits/${sessionId}/observations`,
            {
              room_area: currentSection.room_area,
              content: content || null,
              prompt_key: currentPrompt.key,
              sort_order: currentPrompt.sort_order,
              skipped,
            }
          );
          setObservations((prev) => [...prev, res.data]);
        }

        // Refresh progress
        const progressRes = await api.get<SessionProgress>(
          `/audits/${sessionId}/progress`
        );
        setProgress(progressRes.data);
      } finally {
        setSaving(false);
      }
    },
    [currentPrompt, currentSection, existingObs, sessionId]
  );

  const handleTextChange = (value: string) => {
    setText(value);
    // Clear existing timer
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    // Auto-save after 2 seconds of inactivity
    if (value.trim()) {
      saveTimerRef.current = setTimeout(() => saveObservation(value), 2000);
    }
  };

  const handleBlur = () => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    if (text.trim()) {
      saveObservation(text);
    }
  };

  const handleNext = async () => {
    // Save current text if not empty
    if (text.trim() && !existingObs) {
      await saveObservation(text);
    }
    // Move to next prompt
    if (promptIdx < currentSection.prompts.length - 1) {
      setPromptIdx(promptIdx + 1);
    } else if (sectionIdx < sections.length - 1) {
      setSectionIdx(sectionIdx + 1);
      setPromptIdx(0);
    } else {
      // All done
      router.push(`/audit/${sessionId}`);
    }
  };

  const handleSkip = async () => {
    await saveObservation("", true);
    handleNext();
  };

  const handlePrev = () => {
    if (promptIdx > 0) {
      setPromptIdx(promptIdx - 1);
    } else if (sectionIdx > 0) {
      const prevSection = sections[sectionIdx - 1];
      setSectionIdx(sectionIdx - 1);
      setPromptIdx(prevSection.prompts.length - 1);
    }
  };

  if (loading || !currentSection || !currentPrompt) {
    return (
      <AppShell>
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  const totalPrompts = sections.reduce((s, sec) => s + sec.prompts.length, 0);
  const currentPromptNum =
    sections
      .slice(0, sectionIdx)
      .reduce((s, sec) => s + sec.prompts.length, 0) +
    promptIdx +
    1;

  return (
    <AppShell>
      <div className="mx-auto max-w-lg space-y-4">
        {/* Progress header */}
        <div>
          <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
            <span className="font-medium text-brand-700">
              {currentSection.label}
            </span>
            <span>
              {currentPromptNum} / {totalPrompts}
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-brand-500 transition-all duration-300"
              style={{
                width: `${(currentPromptNum / totalPrompts) * 100}%`,
              }}
            />
          </div>
        </div>

        {/* Prompt card */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-lg font-medium text-gray-900 leading-relaxed">
            {currentPrompt.text}
          </p>

          <textarea
            value={text}
            onChange={(e) => handleTextChange(e.target.value)}
            onBlur={handleBlur}
            placeholder="Type your observation here..."
            rows={5}
            className="mt-4 block w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            autoFocus
          />

          {/* Photo capture */}
          <div className="mt-3">
            <PhotoCapture
              sessionId={sessionId}
              compact
              onAnalyzed={(data) => {
                // Append vision description to observation text
                const visionText = data.description;
                if (visionText && visionText !== "Photo uploaded. Vision analysis unavailable.") {
                  const newText = text
                    ? `${text}\n\n[Photo analysis: ${visionText}]`
                    : `[Photo analysis: ${visionText}]`;
                  setText(newText);
                  saveObservation(newText);
                }
              }}
            />
          </div>

          {saving && (
            <p className="mt-2 text-xs text-gray-400">Saving...</p>
          )}
          {existingObs && !saving && (
            <p className="mt-2 text-xs text-green-500">Saved</p>
          )}
        </div>

        {/* Navigation buttons -- big tap targets for mobile */}
        <div className="flex gap-3">
          <Button
            variant="ghost"
            size="lg"
            onClick={handlePrev}
            disabled={sectionIdx === 0 && promptIdx === 0}
            className="flex-1"
          >
            Back
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={handleSkip}
            className="flex-1"
          >
            Skip
          </Button>
          <Button size="lg" onClick={handleNext} className="flex-1">
            {sectionIdx === sections.length - 1 &&
            promptIdx === currentSection.prompts.length - 1
              ? "Done"
              : "Next"}
          </Button>
        </div>

        {/* Quick section jump */}
        <div className="border-t pt-4">
          <p className="text-xs text-gray-400 mb-2">Jump to section</p>
          <div className="flex flex-wrap gap-2">
            {sections.map((sec, idx) => (
              <button
                key={sec.room_area}
                onClick={() => {
                  setSectionIdx(idx);
                  setPromptIdx(0);
                }}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  idx === sectionIdx
                    ? "bg-brand-100 text-brand-700"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {sec.label}
              </button>
            ))}
          </div>
        </div>

        {/* Pause button */}
        <div className="text-center">
          <button
            onClick={() => router.push(`/audit/${sessionId}`)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Pause and return to session
          </button>
        </div>
      </div>
    </AppShell>
  );
}
