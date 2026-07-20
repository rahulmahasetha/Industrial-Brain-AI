import { useState, useEffect } from 'react';
import { 
  ShieldCheck, AlertTriangle, CheckCircle2, AlertCircle, FileText, Download, Target, 
  BarChart3, Loader2, ArrowRight, Lightbulb
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { apiClient } from '@/lib/api';

interface ComplianceSummary {
  total: number;
  compliant: number;
  non_compliant: number;
  gaps: number;
  overdue: number;
  compliance_percentage: number;
  critical_items: number;
}

interface HeatmapAsset {
  asset_tag: string;
  compliant: number;
  non_compliant: number;
  gaps: number;
  critical_risks: number;
}

interface ComplianceRecord {
  id: number;
  standard: string;
  section: string;
  requirement: string;
  status: string;
  risk_level: string;
  asset_tag: string;
  due_date: string;
  last_audit: string;
}

export default function ComplianceAgent() {
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapAsset[]>([]);
  const [records, setRecords] = useState<ComplianceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAuditing, setIsAuditing] = useState(false);
  const [selectedStandard, setSelectedStandard] = useState("All");
  const [selectedRecord, setSelectedRecord] = useState<ComplianceRecord | null>(null);
  const [explanation, setExplanation] = useState<string>("");
  const [isExplaining, setIsExplaining] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sumRes, heatRes, recRes] = await Promise.all([
        apiClient.get('/compliance/summary'),
        apiClient.get('/compliance/heatmap'),
        apiClient.get('/compliance')
      ]);
      setSummary(sumRes);
      setHeatmap(heatRes);
      setRecords(recRes);
    } catch (err) {
      console.error("Failed to load compliance data", err);
    } finally {
      setLoading(false);
    }
  };

  const runAudit = async () => {
    try {
      setIsAuditing(true);
      // Calls the real agent backend to perform a global auto-audit
      await apiClient.post('/compliance/auto-audit', {});
      // Refresh data
      await fetchData();
    } catch (err) {
      console.error("Audit failed", err);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleExplainClause = async (record: ComplianceRecord) => {
    try {
      setIsExplaining(true);
      const res = await apiClient.post('/compliance/explain', {
        standard: record.standard,
        clause: record.section || "General",
        requirement: record.requirement
      });
      setExplanation(res.explanation);
    } catch (err) {
      console.error("Explanation failed", err);
      setExplanation("Failed to generate AI explanation. Please check backend connection.");
    } finally {
      setIsExplaining(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'compliant': return <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">Compliant</Badge>;
      case 'non_compliant': return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Non-Compliant</Badge>;
      case 'gap': return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Gap Found</Badge>;
      case 'overdue': return <Badge variant="outline" className="bg-rose-50 text-rose-700 border-rose-200">Overdue</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'critical': return <Badge variant="destructive" className="bg-red-500">Critical</Badge>;
      case 'high': return <Badge variant="destructive" className="bg-rose-500">High</Badge>;
      case 'medium': return <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">Medium</Badge>;
      case 'low': return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300">Low</Badge>;
      default: return <Badge variant="outline">{risk}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 no-print">
        <div>
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
            <ShieldCheck className="h-3.5 w-3.5" /> REGULATORY INTELLIGENCE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">Compliance Agent</h1>
          <p className="text-sm text-slate-500 mt-1.5">Map regulatory requirements against current procedures, identify gaps, and generate audit evidence.</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button variant="outline" className="w-full sm:w-auto">
            <Download className="w-4 h-4 mr-2" /> Export Package
          </Button>
          <Button className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 text-white" onClick={runAudit} disabled={isAuditing}>
            {isAuditing ? (
              <span className="flex items-center"><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Scanning...</span>
            ) : (
              <span className="flex items-center"><Target className="w-4 h-4 mr-2" /> Run Global Audit</span>
            )}
          </Button>
        </div>
      </div>

      {/* Summary Scorecards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-emerald-50 border-emerald-100">
          <CardContent className="p-4 sm:p-6 flex flex-col justify-center">
            <div className="flex justify-between items-start">
              <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Compliance Score</p>
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
            </div>
            <h2 className="text-3xl font-extrabold text-emerald-900 mt-2">{summary?.compliance_percentage}%</h2>
            <div className="w-full bg-emerald-200 rounded-full h-1.5 mt-4">
              <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: `${summary?.compliance_percentage}%` }} />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-6">
            <div className="flex justify-between items-start">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Requirements</p>
              <FileText className="h-4 w-4 text-slate-400" />
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-2">{summary?.total}</h2>
            <p className="text-xs text-slate-500 mt-2">Mapped clauses</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 sm:p-6">
            <div className="flex justify-between items-start">
              <p className="text-xs font-bold text-amber-600 uppercase tracking-wider">Identified Gaps</p>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <h2 className="text-3xl font-extrabold text-amber-900 mt-2">{summary?.gaps}</h2>
            <p className="text-xs text-amber-700 mt-2">Procedure mismatches</p>
          </CardContent>
        </Card>

        <Card className={summary?.critical_items && summary.critical_items > 0 ? "bg-red-50 border-red-100" : ""}>
          <CardContent className="p-4 sm:p-6">
            <div className="flex justify-between items-start">
              <p className="text-xs font-bold text-red-600 uppercase tracking-wider">Critical Risks</p>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </div>
            <h2 className="text-3xl font-extrabold text-red-900 mt-2">{summary?.critical_items}</h2>
            <p className="text-xs text-red-700 mt-2">Non-compliant / Overdue</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Heatmap */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-emerald-600" /> Asset Risk Heatmap
            </CardTitle>
            <CardDescription>Compliance concentration by equipment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {heatmap.length === 0 ? (
                <p className="text-sm text-slate-500">No asset data available.</p>
              ) : heatmap.map((asset, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${asset.critical_risks > 0 ? 'bg-red-500 animate-pulse' : asset.gaps > 0 ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                    <span className="font-semibold text-sm">{asset.asset_tag}</span>
                  </div>
                  <div className="flex gap-2">
                    {asset.critical_risks > 0 && <span className="text-xs font-medium text-red-600 bg-red-100 px-2 py-0.5 rounded">{asset.critical_risks} Critical</span>}
                    {asset.gaps > 0 && <span className="text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded">{asset.gaps} Gaps</span>}
                    {asset.critical_risks === 0 && asset.gaps === 0 && <span className="text-xs font-medium text-emerald-600"><CheckCircle2 className="w-4 h-4" /></span>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Requirements Grid */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
            <div>
              <CardTitle className="text-base">Compliance Audit Results</CardTitle>
              <CardDescription>Detailed gap analysis against regulations</CardDescription>
            </div>
            <select 
              className="text-sm border border-slate-200 rounded-md px-3 py-1.5 bg-white shadow-sm"
              value={selectedStandard}
              onChange={(e) => setSelectedStandard(e.target.value)}
            >
              <option value="All">All Standards</option>
              {Array.from(new Set(records.map(r => r.standard))).map(std => (
                <option key={std} value={std}>{std}</option>
              ))}
            </select>
          </CardHeader>
          <CardContent className="px-0 sm:px-6">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Clause</TableHead>
                    <TableHead className="min-w-[200px]">Requirement</TableHead>
                    <TableHead>Asset</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records
                    .filter(r => selectedStandard === "All" || r.standard.includes(selectedStandard))
                    .map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-mono text-xs font-medium text-slate-600">
                        {record.section || record.standard}
                      </TableCell>
                      <TableCell className="text-sm">
                        <div className="line-clamp-2" title={record.requirement}>
                          {record.requirement}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs font-semibold text-slate-500">
                        {record.asset_tag || '-'}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(record.status)}
                      </TableCell>
                      <TableCell>
                        {getRiskBadge(record.risk_level)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 h-8"
                          onClick={() => {
                            setSelectedRecord(record);
                            setExplanation("");
                          }}
                        >
                          Details <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {records.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-500 text-sm">
                        No compliance records found. Run a Global Audit.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

      </div>

      {/* Details Dialog */}
      <Dialog open={!!selectedRecord} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Compliance Details
            </DialogTitle>
            <DialogDescription>
              {selectedRecord?.standard} - {selectedRecord?.section}
            </DialogDescription>
          </DialogHeader>
          
          {selectedRecord && (
            <div className="space-y-6 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <p className="text-xs text-slate-500 font-medium mb-1">Status</p>
                  <div>{getStatusBadge(selectedRecord.status)}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <p className="text-xs text-slate-500 font-medium mb-1">Risk Level</p>
                  <div>{getRiskBadge(selectedRecord.risk_level)}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <p className="text-xs text-slate-500 font-medium mb-1">Asset Target</p>
                  <p className="font-semibold text-slate-900">{selectedRecord.asset_tag || "Global"}</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <p className="text-xs text-slate-500 font-medium mb-1">Due Date</p>
                  <p className="font-semibold text-slate-900">{selectedRecord.due_date || "N/A"}</p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-900 mb-2">Requirement Clause</h4>
                <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-lg text-sm text-blue-900 leading-relaxed">
                  {selectedRecord.requirement}
                </div>
              </div>

              <div className="pt-2">
                {!explanation ? (
                  <Button 
                    variant="outline" 
                    className="w-full border-blue-200 text-blue-700 hover:bg-blue-50"
                    onClick={() => handleExplainClause(selectedRecord)}
                    disabled={isExplaining}
                  >
                    {isExplaining ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> AI Analyzing Clause...</>
                    ) : (
                      <><Lightbulb className="w-4 h-4 mr-2" /> Explain Clause Implications</>
                    )}
                  </Button>
                ) : (
                  <div className="bg-slate-900 rounded-lg p-4 shadow-inner max-h-[250px] overflow-y-auto">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <Lightbulb className="w-3.5 h-3.5" /> AI Interpretation
                    </h4>
                    <div className="text-sm text-slate-200 leading-relaxed prose prose-sm prose-invert max-w-none">
                      <ReactMarkdown>{explanation}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
