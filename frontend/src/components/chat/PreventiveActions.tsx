import { ShieldCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export function PreventiveActions({ actions }: { actions?: string[] }) {
  if (!actions || actions.length === 0) return null;
  return (
    <Card className="border-border/70 bg-card/80">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Preventive Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm text-muted-foreground">
          {actions.map((item, index) => (
            <li key={index} className="flex gap-2">
              <span className="shrink-0 text-primary">•</span>{item}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
