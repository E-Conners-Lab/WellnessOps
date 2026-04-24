"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, APIError } from "@/lib/api";

interface ReportData {
  id: string;
  version: number;
  status: string;
  overall_score: number;
  overall_label: string;
  priority_action_plan: { actions: { rank: number; category_name: string; score: number; action: string }[] } | null;
  vision_section: string | null;
  next_steps: string | null;
  pdf_path: string | null;
  scores?: Array<{
    category_name: string;
    score: number;
    status_label: string;
    what_observed: string | null;
    why_it_matters: string | null;
    how_to_close_gap: string | null;
  }>;
}

export default function ReportPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [report, setReport] = useState<ReportData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [editingVision, setEditingVision] = useState(false);
  const [editingSteps, setEditingSteps] = useState(false);
  const [visionText, setVisionText] = useState("");
  const [stepsText, setStepsText] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [referrals, setReferrals] = useState<{
    product_matches: Record<string, Array<{ name: string; category: string; why_recommended: string }>>;
    partner_matches: Record<string, Array<{ name: string; business_name: string | null; category: string; why_recommended: string }>>;
  }>({ product_matches: {}, partner_matches: {} });

  const loadReport = async () => {
    try {
      // Try to get latest report for this session
      const gen = await api.longPost<ReportData>(`/audits/${sessionId}/reports/generate`);
      const preview = await api.get<ReportData>(`/reports/${gen.data.id}/preview`);
      setReport(preview.data);
      setVisionText(preview.data.vision_section || "");
      setStepsText(preview.data.next_steps || "");
      // Load referrals
      api.get<typeof referrals>(`/audits/${sessionId}/referrals`)
        .then((r) => setReferrals(r.data))
        .catch(() => {});
    } catch {
      // No report yet, need to generate
      setReport(null);
    }
    setLoading(false);
  };

  useEffect(() => { loadReport(); }, [sessionId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.post<ReportData>(`/audits/${sessionId}/reports/generate`);
      const preview = await api.get<ReportData>(`/reports/${res.data.id}/preview`);
      setReport(preview.data);
      setVisionText(preview.data.vision_section || "");
      setStepsText(preview.data.next_steps || "");
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Report generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdits = async () => {
    if (!report) return;
    try {
      await api.put(`/reports/${report.id}`, {
        vision_section: visionText,
        next_steps: stepsText,
      });
      setReport((r) => r ? { ...r, vision_section: visionText, next_steps: stepsText } : r);
      setEditingVision(false);
      setEditingSteps(false);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Save failed");
    }
  };

  const handleApprove = async () => {
    if (!report) return;
    setApproving(true);
    try {
      const res = await api.longPut<ReportData>(`/reports/${report.id}/approve`);
      setReport((r) => r ? { ...r, ...res.data } : r);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  };

  const handleDownloadPDF = () => {
    if (!report) return;
    window.open(`/api/v1/reports/${report.id}/pdf`, "_blank");
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Client Report</h1>
          <div className="flex gap-2">
            {report?.status === "draft" && (
              <>
                <Button onClick={handleSaveEdits} variant="secondary" size="sm">Save Edits</Button>
                <Button onClick={handleApprove} loading={approving} size="sm">Approve and Generate PDF</Button>
              </>
            )}
            {report?.status === "final" && report.pdf_path && (
              <Button onClick={handleDownloadPDF}>Download PDF</Button>
            )}
            {!report && (
              <Button onClick={handleGenerate} loading={generating}>Generate Report</Button>
            )}
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        {report?.status === "final" && (
          <div className="rounded-lg bg-green-50 p-3 text-sm text-green-700">
            Report approved and finalized. PDF is ready for download.
          </div>
        )}

        {report && (
          <>
            {/* Overall Score */}
            <Card className="text-center">
              <div className="text-5xl font-bold text-brand-600">{report.overall_score}</div>
              <div className="text-lg text-brand-700">{report.overall_label}</div>
              <div className="text-xs text-gray-400">Version {report.version} -- {report.status}</div>
            </Card>

            {/* Category Scores */}
            {report.scores && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Category Scores</h2>
                <div className="space-y-3">
                  {report.scores.map((s, i) => (
                    <Card key={i}>
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${
                          s.score >= 7 ? "bg-green-100 text-green-700" : s.score >= 4 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
                        }`}>
                          {s.score}/10
                        </span>
                        <span className="font-medium text-gray-900">{s.category_name}</span>
                      </div>
                      {s.what_observed && <p className="text-sm text-gray-600">{s.what_observed}</p>}
                      {s.how_to_close_gap && <p className="text-sm text-gray-500 mt-1">{s.how_to_close_gap}</p>}
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Priority Action Plan */}
            {report.priority_action_plan?.actions && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Priority Action Plan</h2>
                <div className="space-y-2">
                  {report.priority_action_plan.actions.map((a) => (
                    <Card key={a.rank} className="border-l-4 border-l-amber-400">
                      <div className="flex items-start gap-3">
                        <span className="shrink-0 text-lg font-bold text-amber-600">{a.rank}.</span>
                        <div>
                          <span className="font-medium text-gray-900">{a.category_name}</span>
                          <span className="text-sm text-gray-500 ml-2">({a.score}/10)</span>
                          <p className="text-sm text-gray-600 mt-1">{a.action}</p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Vision Section */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-gray-900">What Changes When You Fix This</h2>
                {report.status === "draft" && (
                  <button onClick={() => setEditingVision(!editingVision)} className="text-xs text-brand-600">
                    {editingVision ? "Cancel" : "Edit"}
                  </button>
                )}
              </div>
              {editingVision ? (
                <textarea
                  value={visionText}
                  onChange={(e) => setVisionText(e.target.value)}
                  rows={6}
                  className="block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm"
                />
              ) : (
                <Card className="bg-brand-50/30 italic">
                  <p className="text-gray-700 whitespace-pre-wrap">{report.vision_section}</p>
                </Card>
              )}
            </div>

            {/* Next Steps */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-gray-900">Next Steps</h2>
                {report.status === "draft" && (
                  <button onClick={() => setEditingSteps(!editingSteps)} className="text-xs text-brand-600">
                    {editingSteps ? "Cancel" : "Edit"}
                  </button>
                )}
              </div>
              {editingSteps ? (
                <textarea
                  value={stepsText}
                  onChange={(e) => setStepsText(e.target.value)}
                  rows={6}
                  className="block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm"
                />
              ) : (
                <Card>
                  <p className="text-gray-700 whitespace-pre-wrap">{report.next_steps}</p>
                </Card>
              )}
            </div>
            {/* Recommended Products and Partners */}
            {(Object.keys(referrals.product_matches).length > 0 ||
              Object.keys(referrals.partner_matches).length > 0) && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  Recommended Products and Partners
                </h2>

                {Object.entries(referrals.product_matches).map(([catKey, products]) => (
                  <div key={catKey} className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 capitalize">
                      {catKey.replace(/_/g, " ")} -- Products
                    </h3>
                    <div className="space-y-2">
                      {products.map((p, i) => (
                        <Card key={i} className="py-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <span className="font-medium text-gray-900">{p.name}</span>
                              <span className="ml-2 text-xs text-gray-500">{p.category}</span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{p.why_recommended}</p>
                        </Card>
                      ))}
                    </div>
                  </div>
                ))}

                {Object.entries(referrals.partner_matches).map(([catKey, partners]) => (
                  <div key={catKey} className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 capitalize">
                      {catKey.replace(/_/g, " ")} -- Partners
                    </h3>
                    <div className="space-y-2">
                      {partners.map((p, i) => (
                        <Card key={i} className="py-3">
                          <span className="font-medium text-gray-900">{p.name}</span>
                          {p.business_name && (
                            <span className="ml-2 text-sm text-gray-500">{p.business_name}</span>
                          )}
                          <span className="ml-2 text-xs text-gray-400">{p.category}</span>
                          <p className="text-sm text-gray-600 mt-1">{p.why_recommended}</p>
                        </Card>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
