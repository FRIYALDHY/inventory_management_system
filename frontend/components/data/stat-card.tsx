import type { ComponentType } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StatCard({
  title,
  value,
  icon: Icon,
  tone = "default"
}: {
  title: string;
  value: string | number;
  icon: ComponentType<{ className?: string }>;
  tone?: "default" | "warning" | "danger" | "info";
}) {
  const toneClass = {
    default: "bg-primary/10 text-primary",
    warning: "bg-secondary text-secondary-foreground",
    danger: "bg-destructive/10 text-destructive",
    info: "bg-accent text-accent-foreground"
  }[tone];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`grid h-9 w-9 place-items-center rounded-md ${toneClass}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

