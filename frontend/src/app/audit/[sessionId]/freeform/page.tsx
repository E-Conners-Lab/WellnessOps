"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PhotoCapture } from "@/components/ui/PhotoCapture";
import { api, APIError } from "@/lib/api";
import type { Observation } from "@/types";

interface CategorizeItem {
  room_area: string | null;
  category: string | null;
  domain_tags: string[];
  confidence: number;
  text: string;
  clarifying_question: string | null;
}

const ROOM_LABELS: Record<string, string> = {
  entry: "Entry and Curb Appeal",
  living: "Living Spaces",
  kitchen: "Kitchen",
  hidden_spaces: "Hidden Spaces",
  bedroom: "Bedroom",
  workspace: "Workspace",
  extended: "Extended Areas",
  wearable: "Wearable Data",
  financial: "Financial Alignment",
  client_responses: "Client Questions",
};

export default function FreeFormPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [text, setText] = useState("");
  const [categorizing, setCategorizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [results, setResults] = useState<CategorizeItem[]>([]);
  const [overrides, setOverrides] = useState<Record<number, string>>({});
  const [saved, setSaved] = useState(false);
  const [savedCount, setSavedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleCategorize = async () => {
    if (!text.trim()) return;
    setError(null);
    setCategorizing(true);
    setResults([]);
    setOverrides({});
    setSaved(false);

    try {
      const res = await api.post<CategorizeItem[]>(
        "/observations/categorize",
        { text }
      );
      setResults(res.data);
      // Pre-fill overrides with suggested rooms
      const initial: Record<number, string> = {};
      res.data.forEach((item, idx) => {
        if (item.room_area) initial[idx] = item.room_area;
      });
      setOverrides(initial);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Categorization failed");
    } finally {
      setCategorizing(false);
    }
  };

  const handleSaveAll = async () => {
    setSaving(true);
    setError(null);
    let count = 0;

    try {
      for (let i = 0; i < results.length; i++) {
        const item = results[i];
        const room = overrides[i];
        if (!room) continue;

        await api.post<Observation>(`/audits/${sessionId}/observations`, {
          room_area: room,
          category: item.category || null,
          content: item.text,
          is_from_structured_flow: false,
          auto_categorized: true,
          domain_tags: item.domain_tags || [],
        });
        count++;
      }
      setSaved(true);
      setSavedCount(count);
      setText("");
      setResults([]);
      setOverrides({});
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    setResults([]);
    setOverrides({});
  };

  const updateOverride = (idx: number, value: string) => {
    setOverrides((prev) => ({ ...prev, [idx]: value }));
  };

  const allHaveRooms = results.length > 0 && results.every((_, i) => overrides[i]);

  return (
    <AppShell>
      <div className="mx-auto max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            Free-Form Capture
          </h1>
          <button
            onClick={() => router.push(`/audit/${sessionId}`)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Back to session
          </button>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {saved && (
          <div className="rounded-lg bg-green-50 p-3 text-sm text-green-700">
            {savedCount} observation{savedCount !== 1 ? "s" : ""} saved. Add
            another or go back to the session.
          </div>
        )}

        {/* Input area */}
        <Card>
          <textarea
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setSaved(false);
            }}
            placeholder="Type or paste your observations here. You can describe multiple rooms at once -- the system will split them automatically."
            rows={6}
            className="block w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            autoFocus
          />
          <div className="mt-3 flex gap-3">
            <Button
              onClick={handleCategorize}
              loading={categorizing}
              disabled={!text.trim()}
              className="flex-1"
              size="lg"
            >
              Categorize
            </Button>
          </div>

          {/* Photo capture with vision analysis */}
          <div className="mt-3">
            <PhotoCapture
              sessionId={sessionId}
              onAnalyzed={(data) => {
                const desc = data.description;
                if (desc && desc !== "Photo uploaded. Vision analysis unavailable.") {
                  const newText = text
                    ? `${text}\n\n${desc}`
                    : desc;
                  setText(newText);
                  setSaved(false);
                }
              }}
            />
          </div>
        </Card>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-3">
            {results.length > 1 && (
              <p className="text-sm text-gray-600">
                Detected {results.length} observations across different areas:
              </p>
            )}

            {results.map((item, idx) => (
              <Card key={idx}>
                <div className="space-y-3">
                  {/* Extracted text */}
                  <p className="text-sm text-gray-700 italic">
                    &ldquo;{item.text}&rdquo;
                  </p>

                  {/* Categorization or clarifying question */}
                  {item.clarifying_question && item.confidence < 0.7 ? (
                    <p className="text-sm font-medium text-amber-700">
                      {item.clarifying_question}
                    </p>
                  ) : (
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-brand-50 px-2.5 py-1 text-sm font-medium text-brand-700">
                        {ROOM_LABELS[item.room_area || ""] || item.room_area}
                      </span>
                      <span className="text-xs text-gray-400">
                        {Math.round(item.confidence * 100)}% confident
                      </span>
                    </div>
                  )}

                  {item.domain_tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.domain_tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Override */}
                  <select
                    value={overrides[idx] || ""}
                    onChange={(e) => updateOverride(idx, e.target.value)}
                    className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="">Select room area...</option>
                    {Object.entries(ROOM_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </Card>
            ))}

            <div className="flex gap-3">
              <Button
                onClick={handleSaveAll}
                loading={saving}
                disabled={!allHaveRooms}
                className="flex-1"
              >
                Save {results.length > 1 ? `All ${results.length}` : ""}
                Observation{results.length !== 1 ? "s" : ""}
              </Button>
              <Button
                variant="ghost"
                onClick={handleDiscard}
                className="flex-1"
              >
                Discard
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
