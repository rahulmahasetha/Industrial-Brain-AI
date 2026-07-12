import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Activity, AlertTriangle, CheckCircle2, FileText, Wrench,
  Brain, ArrowUpRight, Sparkles, Database, Server, RefreshCw, Cpu, 
  Clock, Layers, Award, HelpCircle, Info
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ReactNode;
  iconBg: string;
  accentClass: string;
  progress?: number;
}

function StatCard({ title, value, subtitle, icon, iconBg, accentClass, progress }: StatCardProps) {
  return (
    <Card className={`dashboard-stat card-hover gap-0 py-0 bg-white/90 border border-slate-200/80 shadow-sm ${accentClass}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={`h-8 w-8 flex items-center justify-center rounded-md ${iconBg}`}>
            {icon}
          </div>
          <ArrowUpRight className="h-3.5 w-3.5 text-slate-300" />
        </div>
        <div className="text-xl font-bold leading-tight text-slate-900">{value || '—'}</div>
        <div className="text-[12px] font-medium text-slate-500 mt-0.5">{title}</div>
        <div className="text-[10px] leading-4 text-slate-400 mt-0.5">{subtitle}</div>
        {progress !== undefined && (
          <Progress value={progress} className="h-1 mt-2.5 bg-slate-100 [&>div]:bg-blue-500" />
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [systemMetrics, setSystemMetrics] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    setRefreshing(true);
    try {
      const s = await apiClient.get('/dashboard/stats');
      setStats(s);
      const m = await apiClient.get('/dashboard/system-metrics');
      setSystemMetrics(m);
      const i = await apiClient.get('/dashboard/incidents/recent');
      setIncidents((i || []).slice(0, 5));
      const c = await apiClient.get('/documents/stats/category-counts');
      setCategories(c || []);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const severityConfig: Record<string, { badge: string; icon: React.ReactNode }> = {
    critical: { badge: 'badge-error', icon: <AlertTriangle className="h-3.5 w-3.5" /> },
    high:     { badge: 'badge-error', icon: <AlertTriangle className="h-3.5 w-3.5" /> },
    medium:   { badge: 'badge-warning', icon: <Wrench className="h-3.5 w-3.5" /> },
    low:      { badge: 'badge-success', icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
  };

  const renderValue = (val: any, suffix: string = '') => {
    if (val === null || val === undefined) return <span className="text-slate-400 font-medium italic">Not Available</span>;
    return <span className="font-bold text-slate-800">{val}{suffix}</span>;
  };

  const data = systemMetrics;
  const maxIngestionCount = data ? Math.max(...data.charts.ingestion_trend.map((d: any) => d.count), 1) : 1;
  const maxResponseDuration = data ? Math.max(...data.charts.response_trend.map((d: any) => d.duration), 0.1) : 0.1;

  return (
    <div className="dashboard-shell space-y-8">
      {/* Page Header */}
      <section className="dashboard-hero relative overflow-hidden rounded-2xl px-5 py-6 sm:px-7 sm:py-7">
        <div className="dashboard-orb dashboard-orb-one" />
        <div className="dashboard-orb dashboard-orb-two" />
        <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-blue-100">
              <Sparkles className="h-3.5 w-3.5 text-cyan-300" /> INDUSTRIAL INTELLIGENCE
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Plant operations, at a glance.</h1>
            <p className="mt-2 text-sm leading-6 text-slate-300">Monitor equipment health, operational risk, and the knowledge system that supports your team.</p>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:gap-3 xl:min-w-[150px]">
            <div className="hero-mini-stat"><span>Brain score</span><strong>{stats?.brain_score ?? '—'}<small>/100</small></strong></div>
          </div>
        </div>
        <div className="relative mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-4">
          <span className="inline-flex items-center gap-2 text-xs text-emerald-200"><span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_4px_rgba(74,222,128,.12)]" /> Live operational view</span>
          <div className="flex items-center gap-2">
            <button onClick={() => navigate('/copilot')} className="hero-action-primary">Ask Industrial Brain <Brain className="h-3.5 w-3.5" /></button>
          </div>
        </div>
      </section>

      {/* Primary KPI Cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Brain Score"
          value={stats ? `${stats.brain_score}/100` : '—'}
          subtitle="Avg. asset health index"
          icon={<Brain className="h-4 w-4 text-blue-600" />}
          iconBg="bg-blue-50"
          accentClass="stat-card-blue"
          progress={stats?.brain_score}
        />
        <StatCard
          title="System Confidence"
          value={systemMetrics?.quality?.answer_confidence ? `${systemMetrics.quality.answer_confidence}%` : '—'}
          subtitle="Avg. AI response confidence"
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-600" />}
          iconBg="bg-emerald-50"
          accentClass="stat-card-green"
          progress={systemMetrics?.quality?.answer_confidence}
        />
        <StatCard
          title="Knowledge Base"
          value={stats?.knowledge_documents ?? '—'}
          subtitle={stats ? `${stats.indexed_documents} indexed • ${stats.pending_documents} pending` : 'Loading...'}
          icon={<FileText className="h-4 w-4 text-indigo-600" />}
          iconBg="bg-indigo-50"
          accentClass="stat-card-purple"
        />
      </div>

      {/* Incidents & Categories */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="dashboard-panel bg-white border border-slate-200 shadow-sm">
          <CardHeader className="px-5 pt-5 pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-[15px] font-semibold text-slate-800">Recent Incidents</CardTitle>
                <p className="text-[12px] text-slate-400 mt-0.5">Latest anomalies requiring attention</p>
              </div>
              <button onClick={() => navigate('/rca')} className="text-[12px] font-medium text-blue-600 hover:text-blue-700 transition-colors">Investigate →</button>
            </div>
          </CardHeader>
          <CardContent className="px-5 py-3 h-[250px] overflow-y-auto">
            {incidents.length === 0 && (
              <div className="py-6 text-center">
                <div className="skeleton h-4 w-full mb-2 mx-auto" />
                <div className="skeleton h-4 w-3/4 mx-auto" />
              </div>
            )}
            <div className="divide-y divide-slate-100">
              {incidents.map((incident: any) => {
                const sev = incident.severity?.toLowerCase() || 'low';
                const cfg = severityConfig[sev] || severityConfig.low;
                return (
                  <div key={incident.id} className="flex items-start gap-3 py-3">
                    <div className={`mt-0.5 h-6 w-6 flex items-center justify-center rounded-full ${
                      sev === 'high' || sev === 'critical' ? 'bg-red-50 text-red-500' :
                      sev === 'medium' ? 'bg-amber-50 text-amber-500' : 'bg-emerald-50 text-emerald-500'
                    }`}>
                      {cfg.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13.5px] font-medium text-slate-800 leading-snug truncate">{incident.title}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">{incident.asset_tag} • {incident.status}</p>
                    </div>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full shrink-0 ${cfg.badge}`}>
                      {incident.severity}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="dashboard-panel bg-white border border-slate-200 shadow-sm">
          <CardHeader className="px-5 pt-5 pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-[15px] font-semibold text-slate-800">Document Categories</CardTitle>
                <p className="text-[12px] text-slate-400 mt-0.5">Total Categories: {categories.length}</p>
              </div>
              <button onClick={() => navigate('/documents')} className="text-[12px] font-medium text-blue-600 hover:text-blue-700 transition-colors">View Hub →</button>
            </div>
          </CardHeader>
          <CardContent className="px-5 py-3 h-[250px] overflow-y-auto">
            {categories.length === 0 && (
              <div className="py-6 text-center">
                <div className="skeleton h-4 w-full mb-2 mx-auto" />
                <div className="skeleton h-4 w-3/4 mx-auto" />
              </div>
            )}
            <div className="divide-y divide-slate-100">
              {categories.map((category: any) => (
                <div key={category.name} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-8 w-8 flex items-center justify-center bg-slate-50 border border-slate-100 rounded-md shrink-0 text-lg">
                      {category.icon || '📄'}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13.5px] font-medium text-slate-800 truncate">{category.name}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5 truncate">{category.description}</p>
                    </div>
                  </div>
                  <span className="text-[13px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full shrink-0">
                    {category.count}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* --- SYSTEM METRICS OBSERVABILITY SECTION --- */}
      {data && (
        <div className="space-y-6 pt-6 border-t border-slate-200">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
                <Activity className="w-6 h-6 text-indigo-600" />
                System Metrics Observability
              </h2>
              <p className="text-slate-500 text-[13px] mt-1">Real-time performance instrumentation, infrastructure statuses, and AI quality logs.</p>
            </div>
            <button 
              onClick={fetchData}
              disabled={refreshing}
              className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh Metrics'}
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
              <Server className="w-4 h-4 text-indigo-500" />
              Infrastructure & Database Clusters
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(data.infrastructure).map(([name, status]: any) => (
                <div key={name} className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-150 rounded-xl">
                  <span className={`w-2.5 h-2.5 rounded-full ring-4 ${
                    status === 'online' ? 'bg-emerald-500 ring-emerald-500/10' : 'bg-rose-500 ring-rose-500/10'
                  }`} />
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide leading-none mb-1">
                      {name.replace('_', ' ')}
                    </p>
                    <p className="text-xs font-bold text-slate-700 capitalize leading-none">{status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { label: 'Total Documents', value: data.system_stats.total_documents, icon: FileText, color: 'text-indigo-600 bg-indigo-50 border-indigo-100', tooltip: 'Global quantity of distinct manual, SOP, compliance and reports files.' },
              { label: 'Pages Indexed', value: data.system_stats.total_pages, icon: Layers, color: 'text-sky-600 bg-sky-50 border-sky-100', tooltip: 'Accumulated pages parsed and indexed into search rows.' },
              { label: 'Semantic Chunks', value: data.system_stats.total_chunks, icon: Database, color: 'text-violet-600 bg-violet-50 border-violet-100', tooltip: 'Granular context paragraphs prepared for Vector search embedding.' },
              { label: 'Total Embeddings', value: data.system_stats.total_embeddings, icon: Cpu, color: 'text-purple-600 bg-purple-50 border-purple-100', tooltip: 'High-dimensional vector representations stored in ChromaDB.' },
              { label: 'Knowledge Nodes', value: data.system_stats.kg_nodes, icon: Activity, color: 'text-pink-600 bg-pink-50 border-pink-100', tooltip: 'Physical and virtual entities mapped into the Neo4j/Postgres Knowledge Graph.' },
              { label: 'Knowledge Edges', value: data.system_stats.kg_edges, icon: Clock, color: 'text-rose-600 bg-rose-50 border-rose-100', tooltip: 'Direct relational connections connecting entity nodes.' }
            ].map((c, i) => {
              const Icon = c.icon;
              return (
                <div key={i} className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow relative group">
                  <div className="flex justify-between items-start mb-2.5">
                    <div className={`p-2 rounded-lg border ${c.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute right-4 top-4 text-slate-400 cursor-help" title={c.tooltip}>
                      <HelpCircle className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">{c.label}</p>
                  <h2 className="text-xl font-extrabold text-slate-800">{c.value.toLocaleString()}</h2>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-indigo-500" />
                    AI / RAG Query Performance
                  </h3>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-50 border border-slate-150 py-0.5 px-2 rounded-full">
                    Average Latencies
                  </span>
                </div>
                <div className="space-y-4">
                  {[
                    { label: 'Intent Classification Time', value: data.performance.intent_classification_time, desc: 'Classifies engineering query intent.' },
                    { label: 'Metadata Lookup Time', value: data.performance.metadata_lookup_time, desc: 'Tier 1 exact metadata bypass query.' },
                    { label: 'TOC Retrieval Time', value: data.performance.toc_retrieval_time, desc: 'Section lookup from Table of Contents.' },
                    { label: 'SQL Search Time', value: data.performance.sql_search_time, desc: 'Keywords scanning across document pages.' },
                    { label: 'Vector Search Time', value: data.performance.vector_search_time, desc: 'ChromaDB vector embedding similarity match.' },
                    { label: 'Knowledge Graph Retrieval Time', value: data.performance.kg_retrieval_time, desc: 'Resolves relational links from graph.' },
                    { label: 'Reranking Time', value: data.performance.reranking_time, desc: 'Deduplicates and sorts candidate passages.' },
                    { label: 'LLM Generation Time', value: data.performance.llm_generation_time, desc: 'Synthesis output generation in primary LLM.' }
                  ].map((p, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs group relative">
                      <div>
                        <span className="font-semibold text-slate-700">{p.label}</span>
                        <p className="text-[10px] text-slate-400">{p.desc}</p>
                      </div>
                      <div className="font-mono text-slate-700 font-bold bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded">
                        {p.value !== null ? `${p.value.toFixed(3)}s` : 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-t border-slate-100 pt-5 mt-6 flex justify-between items-center bg-indigo-50/30 p-4 rounded-xl border border-indigo-50">
                <div>
                  <p className="text-[10px] font-bold text-indigo-500 uppercase tracking-wide">Total Query Execution Time</p>
                  <p className="text-xs text-slate-500">Retrieval + Synthesis aggregate</p>
                </div>
                <div className="font-mono text-lg font-extrabold text-indigo-700">
                  {data.performance.total_query_time !== null ? `${data.performance.total_query_time.toFixed(3)}s` : 'N/A'}
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-sky-500" />
                    Hybrid Search Retrieval Matches
                  </h3>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-50 border border-slate-150 py-0.5 px-2 rounded-full">
                    Per-Query Matches
                  </span>
                </div>
                <div className="space-y-4">
                  {[
                    { label: 'Metadata Matches', value: data.retrieval.metadata_matches, color: 'bg-indigo-500' },
                    { label: 'SQL Keyword Matches', value: data.retrieval.sql_matches, color: 'bg-sky-500' },
                    { label: 'TOC Section Matches', value: data.retrieval.toc_matches, color: 'bg-teal-500' },
                    { label: 'Vector Semantic Matches', value: data.retrieval.vector_matches, color: 'bg-violet-500' },
                    { label: 'Knowledge Graph Connections', value: data.retrieval.kg_matches, color: 'bg-pink-500' }
                  ].map((r, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold text-slate-700">
                        <span>{r.label}</span>
                        <span>{r.value !== null ? r.value.toFixed(1) : 'N/A'}</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${r.color} transition-all`} 
                          style={{ width: `${Math.min((r.value || 0) * 10, 100)}%` }} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-slate-150 pt-5 mt-6 text-center">
                <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-0.5">Retrieved</p>
                  <p className="text-sm font-extrabold text-slate-800">{renderValue(data.retrieval.final_retrieved_documents)}</p>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-0.5">Deduplicated</p>
                  <p className="text-sm font-extrabold text-slate-800">{renderValue(data.retrieval.deduplicated_documents)}</p>
                </div>
                <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-xl">
                  <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wide mb-0.5">Confidence</p>
                  <p className="text-sm font-extrabold text-emerald-700">{renderValue(data.retrieval.retrieval_confidence_score, '%')}</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-emerald-500" />
                    AI Quality & Ingestion
                  </h3>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-50 border border-slate-150 py-0.5 px-2 rounded-full">
                    Observability Logs
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Citation Coverage</p>
                    <h4 className="text-base font-extrabold text-slate-800">{renderValue(data.quality.citation_coverage, '%')}</h4>
                  </div>
                  <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Hallucination Risk</p>
                    <h4 className={`text-base font-extrabold ${
                      data.quality.hallucination_risk !== null && data.quality.hallucination_risk > 20 ? 'text-rose-600' : 'text-slate-800'
                    }`}>{renderValue(data.quality.hallucination_risk, '%')}</h4>
                  </div>
                  <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Cache Hit Rate</p>
                    <h4 className="text-base font-extrabold text-emerald-600">{renderValue(data.quality.cache_hit_rate, '%')}</h4>
                  </div>
                  <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-xl">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Cache Miss Rate</p>
                    <h4 className="text-base font-extrabold text-slate-800">{renderValue(data.quality.cache_miss_rate, '%')}</h4>
                  </div>
                </div>
                <div className="mt-5 space-y-3.5 border-t border-slate-100 pt-5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-700">Duplicate Documents Removed</span>
                    <span className="font-bold text-rose-600 bg-rose-50 border border-rose-100 px-1.5 py-0.5 rounded font-mono">
                      {data.ingestion.duplicate_documents_removed}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-700">Average Chunk Size</span>
                    <span className="font-bold text-slate-700 bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded font-mono">
                      {data.ingestion.average_chunk_size} chars
                    </span>
                  </div>
                </div>
              </div>
              <div className="bg-slate-50 border border-slate-150 p-4 rounded-xl flex items-start gap-2.5 mt-6">
                <Info className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <p className="text-[10px] text-slate-500 leading-normal">
                  Observability log counts track the overall query performance using Redis caches. Baselines are computed locally.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-1.5">
                <Database className="w-4 h-4 text-indigo-500" />
                Documents Ingested Over Time
              </h3>
              <div className="h-60 w-full flex items-end justify-between gap-2 px-4 border-b border-slate-200 pb-2">
                {data.charts.ingestion_trend.map((day: any, idx: number) => {
                  const heightPct = Math.max(5, (day.count / maxIngestionCount) * 100);
                  return (
                    <div key={idx} className="flex-1 h-full flex flex-col justify-end items-center gap-2 group relative">
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full mb-1.5 bg-slate-800 text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-10 shadow">
                        {day.count} documents
                      </div>
                      <div 
                        className="w-full bg-indigo-500 hover:bg-indigo-600 rounded-t-md transition-all duration-500"
                        style={{ height: `${heightPct}%` }}
                      />
                      <span className="text-[10px] font-bold text-slate-400 tracking-tight mt-1">{day.date}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-sky-500" />
                Query Response Time Trend (Last 10 Queries)
              </h3>
              <div className="h-60 w-full flex items-end justify-between gap-2 px-4 border-b border-slate-200 pb-2">
                {data.charts.response_trend.map((q: any, idx: number) => {
                  const heightPct = Math.max(5, (q.duration / maxResponseDuration) * 100);
                  return (
                    <div key={idx} className="flex-1 h-full flex flex-col justify-end items-center gap-2 group relative">
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full mb-1.5 bg-slate-800 text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-10 shadow">
                        {q.duration.toFixed(3)}s
                      </div>
                      <div 
                        className="w-full bg-sky-500 hover:bg-sky-600 rounded-t-md transition-all duration-500"
                        style={{ height: `${heightPct}%` }}
                      />
                      <span className="text-[10px] font-bold text-slate-400 tracking-tight mt-1">{q.query}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
