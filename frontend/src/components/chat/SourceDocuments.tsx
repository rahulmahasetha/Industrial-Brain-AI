import { FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

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
        <div className="flex flex-wrap gap-2">
          {parsedDocs.map((doc: any, index: number) => {
            const label = typeof doc === 'string' ? doc : (doc.document_name || doc.title || 'Document');
            return (
              <Badge 
                key={index} 
                variant="outline" 
                className="cursor-pointer hover:bg-primary/20 bg-background/60"
              >
                {label}
              </Badge>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
