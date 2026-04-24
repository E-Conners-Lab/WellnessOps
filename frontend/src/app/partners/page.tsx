"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, APIError } from "@/lib/api";

interface Partner {
  id: string;
  name: string;
  business_name: string | null;
  category: string;
  location: string | null;
  why_recommended: string;
  is_ambassador: boolean;
  is_active: boolean;
}

export default function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [bizName, setBizName] = useState("");
  const [location, setLocation] = useState("");
  const [whyRec, setWhyRec] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    api.get<Partner[]>("/partners").then((r) => setPartners(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/partners", {
        name, category,
        business_name: bizName || undefined,
        location: location || undefined,
        why_recommended: whyRec,
      });
      setShowForm(false);
      setName(""); setCategory(""); setBizName(""); setLocation(""); setWhyRec("");
      load();
    } catch (err) {
      alert(err instanceof APIError ? err.message : "Failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Partners</h1>
          <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add Partner"}</Button>
        </div>

        {showForm && (
          <Card>
            <form onSubmit={handleCreate} className="space-y-3">
              <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Business Name" value={bizName} onChange={(e) => setBizName(e.target.value)} />
              <Input label="Category" value={category} onChange={(e) => setCategory(e.target.value)} required placeholder="organizer, chef, trainer, etc." />
              <Input label="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Why Recommended</label>
                <textarea value={whyRec} onChange={(e) => setWhyRec(e.target.value)} required rows={2} className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <Button type="submit" loading={saving}>Save Partner</Button>
            </form>
          </Card>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
          </div>
        ) : partners.length === 0 ? (
          <Card className="text-center py-8"><p className="text-gray-500">No partners yet.</p></Card>
        ) : (
          <div className="space-y-3">
            {partners.map((p) => (
              <Card key={p.id}>
                <div>
                  <h3 className="font-semibold text-gray-900">{p.name}</h3>
                  {p.business_name && <p className="text-sm text-gray-500">{p.business_name}</p>}
                  <div className="flex gap-2 mt-1">
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{p.category}</span>
                    {p.location && <span className="text-xs text-gray-400">{p.location}</span>}
                    {p.is_ambassador && <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700">Ambassador</span>}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{p.why_recommended}</p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
