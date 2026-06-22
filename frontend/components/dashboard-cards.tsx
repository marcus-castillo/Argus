import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatPercent } from "@/lib/utils";
import type { DashboardStats } from "@/lib/api/types";

export function DashboardCards({ stats }: { stats: DashboardStats }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Total citations" value={stats.total_citations} />
      <StatCard
        label="Verified"
        value={stats.verified}
        accent="text-emerald-600"
      />
      <StatCard
        label="Suspicious"
        value={stats.suspicious}
        accent="text-amber-600"
      />
      <StatCard
        label="Hallucinated"
        value={stats.hallucinated}
        accent="text-red-600"
      />

      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Verification rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold">
            {formatPercent(stats.verification_rate)}
          </div>
          <Progress
            className="mt-3"
            value={stats.verification_rate * 100}
            indicatorClassName="bg-emerald-500"
          />
        </CardContent>
      </Card>

      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Average confidence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold">
            {formatPercent(stats.average_confidence)}
          </div>
          <Progress
            className="mt-3"
            value={stats.average_confidence * 100}
            indicatorClassName="bg-primary"
          />
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${accent ?? ""}`}>{value}</div>
      </CardContent>
    </Card>
  );
}
