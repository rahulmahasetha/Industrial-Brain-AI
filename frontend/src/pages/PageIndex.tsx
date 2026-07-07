import { useEffect, useMemo, useState } from 'react';
import { ExternalLink, FileSearch, FileText, Layers3, RefreshCw, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { apiClient } from '@/lib/api';

const API_ORIGIN = 'http://localhost:8000';

export default function PageIndex() {
  const [pages, setPages] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [selectedPage, setSelectedPage] = useState<any | null>(null);
  const [viewer, setViewer] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadPages = async (search = query) => {
    setIsLoading(true);
    try {
      const endpoint = search.trim()
        ? `/page-index/search?q=${encodeURIComponent(search.trim())}`
        : '/page-index';
      const data = await apiClient.get(endpoint);
      setPages(data);
    } catch (error) {
      console.error('Failed to load page index', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPages('');
  }, []);

  const openPage = async (page: any) => {
    setSelectedPage(page);
    setViewer(null);
    try {
      const data = await apiClient.get(`/page-index/${page.id}/viewer`);
      setViewer(data);
    } catch (error) {
      console.error('Failed to load page viewer', error);
    }
  };

  const totals = useMemo(() => {
    const indexed = pages.filter((page) => page.indexing_status === 'indexed').length;
    const docs = new Set(pages.map((page) => page.document_id)).size;
    const chunks = pages.reduce((sum, page) => sum + (page.chunk_ids?.length || 0), 0);
    return { indexed, docs, chunks };
  }, [pages]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Page Index</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Page-level retrieval, metadata, and GraphRAG citations</p>
        </div>
        <Button variant="outline" onClick={() => loadPages()} disabled={isLoading}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Indexed Pages</CardTitle>
            <Layers3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totals.indexed}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">{totals.docs} source documents</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Page Chunks</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totals.chunks}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Used only for page ranking</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Index Status</CardTitle>
            <FileSearch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pages.length ? 'Ready' : 'Empty'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Page-first retrieval enabled</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Indexed Pages</CardTitle>
          <CardDescription>Search by document, page text, equipment, section, or keyword</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              loadPages();
            }}
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search FM101, shutdown, inspection, ISO 22000, page text..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              <Search className="mr-2 h-4 w-4" />
              Search
            </Button>
          </form>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Document</TableHead>
                <TableHead>Page</TableHead>
                <TableHead>Section</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Keywords</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Open</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pages.map((page) => (
                <TableRow key={page.id}>
                  <TableCell className="max-w-[260px] font-medium">
                    <div className="truncate">{page.document_name}</div>
                  </TableCell>
                  <TableCell>{page.page_number}</TableCell>
                  <TableCell className="max-w-[220px] text-muted-foreground">
                    <div className="truncate">{page.section_title || 'N/A'}</div>
                  </TableCell>
                  <TableCell>
                    <div className="flex max-w-[180px] flex-wrap gap-1">
                      {(page.equipment_ids || []).slice(0, 3).map((id: string) => (
                        <Badge key={id} variant="outline">{id}</Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="max-w-[220px] text-xs text-muted-foreground">
                    <div className="truncate">{(page.keywords || []).join(', ') || 'N/A'}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={page.indexing_status === 'indexed' ? 'default' : 'secondary'}>
                      {page.indexing_status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openPage(page)}>
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={Boolean(selectedPage)} onOpenChange={(open) => !open && setSelectedPage(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedPage?.document_name} - Page {selectedPage?.page_number}</DialogTitle>
            <DialogDescription>{selectedPage?.section_title || 'No section title detected'}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
            <div className="space-y-4">
              <div className="rounded-md border p-4">
                <div className="mb-2 text-sm font-medium">Extracted Metadata</div>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p>Embedding: {selectedPage?.embedding_id || 'Pending'}</p>
                  <p>Chunks: {(selectedPage?.chunk_ids || []).join(', ') || 'Pending'}</p>
                  <p>Equipment: {(selectedPage?.equipment_ids || []).join(', ') || 'N/A'}</p>
                  <p>Keywords: {(selectedPage?.keywords || []).join(', ') || 'N/A'}</p>
                </div>
              </div>

              <div className="rounded-md border p-4">
                <div className="mb-2 text-sm font-medium">Page Summary</div>
                <p className="text-sm text-muted-foreground">{selectedPage?.page_summary || 'No summary available.'}</p>
              </div>

              {viewer?.pdf_url ? (
                <Button asChild className="w-full">
                  <a href={`${API_ORIGIN}${viewer.pdf_url}`} target="_blank" rel="noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Open PDF on Page {selectedPage?.page_number}
                  </a>
                </Button>
              ) : (
                <Button className="w-full" disabled>PDF file not found</Button>
              )}
            </div>

            <div className="space-y-4">
              <div className="rounded-md border bg-amber-500/10 p-4">
                <div className="mb-2 text-sm font-medium">Highlighted Paragraph</div>
                <p className="text-sm leading-6">{viewer?.highlight_text || selectedPage?.page_summary || 'No highlight available.'}</p>
              </div>
              <div className="max-h-[420px] overflow-y-auto rounded-md border p-4">
                <div className="mb-2 text-sm font-medium">Extracted Text</div>
                <p className="whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{selectedPage?.extracted_text}</p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
