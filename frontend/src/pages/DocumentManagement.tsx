import { Upload, FileText, Download, MoreVertical, CheckCircle2, AlertCircle, UploadCloud, File } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { apiClient } from '@/lib/api';
import { useEffect, useState, useRef } from 'react';
import DocumentStatsCards from '@/components/DocumentStatsCards';

export default function DocumentManagement() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [statsRefreshTrigger, setStatsRefreshTrigger] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDocuments();
    // Poll every 5 seconds to update status
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await apiClient.get('/documents');
      setDocuments(data);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', 'Manual');

    try {
      await apiClient.post('/documents/upload', formData);
      await fetchDocuments();
      // Trigger stats refresh
      setStatsRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error("Failed to upload", error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const processingDocs = documents.filter(d => d.status === 'processing');

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Document Hub</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Ingest and process industrial documents</p>
        </div>
        <div>
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt,.csv" 
          />
          <Button className="flex items-center" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
            <UploadCloud className="w-4 h-4 mr-2" />
            {isUploading ? 'Uploading...' : 'Upload Document'}
          </Button>
        </div>
      </div>

      {/* Document Statistics Cards */}
      <DocumentStatsCards refreshTrigger={statsRefreshTrigger} />

      <div className="grid gap-6 md:grid-cols-3">
        <Card 
          className="col-span-1 border-dashed border-2 bg-muted/30 hover:bg-muted/80 transition-colors cursor-pointer flex flex-col items-center justify-center h-48"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-8 w-8 text-muted-foreground mb-4" />
          <p className="text-sm font-medium">Click or Drag & drop files here</p>
          <p className="text-xs text-sm text-muted-foreground mt-1.5">PDF, DOCX, XLSX, TXT up to 50MB</p>
        </Card>
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Processing Queue</CardTitle>
            <CardDescription>Documents currently being analyzed by AI</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {processingDocs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No documents are currently processing.</p>
              ) : (
                processingDocs.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-8 w-8 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium">{doc.title}</p>
                        <p className="text-xs text-muted-foreground">Extracting text and relationships...</p>
                      </div>
                    </div>
                    <Badge variant="secondary" className="animate-pulse">Processing</Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Document Repository</CardTitle>
          <CardDescription>All indexed knowledge sources</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <File className="h-4 w-4 text-muted-foreground" />
                    {doc.title}
                  </TableCell>
                  <TableCell><Badge variant="outline">{doc.type}</Badge></TableCell>
                  <TableCell className="text-muted-foreground">{doc.size}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{doc.equipment_tags || "N/A"}</TableCell>
                  <TableCell>
                    {doc.status === 'processed' ? <span className="flex items-center gap-1 text-emerald-500 text-sm"><CheckCircle2 className="h-4 w-4"/> Indexed</span> :
                     doc.status === 'processing' ? <span className="flex items-center gap-1 text-blue-500 text-sm"><div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" /> Processing</span> :
                     <span className="flex items-center gap-1 text-destructive text-sm"><AlertCircle className="h-4 w-4"/> Failed</span>}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon"><Download className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
