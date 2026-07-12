import { ExternalLink, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

function valueOrFallback(value: any, fallback = 'N/A') {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value);
}

export function SourceDocuments({ documents }: { documents?: any[] }) {
  if (!documents || documents.length === 0) return null;
  
  // Try to parse if it's a string like "doc1,doc2"
  let parsedDocs = documents;
  if (typeof documents === 'string') {
    parsedDocs = (documents as string).split(',').map(s => s.trim()).filter(Boolean);
  }

  if (parsedDocs.length === 0) return null;

  return (
    <Card className="border-border/70 bg-card/80">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
          <FileText className="h-4 w-4" />
        </div>
        <CardTitle className="text-base">Source Documents</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {parsedDocs.map((doc: any, index: number) => {
            const label = typeof doc === 'string' ? doc : (doc.document_name || doc.title || doc.document_id || 'Document');
            const page = typeof doc === 'string' ? '' : valueOrFallback(doc.page_number, '');
            const section = typeof doc === 'string' ? '' : valueOrFallback(doc.section || doc.section_title, '');
            const confidence = typeof doc === 'string' ? null : doc.confidence;
            return (
              <div
                key={`${label}-${index}`}
                className="rounded-lg border border-border/70 bg-background/70 p-3 text-sm"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">
                    {index + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex min-w-0 flex-wrap items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="break-words font-semibold text-foreground">{label}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      {page && (
                        <Badge variant="outline" className="rounded-md bg-primary/5 text-[11px] text-primary">
                          Page {page}
                        </Badge>
                      )}
                      {section && (
                        <Badge variant="outline" className="max-w-full rounded-md bg-muted/60 text-[11px] text-muted-foreground">
                          <span className="truncate">Section: {section}</span>
                        </Badge>
                      )}
                      {confidence !== null && confidence !== undefined && (
                        <Badge variant="outline" className="rounded-md bg-emerald-500/10 text-[11px] text-emerald-600 dark:text-emerald-400">
                          {confidence}% match
                        </Badge>
                      )}
                      {doc?.page_index_id && (
                        <Badge variant="outline" className="rounded-md bg-background text-[11px] text-muted-foreground">
                          <ExternalLink className="h-3 w-3" />
                          Indexed page
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
