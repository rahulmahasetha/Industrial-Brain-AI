import { Upload, FileText, Download, CheckCircle2, AlertCircle, UploadCloud, File, Trash2, Search, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { apiClient } from '@/lib/api';
import { useEffect, useState, useRef } from 'react';
import DocumentStatsCards from '@/components/DocumentStatsCards';

export default function DocumentManagement() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [statsRefreshTrigger, setStatsRefreshTrigger] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [docToDelete, setDocToDelete] = useState<any | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<boolean>(false);

  const fetchDocuments = async () => {
    try {
      const url = searchQuery ? `/documents/?q=${encodeURIComponent(searchQuery)}` : '/documents/';
      const data = await apiClient.get(url);
      setDocuments(data);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll every 5 seconds to update status
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, [searchQuery]);

  const handleDeleteClick = (doc: any) => {
    setDocToDelete(doc);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!docToDelete) return;
    try {
      await apiClient.delete(`/documents/${docToDelete.id}`);
      await fetchDocuments();
      // Trigger stats refresh
      setStatsRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error("Failed to delete document", error);
    } finally {
      setDeleteDialogOpen(false);
      setDocToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setDocToDelete(null);
  };

  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('Manual');
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);

  const DOCUMENT_CATEGORIES = [
    { value: 'Manual', label: 'Equipment Manual', icon: '📘', desc: 'Operating manuals and schematics for machinery' },
    { value: 'SOP', label: 'SOP', icon: '📋', desc: 'Standard Operating Procedures for operations' },
    { value: 'Maintenance Log', label: 'Maintenance Log', icon: '🔧', desc: 'Logs of scheduled/unscheduled maintenance tasks' },
    { value: 'Incident Report', label: 'Incident Report', icon: '⚠️', desc: 'Reports on equipment faults or safety events' },
    { value: 'Inspection Report', label: 'Inspection Report', icon: '🔍', desc: 'Safety and operation inspection logs' },
    { value: 'Quality Report', label: 'Quality Report', icon: '📊', desc: 'QA inspection logs and batch reports' },
    { value: 'Compliance Document', label: 'Compliance Document', icon: '🛡️', desc: 'ISO standards, regulatory filings' },
    { value: 'Expert Note', label: 'Expert Note', icon: '🧠', desc: 'Notes and tips from senior engineers' },
    { value: 'Training Manual', label: 'Training Manual', icon: '📚', desc: 'Staff training guides and checklists' },
    { value: 'RCA Report', label: 'RCA Report', icon: '🔍', desc: 'Root Cause Analysis on chronic failures' }
  ];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setPendingFile(file);
    setSelectedCategory('Manual');
    setDialogOpen(true);
  };

  const handleConfirmUpload = async () => {
    if (!pendingFile) return;

    setDialogOpen(false);
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', pendingFile);
    formData.append('doc_type', selectedCategory);

    try {
      await apiClient.post('/documents/upload', formData);
      await fetchDocuments();
      // Trigger stats refresh
      setStatsRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error("Failed to upload", error);
    } finally {
      setIsUploading(false);
      setPendingFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleCancelUpload = () => {
    setDialogOpen(false);
    setPendingFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
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
            onChange={handleFileSelect}
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
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle>Document Repository</CardTitle>
            <CardDescription>All indexed knowledge sources</CardDescription>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by title, type, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>File Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Upload Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc, index) => (
                <TableRow key={doc.id}>
                  <TableCell className="text-slate-500 font-mono text-sm">{index + 1}</TableCell>
                  <TableCell className="font-medium flex items-center gap-2">
                    <File className="h-4 w-4 text-muted-foreground" />
                    {doc.title}
                  </TableCell>
                  <TableCell><Badge variant="outline">{doc.type}</Badge></TableCell>
                  <TableCell className="text-muted-foreground">{doc.size}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{doc.equipment_tags || "N/A"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {doc.created_at ? new Date(doc.created_at).toLocaleString() : "N/A"}
                  </TableCell>
                  <TableCell>
                    {doc.status === 'processed' ? <span className="flex items-center gap-1 text-emerald-500 text-sm"><CheckCircle2 className="h-4 w-4"/> Indexed</span> :
                     doc.status === 'processing' ? <span className="flex items-center gap-1 text-blue-500 text-sm"><div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" /> Processing</span> :
                     <span className="flex items-center gap-1 text-destructive text-sm"><AlertCircle className="h-4 w-4"/> Failed</span>}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" title="Download"><Download className="h-4 w-4 text-slate-400" /></Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => handleDeleteClick(doc)}
                      className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                      title="Delete Document"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Category Upload Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) handleCancelUpload(); }}>
        <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-indigo-400" />
              Ingest Document
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Select a knowledge category for the file: <span className="text-indigo-300 font-mono font-medium block mt-1 truncate">{pendingFile?.name}</span>
            </DialogDescription>
          </DialogHeader>
          
          <div className="max-h-[300px] overflow-y-auto space-y-2 pr-1 py-1 custom-scrollbar">
            {DOCUMENT_CATEGORIES.map((cat) => (
              <div 
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value)}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedCategory === cat.value 
                    ? 'bg-indigo-600/20 border-indigo-500 shadow-md shadow-indigo-500/10' 
                    : 'bg-slate-950/40 border-slate-800 hover:bg-slate-850 hover:border-slate-700'
                }`}
              >
                <span className="text-2xl mt-0.5 shrink-0">{cat.icon}</span>
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-semibold block text-slate-200">{cat.label}</span>
                  <span className="text-xs text-slate-400 block truncate mt-0.5">{cat.desc}</span>
                </div>
                <div className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 mt-1 ${
                  selectedCategory === cat.value 
                    ? 'border-indigo-500 bg-indigo-500' 
                    : 'border-slate-700'
                }`}>
                  {selectedCategory === cat.value && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                </div>
              </div>
            ))}
          </div>
          
          <DialogFooter className="flex sm:flex-row gap-2 mt-4">
            <Button 
              variant="ghost" 
              onClick={handleCancelUpload}
              className="flex-1 border border-slate-800 text-slate-400 hover:bg-slate-850 hover:text-white"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleConfirmUpload}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-500/25"
            >
              Confirm & Ingest
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={(open) => { if (!open) handleCancelDelete(); }}>
        <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2 text-red-500">
              <AlertTriangle className="w-5 h-5" />
              Delete Document
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Are you sure you want to delete this document? This action is permanent and will delete all associated pages, chunks, vector embeddings, and knowledge graph links.
            </DialogDescription>
          </DialogHeader>
          
          <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4 my-2">
            <div className="flex items-center gap-3">
              <File className="h-8 w-8 text-indigo-400 shrink-0" />
              <div className="min-w-0">
                <span className="text-sm font-semibold block text-slate-200 truncate">{docToDelete?.title}</span>
                <span className="text-xs text-slate-500 block mt-0.5">{docToDelete?.type} • {docToDelete?.size}</span>
              </div>
            </div>
          </div>
          
          <DialogFooter className="flex sm:flex-row gap-2 mt-4">
            <Button 
              variant="ghost" 
              onClick={handleCancelDelete}
              className="flex-1 border border-slate-800 text-slate-400 hover:bg-slate-850 hover:text-white"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleConfirmDelete}
              className="flex-1 bg-red-650 hover:bg-red-550 text-white font-semibold shadow-lg shadow-red-500/25"
            >
              Delete Permanently
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
