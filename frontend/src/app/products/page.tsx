"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, APIError } from "@/lib/api";

interface Product {
  id: string;
  name: string;
  brand: string | null;
  category: string;
  price_range: string | null;
  why_recommended: string;
  is_recommended: boolean;
  is_active: boolean;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [whyRec, setWhyRec] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    api.get<Product[]>("/products").then((r) => setProducts(r.data)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/products", { name, category, brand: brand || undefined, why_recommended: whyRec });
      setShowForm(false);
      setName(""); setCategory(""); setBrand(""); setWhyRec("");
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
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add Product"}</Button>
        </div>

        {showForm && (
          <Card>
            <form onSubmit={handleCreate} className="space-y-3">
              <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Brand" value={brand} onChange={(e) => setBrand(e.target.value)} />
              <Input label="Category" value={category} onChange={(e) => setCategory(e.target.value)} required placeholder="air_quality, sleep, lighting, etc." />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Why Recommended</label>
                <textarea value={whyRec} onChange={(e) => setWhyRec(e.target.value)} required rows={2} className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <Button type="submit" loading={saving}>Save Product</Button>
            </form>
          </Card>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
          </div>
        ) : products.length === 0 ? (
          <Card className="text-center py-8"><p className="text-gray-500">No products yet.</p></Card>
        ) : (
          <div className="space-y-3">
            {products.map((p) => (
              <Card key={p.id}>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{p.name}</h3>
                    {p.brand && <p className="text-sm text-gray-500">{p.brand}</p>}
                    <span className="inline-block mt-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{p.category}</span>
                    <p className="text-sm text-gray-600 mt-2">{p.why_recommended}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
