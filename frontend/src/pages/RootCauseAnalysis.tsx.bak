import { useState, useRef } from 'react';
import { Activity, ShieldAlert, FileSearch, Network, GitMerge, FileText, AlertTriangle, Lightbulb, Clock, CheckCircle2, XCircle, Download } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Separator } from '@/components/ui/separator';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useUser } from '@/contexts/UserContext';

export default function RootCauseAnalysis() {
  const { profile } = useUser();
  const [description, setDescription] = useState("Bottle Filling Machine FM101 stopped due to low fill level and nozzle blockage");
  const [assetTag, setAssetTag] = useState("FM101");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>("");
  
  const [baseResult, setBaseResult] = useState<any>(null);

  const [chatInput, setChatInput] = useState("");
  const [chatResponse, setChatResponse] = useState("");
  const [isChatting, setIsChatting] = useState(false);

  const reportRef = useRef<HTMLDivElement>(null);

  const handleAnalyze = async () => {
    if (!description) return;
    
    setIsAnalyzing(true);
    setBaseResult(null);
    setChatResponse("");
    
    try {
      setLoadingStage("Executing forensic RCA pipeline...");
      
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://industrial-brain-ai-zad4.onrender.com/api';
      const res = await fetch(`${API_BASE_URL}/rca/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, asset_tag: assetTag })
      });
      
      if (!res.ok) throw new Error("Failed to execute RCA.");
      const rcaData = await res.json();
      setBaseResult(rcaData);
      
      setIsAnalyzing(false);
    } catch (error) {
      console.error("Analysis Error:", error);
      setIsAnalyzing(false);
    } finally {
      setLoadingStage("");
    }
  };

  const handleAskAI = async (causeDescription: string) => {
    if (!chatInput.trim()) return;
    setIsChatting(true);
    setChatResponse("");
    try {
      const prompt = `Context: Root Cause Analysis for ${assetTag}. The user is asking about the following root cause: "${causeDescription}". User question: ${chatInput}`;
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://industrial-brain-ai-zad4.onrender.com/api';
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: prompt, history: [] })
      });
      const data = await res.json();
      setChatResponse(data.content);
    } catch (error) {
      console.error("Chat error:", error);
      setChatResponse("Failed to communicate with AI.");
    } finally {
      setIsChatting(false);
    }
  };

  const handleExportPDF = () => {
    window.print();
  };

  const reportId = `RCA-${Math.random().toString(36).substr(2, 6).toUpperCase()}-${Date.now().toString().slice(-4)}`;
  const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const timeStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="space-y-6 pb-20 print:p-0 print:bg-white print:text-black" style={{ WebkitPrintColorAdjust: 'exact', printColorAdjust: 'exact' }}>
      
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          @page { size: A4; margin: 0; }
          body { 
            background: white !important; 
            -webkit-print-color-adjust: exact !important; 
            print-color-adjust: exact !important;
          }
          .no-print { display: none !important; }
          
          /* Force accordions open for print */
          [data-state="closed"] {
            display: block !important;
            height: auto !important;
            overflow: visible !important;
          }
          [data-state="closed"] > div {
            animation: none !important;
          }

          .print-break-inside-avoid { break-inside: avoid; }
          .print-border { border: 1px solid #e2e8f0; }
          
          .print-footer { 
            position: fixed; 
            bottom: 0; 
            left: 0; 
            right: 0; 
            height: 60px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 48px;
            background-color: white !important;
            border-top: 1px solid #e2e8f0;
          }
        }
      `}} />

      {/* PRINT ONLY HEADER */}
      {baseResult && (
        <div className="hidden print:block p-12 pb-8 w-full bg-white text-black font-sans">
          {/* 1. Company Header */}
          <div className="border-b-2 border-slate-900 pb-6 mb-8 flex justify-between items-end">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">FreshFlow Beverages Pvt. Ltd.</h1>
              <p className="text-sm text-slate-500 mt-1 font-medium tracking-widest uppercase">Enterprise Knowledge Intelligence</p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-slate-800">Forensic RCA Report</p>
              <p className="text-sm font-mono text-slate-500 mt-1">ID: {reportId}</p>
            </div>
          </div>

          {/* 2. Metadata Grid */}
          <div className="grid grid-cols-2 gap-8 mb-10">
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Generation Details</h3>
              <div className="space-y-2 text-sm">
                <p><span className="font-semibold w-24 inline-block">Date:</span> {dateStr}</p>
                <p><span className="font-semibold w-24 inline-block">Time:</span> {timeStr}</p>
                <p><span className="font-semibold w-24 inline-block">System:</span> Forensic RCA Engine</p>
              </div>
            </div>
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">User Context</h3>
              <div className="space-y-2 text-sm">
                <p><span className="font-semibold w-24 inline-block">Generated By:</span> {profile?.name || 'System Auto'}</p>
                <p><span className="font-semibold w-24 inline-block">Employee ID:</span> {profile?.employee_id || 'N/A'}</p>
                <p><span className="font-semibold w-24 inline-block">Email:</span> {profile?.email || 'N/A'}</p>
                <p><span className="font-semibold w-24 inline-block">Role/Dept:</span> {profile?.role || 'Operations'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PRINT ONLY FOOTER */}
      {baseResult && (
        <div className="hidden print:flex print-footer text-xs text-slate-500 font-mono">
          <span>FRESHFLOW BEVERAGES PVT. LTD. — CONFIDENTIAL</span>
          <span>{dateStr} {timeStr}</span>
        </div>
      )}

      <div className="print:px-12 print:pb-24">

      <div className="flex justify-between items-end no-print">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">AI Investigation Engine</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Deep forensic root cause analysis, evidence validation, and impact assessment.</p>
        </div>
        {baseResult && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExportPDF}>
              <Download className="w-4 h-4 mr-2" />
              Export PDF Report
            </Button>
          </div>
        )}
      </div>

      {/* Input Section */}
      <Card className="no-print border-border bg-card/50 backdrop-blur-sm">
        <CardHeader className="pb-4">
          <CardTitle>Initialize Investigation</CardTitle>
          <CardDescription>Enter the symptom and asset tag to begin the multi-stage AI forensic pipeline.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="w-32">
              <label className="text-xs font-semibold mb-1.5 block text-muted-foreground">Asset Tag</label>
              <Input 
                placeholder="FM101" 
                value={assetTag}
                onChange={(e) => setAssetTag(e.target.value)}
              />
            </div>
            <div className="flex-1">
              <label className="text-xs font-semibold mb-1.5 block text-muted-foreground">Anomaly Symptom</label>
              <Input 
                placeholder="Describe the failure symptom..." 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button className="w-40" onClick={handleAnalyze} disabled={isAnalyzing || !description}>
                {isAnalyzing ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <FileSearch className="w-4 h-4" />
                    Run Investigation
                  </span>
                )}
              </Button>
            </div>
          </div>
          {isAnalyzing && (
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{loadingStage}</span>
                <span className="animate-pulse">Accessing Enterprise Data...</span>
              </div>
              <Progress value={45} className="h-1.5" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Dashboard */}
      {baseResult && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6" ref={reportRef}>
          
          {/* Main Content Column */}
          <div className="md:col-span-2 space-y-6">
            
            {/* Executive & Decision Reasoning */}
            <Card className="print-border print-break-inside-avoid shadow-sm border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-xl flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-blue-500" />
                  Investigation Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted/40 rounded-lg text-sm border">
                  <span className="font-semibold text-foreground block mb-1">Anomaly Profile:</span>
                  {description} (Asset: <Badge variant="outline">{assetTag}</Badge>)
                </div>
                {baseResult.ai_reasoning && (
                  <div>
                    <span className="text-sm font-semibold text-foreground flex items-center gap-1.5 mb-2">
                      <Lightbulb className="w-4 h-4 text-amber-500" />
                      AI Decision Reasoning
                    </span>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {baseResult.ai_reasoning}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Ranked Root Causes & Evidence Chain */}
            <Card className="print-border print-break-inside-avoid">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <GitMerge className="w-5 h-5 text-indigo-500" />
                    Predicted Root Causes & Evidence Chains
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <Accordion type="single" collapsible defaultValue="cause-0" className="w-full">
                  {baseResult.causes?.map((cause: any, idx: number) => (
                    <AccordionItem value={`cause-${idx}`} key={idx} className="border-b-0 mb-4 bg-muted/20 border rounded-lg px-4 overflow-hidden">
                      <AccordionTrigger className="hover:no-underline py-4">
                        <div className="flex items-center gap-4 w-full pr-4 text-left">
                          <div className="w-16 shrink-0 text-center">
                            <span className={`text-lg font-bold ${(cause.probability) > 70 ? 'text-destructive' : (cause.probability) > 40 ? 'text-amber-500' : 'text-blue-500'}`}>
                              {cause.probability}%
                            </span>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-foreground">{cause.description}</h3>
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{cause.mechanism || "Predicted via retrieved evidence"}</p>
                          </div>
                          <Badge variant="outline" className="shrink-0 no-print">
                            {idx === 0 ? "Primary Root Cause" : "Contributing Factor"}
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="pt-2 pb-4 space-y-6">
                        
                        {/* Interactive Tree Vis / Evidence Chain */}
                        {cause.evidence_chain && cause.evidence_chain.length > 0 && (
                          <div className="relative pl-6 py-2">
                            <h4 className="text-xs font-semibold mb-3 flex items-center gap-1.5 uppercase text-muted-foreground">
                              <Network className="w-3.5 h-3.5" /> Traceable Evidence Chain
                            </h4>
                            <div className="absolute left-[11px] top-6 bottom-0 w-px bg-border" />
                            
                            {cause.evidence_chain.map((step: any, sIdx: number) => (
                              <div key={sIdx} className="relative z-10 flex items-start gap-3 text-sm mb-4">
                                <div className={`w-2 h-2 rounded-full mt-1.5 outline outline-4 outline-background ${sIdx === 0 ? 'bg-destructive' : sIdx === cause.evidence_chain.length - 1 ? 'bg-blue-500' : 'bg-amber-500'}`} />
                                <div>
                                  <span className="font-medium">{step.step}: </span>
                                  <span className="text-muted-foreground">{step.description}</span>
                                  {(step.document || step.confidence) && (
                                    <div className="text-[10px] text-muted-foreground mt-0.5 flex gap-2">
                                      {step.document && <span>Doc: {step.document} {step.page ? `(Pg ${step.page})` : ''}</span>}
                                      {step.confidence && <span className="text-blue-500">Conf: {step.confidence}%</span>}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Supporting Evidence Snippets */}
                        {cause.supporting_evidence && cause.supporting_evidence.length > 0 && (
                          <div className="pt-2">
                            <h4 className="text-xs font-semibold mb-2 flex items-center gap-1.5 uppercase text-muted-foreground">
                              <FileSearch className="w-3.5 h-3.5" /> Supporting Document Snippets
                            </h4>
                            <div className="grid gap-2">
                              {cause.supporting_evidence.map((ev: any, evIdx: number) => (
                                <div key={evIdx} className="p-3 bg-background border rounded-md text-xs">
                                  <div className="flex justify-between items-center mb-1.5 pb-1.5 border-b border-border/50">
                                    <span className="font-semibold text-blue-600">{ev.document}</span>
                                    <span className="text-muted-foreground">Pg {ev.page || '?'} | Sec {ev.section || '?'}</span>
                                  </div>
                                  <p className="italic text-muted-foreground">"{ev.snippet}"</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Ask AI Mini-Chat */}
                        <div className="mt-4 pt-4 border-t border-border/50 no-print">
                          <h4 className="text-xs font-semibold mb-2 flex items-center gap-1.5">
                            <Activity className="w-3.5 h-3.5" />
                            Ask AI about this specific cause
                          </h4>
                          <div className="flex gap-2">
                            <Input 
                              placeholder="e.g. How do I verify this?" 
                              value={chatInput}
                              onChange={(e) => setChatInput(e.target.value)}
                              className="h-8 text-xs"
                            />
                            <Button size="sm" className="h-8" onClick={() => handleAskAI(cause.description)} disabled={isChatting}>
                              Ask
                            </Button>
                          </div>
                          {chatResponse && (
                            <div className="mt-3 p-4 bg-primary/5 rounded-md text-sm border border-primary/10 prose prose-sm max-w-none prose-table:w-full prose-table:border-collapse prose-th:bg-muted prose-th:px-3 prose-th:py-2 prose-th:border prose-td:border prose-td:px-3 prose-td:py-2 prose-p:leading-relaxed prose-headings:font-bold">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {chatResponse}
                              </ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card className="print-border print-break-inside-avoid">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  Recommended Corrective Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold border-b pb-1">Immediate Actions</h4>
                    {baseResult.recommendations?.immediate_actions?.length > 0 ? (
                      baseResult.recommendations.immediate_actions.map((act: any, idx: number) => (
                        <div key={idx} className="flex gap-2 text-sm">
                          <div className="w-5 h-5 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0 text-xs font-bold">{idx + 1}</div>
                          <div>
                            <p>{act.action}</p>
                            <span className="text-xs text-muted-foreground">Team: {act.responsible_team} | {act.estimated_time}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No immediate actions generated.</p>
                    )}
                  </div>
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold border-b pb-1">Preventive Actions</h4>
                    {baseResult.recommendations?.preventive_actions?.length > 0 ? (
                      baseResult.recommendations.preventive_actions.map((act: any, idx: number) => (
                        <div key={idx} className="flex gap-2 text-sm">
                          <div className="w-5 h-5 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0 text-xs font-bold">{idx + 1}</div>
                          <div>
                            <p>{act.action}</p>
                            <span className="text-xs text-muted-foreground">Freq: {act.frequency}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No preventive actions generated.</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Final Decision */}
            {baseResult.final_decision && (
              <Card className="print-border print-break-inside-avoid shadow-sm bg-muted/10">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <GitMerge className="w-5 h-5 text-emerald-600" />
                    Final AI Decision
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-foreground leading-relaxed font-medium">
                    {baseResult.final_decision}
                  </p>
                </CardContent>
              </Card>
            )}

          </div>

          {/* Side Column (Evidence, Topology, Timelines) */}
          <div className="space-y-6">
            
            {/* Missing & Contradictory Evidence */}
            {(baseResult.missing_evidence?.length > 0 || baseResult.contradicting_evidence?.length > 0) && (
              <Card className="print-border print-break-inside-avoid border-l-4 border-l-amber-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    Evidence Discrepancies
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  {baseResult.missing_evidence?.length > 0 && (
                    <div>
                      <span className="font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <XCircle className="w-3.5 h-3.5 text-destructive" /> Missing Evidence
                      </span>
                      <ul className="list-disc pl-5 text-muted-foreground space-y-1">
                        {baseResult.missing_evidence.map((item: string, i: number) => <li key={i}>{item}</li>)}
                      </ul>
                    </div>
                  )}
                  {baseResult.missing_evidence?.length > 0 && baseResult.contradicting_evidence?.length > 0 && <Separator />}
                  {baseResult.contradicting_evidence?.length > 0 && (
                    <div>
                      <span className="font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <GitMerge className="w-3.5 h-3.5 text-amber-500" /> Contradictory Evidence
                      </span>
                      <ul className="list-disc pl-5 text-muted-foreground space-y-1">
                        {baseResult.contradicting_evidence.map((item: any, i: number) => (
                          <li key={i}>
                            <strong>{item.document}:</strong> {item.reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Source Documents */}
            <Card className="print-border print-break-inside-avoid">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-500" />
                  Cited Manuals & Docs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {baseResult.sources_cited?.length > 0 ? (
                    baseResult.sources_cited.map((source: string, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded-md border bg-muted/20 hover:bg-muted/40 transition-colors">
                        <span className="text-xs font-medium truncate pr-2" title={source}>{source}</span>
                        <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" title="Open Document">
                          <FileSearch className="h-3 w-3" />
                        </Button>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">No specific documents cited in base RCA.</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Investigation Timeline */}
            <Card className="print-border print-break-inside-avoid">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="w-4 h-4 text-purple-500" />
                  Investigation Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative pl-4 space-y-4 py-2 border-l border-border ml-2">
                  <div className="relative z-10">
                    <div className="absolute -left-[21px] w-2.5 h-2.5 rounded-full bg-destructive outline outline-4 outline-background" />
                    <p className="text-sm font-medium">Anomaly Detected</p>
                    <p className="text-xs text-muted-foreground">Current Event</p>
                  </div>
                  {baseResult.historical_similar_incidents?.map((inc: any, idx: number) => (
                    <div key={idx} className="relative z-10 opacity-70">
                      <div className="absolute -left-[21px] w-2.5 h-2.5 rounded-full bg-amber-500 outline outline-4 outline-background" />
                      <p className="text-sm font-medium">{inc.title || "Similar Incident"}</p>
                      <p className="text-xs text-muted-foreground line-clamp-1">{inc.root_cause || "Historical Match"}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      )}
      
      {/* Close the print padding wrapper */}
      </div>
    </div>
  );
}
