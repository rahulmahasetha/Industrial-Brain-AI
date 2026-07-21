import { useEffect, useState } from 'react';
import { ExternalLink, FileSearch, FileText, Layers3, RefreshCw, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { apiClient } from '@/lib/api';

import { API_ORIGIN } from '@/lib/config';

export default function PageIndex() {
  const [pages, setPages] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [selectedPage, setSelectedPage] = useState<any | null>(null);
  const [viewer, setViewer] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  const loadPages = async (search = query, p = page, size = pageSize) => {
    setIsLoading(true);
    try {
      const skip = (p - 1) * size;
      const endpoint = search.trim()
        ? `/page-index/search?q=${encodeURIComponent(search.trim())}&skip=${skip}&limit=${size}`
        : `/page-index?skip=${skip}&limit=${size}`;
      const data = await apiClient.get(endpoint);
      setPages(data.data || (Array.isArray(data) ? data : []));
      setTotalCount(data.total || (Array.isArray(data) ? data.length : 0));
    } catch (error) {
      console.error('Failed to load page index', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPages('');
    apiClient.get('/dashboard/stats').then(setStats).catch(console.error);
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

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Page Index</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Page-level retrieval, metadata, and GraphRAG citations</p>
        </div>
        <Button variant="outline" onClick={() => loadPages(query, page, pageSize)} disabled={isLoading}>
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
            <div className="text-2xl font-bold">{stats?.total_indexed_pages ?? '—'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">{stats?.total_documents ?? '—'} source documents</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Page Chunks</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_chunks ?? '—'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Used only for page ranking</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Index Status</CardTitle>
            <FileSearch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_indexed_pages ? 'Ready' : 'Empty'}</div>
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
              setPage(1);
              loadPages(query, 1, pageSize);
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
              {(pages || []).map((page) => (
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

          <div className="flex items-center justify-between pt-4">
            <div className="text-sm text-muted-foreground">
              Showing {totalCount === 0 ? 0 : (page - 1) * pageSize + 1} to {Math.min(page * pageSize, totalCount)} of {totalCount} results
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Rows per page</span>
                <select
                  className="rounded-md border p-1 text-sm bg-background"
                  value={pageSize}
                  onChange={(e) => {
                    const newSize = Number(e.target.value);
                    setPageSize(newSize);
                    setPage(1);
                    loadPages(query, 1, newSize);
                  }}
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1 || isLoading}
                  onClick={() => {
                    const newPage = page - 1;
                    setPage(newPage);
                    loadPages(query, newPage, pageSize);
                  }}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * pageSize >= totalCount || isLoading}
                  onClick={() => {
                    const newPage = page + 1;
                    setPage(newPage);
                    loadPages(query, newPage, pageSize);
                  }}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
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
