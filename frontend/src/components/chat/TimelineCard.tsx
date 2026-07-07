import { History } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function riskClasses(level?: string) {
  const value = (level || '').toLowerCase();
  if (value.includes('critical')) return 'bg-red-500/15 text-red-400 border-red-500/30';
  if (value.includes('high')) return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
  if (value.includes('medium')) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  if (value.includes('low')) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
}

export function TimelineCard({ timeline }: { timeline?: any[] }) {
  if (!timeline || timeline.length === 0) return null;
  return (
    <Card className="border-border/70 bg-card/80">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <History className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Failure History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {timeline.map((item, index) => (
            <div key={index} className="grid grid-cols-[88px_1fr] gap-3 text-sm">
              <div className="text-muted-foreground">{item.date}</div>
              <div className="rounded-md border bg-background/60 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{item.title || item.event}</span>
                  {item.severity && (
                    <Badge variant="outline" className={riskClasses(item.severity)}>
                      {item.severity}
                    </Badge>
                  )}
                </div>
                {(item.root_cause || item.description) && (
                  <p className="mt-1 text-muted-foreground">{item.root_cause || item.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
