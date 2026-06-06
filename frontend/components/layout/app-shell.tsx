"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Boxes,
  ClipboardList,
  FileBarChart,
  LayoutDashboard,
  LogOut,
  Menu,
  PackageMinus,
  ShieldCheck,
  ShoppingCart,
  X
} from "lucide-react";
import { useState, type ComponentType, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/lib/types";

const navItems: Array<{
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  roles: UserRole[];
}> = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["OWNER", "PURCHASE", "GUDANG"] },
  { href: "/owner", label: "Owner", icon: ShieldCheck, roles: ["OWNER"] },
  { href: "/inventory", label: "Inventory", icon: Boxes, roles: ["OWNER", "PURCHASE", "GUDANG"] },
  { href: "/purchase", label: "Purchase", icon: ShoppingCart, roles: ["OWNER", "PURCHASE", "GUDANG"] },
  { href: "/waste", label: "Waste", icon: PackageMinus, roles: ["OWNER", "GUDANG"] },
  { href: "/reports", label: "Laporan", icon: FileBarChart, roles: ["OWNER"] }
];

export function AppShell({
  title,
  description,
  children
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const visibleItems = navItems.filter((item) => user && item.roles.includes(user.role));

  const Sidebar = (
    <aside className="flex h-full w-72 flex-col border-r bg-card">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="grid h-10 w-10 place-items-center rounded-md bg-primary text-primary-foreground">
          <BarChart3 className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">ATA PIMS</p>
          <p className="text-xs text-muted-foreground">Cafe & Billiard</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={cn(
                "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                active && "bg-accent text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <div className="mb-3">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="text-xs text-muted-foreground">{user?.role}</p>
        </div>
        <Button variant="outline" className="w-full justify-start" onClick={logout}>
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="hidden fixed inset-y-0 left-0 z-30 lg:block">{Sidebar}</div>
      {open ? (
        <div className="fixed inset-0 z-40 bg-black/40 lg:hidden">
          <div className="h-full w-72">
            {Sidebar}
            <Button
              size="icon"
              variant="secondary"
              className="absolute left-[18.5rem] top-3"
              onClick={() => setOpen(false)}
              aria-label="Tutup menu"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : null}
      <main className="lg:pl-72">
        <header className="sticky top-0 z-20 flex min-h-16 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur sm:px-6">
          <Button size="icon" variant="ghost" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Buka menu">
            <Menu className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-lg font-semibold sm:text-xl">{title}</h1>
            {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
          </div>
        </header>
        <div className="mx-auto w-full max-w-7xl p-4 sm:p-6">{children}</div>
      </main>
    </div>
  );
}
