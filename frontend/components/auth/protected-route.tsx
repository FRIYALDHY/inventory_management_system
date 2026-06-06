"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/features/auth/auth-provider";
import type { UserRole } from "@/lib/types";

export function ProtectedRoute({
  children,
  roles
}: {
  children: ReactNode;
  roles?: UserRole[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, pathname, router, user]);

  if (loading) {
    return <div className="grid min-h-screen place-items-center text-sm text-muted-foreground">Memuat sesi...</div>;
  }

  if (!user) return null;

  if (roles && !roles.includes(user.role)) {
    return (
      <div className="grid min-h-screen place-items-center p-6">
        <div className="max-w-md rounded-lg border bg-card p-6 text-center">
          <h1 className="text-lg font-semibold">Akses dibatasi</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Role Anda tidak memiliki akses ke halaman ini.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
