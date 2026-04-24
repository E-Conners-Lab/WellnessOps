"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, APIError } from "@/lib/api";
import type { UserProfile } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const checkSession = useCallback(async () => {
    try {
      const response = await api.get<UserProfile>("/auth/me");
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email: string, password: string) => {
    const response = await api.post<UserProfile>("/auth/login", {
      email,
      password,
    });
    setUser(response.data);
    router.push("/dashboard");
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Clear state even if logout request fails
    }
    setUser(null);
    router.push("/login");
  };

  return { user, loading, login, logout, checkSession };
}
