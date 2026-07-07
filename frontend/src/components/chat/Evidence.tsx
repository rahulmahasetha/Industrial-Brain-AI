import { ShieldCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export function Evidence({ evidence }: { evidence?: any[] }) {
  if (!evidence || evidence.length === 0) return null;
  return (
    <Card className="border-border/70 bg-card/80">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Evidence</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {evidence.map((item, index) => (
            <div key={index} className="rounded-md border bg-background/60 p-3">
              <div className="font-medium">{item.document_name || item.title || 'Document'}</div>
              {(item.page_number || item.section) && (
                <div className="text-xs text-muted-foreground mt-1">
                  {item.page_number ? `Page ${item.page_number}` : ''}
                  {item.page_number && item.section ? ' • ' : ''}
                  {item.section ? `${item.section}` : ''}
                </div>
              )}
              {item.excerpt && <p className="mt-2 text-sm text-muted-foreground">{item.excerpt}</p>}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
