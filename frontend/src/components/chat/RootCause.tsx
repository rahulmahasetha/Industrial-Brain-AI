import { AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export function RootCause({ cause }: { cause?: string }) {
  if (!cause) return null;
  return (
    <Card className="border-border/70 bg-card/80">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Root Cause</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm font-medium">{cause}</p>
      </CardContent>
    </Card>
  );
}
