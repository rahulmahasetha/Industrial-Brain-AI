import { useState, useEffect } from 'react';
import { 
  Lightbulb, AlertOctagon, TrendingUp, AlertTriangle, 
  Loader2, Activity, Settings, ArrowRight 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Warning {
  id: string;
  asset_tag: string;
  asset_name: string;
  risk_level: string;
  message: string;
  temperature: number;
  vibration: number;
}

interface Pattern {
  id: string;
  title: string;
  confidence: number;
  occurrences: number;
  affected_assets: string[];
  preventative_warning: string;
}

interface Stats {
  total_historical_incidents: number;
  critical_failures: number;
  chart_data: { name: string; incidents: number }[];
}

export default function FailureIntelligence() {
  const navigate = useNavigate();
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [warnRes, patRes, statRes] = await Promise.all([
        apiClient.get('/failure-intelligence/warnings'),
        apiClient.get('/failure-intelligence/patterns'),
        apiClient.get('/failure-intelligence/stats')
      ]);
      setWarnings(warnRes);
      setPatterns(patRes);
      setStats(statRes);
    } catch (err) {
      console.error("Failed to load failure intelligence data", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 text-amber-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 no-print">
        <div>
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
            <Lightbulb className="h-3.5 w-3.5" /> FAILURE INTELLIGENCE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">Systemic Pattern Discovery</h1>
          <p className="text-sm text-slate-500 mt-1.5">AI analysis of historical incidents to predict and prevent future failures.</p>
        </div>
      </div>

      {/* Active Warnings Feed */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <AlertOctagon className="w-4 h-4 text-red-500" /> Active Proactive Warnings
        </h2>
        {warnings.length === 0 ? (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-500">
            No active conditions currently match historical failure patterns.
          </div>
        ) : (
          warnings.map(warn => (
            <div key={warn.id} className="bg-red-50/50 border border-red-200 rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row gap-4 justify-between items-start">
              <div className="flex gap-3">
                <div className="mt-0.5"><AlertTriangle className="w-5 h-5 text-red-500" /></div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-red-900">{warn.asset_tag}</span>
                    <Badge variant="destructive" className="bg-red-500 hover:bg-red-600">{warn.risk_level} Risk Match</Badge>
                  </div>
                  <p className="text-sm text-red-800/90">{warn.message}</p>
                  <div className="flex gap-4 mt-2 text-xs font-medium text-red-700">
                    <span className="flex items-center gap-1"><Activity className="w-3.5 h-3.5"/> Temp: {warn.temperature}°C</span>
                    <span className="flex items-center gap-1"><Settings className="w-3.5 h-3.5"/> Vib: {warn.vibration}mm/s</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => navigate('/rca', { state: { assetTag: warn.asset_tag, description: warn.message, autoRun: true } })}
                className="text-xs font-semibold text-red-700 bg-red-100 hover:bg-red-200 px-3 py-1.5 rounded-md transition-colors whitespace-nowrap w-full sm:w-auto">
                Generate RCA Pre-Brief
              </button>
            </div>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Historical Chart */}
        <Card className="lg:col-span-1 border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-amber-500" /> Historical Clustering
            </CardTitle>
            <CardDescription>Incidents clustered by asset</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-3xl font-extrabold text-slate-900">{stats?.total_historical_incidents}</p>
                <p className="text-xs text-slate-500 font-medium">Total Historical Incidents</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-extrabold text-red-600">{stats?.critical_failures}</p>
                <p className="text-xs text-slate-500 font-medium">Critical Failures</p>
              </div>
            </div>
            
            <div className="h-48 w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.chart_data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                  <YAxis tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{fill: '#f1f5f9'}} contentStyle={{borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px'}} />
                  <Bar dataKey="incidents" radius={[4, 4, 0, 0]}>
                    {stats?.chart_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index < 2 ? '#ef4444' : '#f59e0b'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Pattern Feed */}
        <Card className="lg:col-span-2 border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">AI-Detected Systemic Patterns</CardTitle>
            <CardDescription>Recurring root causes extracted from database history</CardDescription>
          </CardHeader>
          <CardContent className="px-0 sm:px-6">
            <div className="space-y-0 divide-y divide-slate-100 border-t border-slate-100">
              {patterns.map(pattern => (
                <div key={pattern.id} className="py-4 px-4 sm:px-0 hover:bg-slate-50 transition-colors group">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-semibold text-slate-900">{pattern.title}</h3>
                    <Badge variant="outline" className={pattern.confidence > 80 ? "bg-amber-50 text-amber-700 border-amber-200" : ""}>
                      {pattern.confidence}% Confidence
                    </Badge>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-2 mt-2 mb-3">
                    <span className="text-xs font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {pattern.occurrences} Occurrences
                    </span>
                    <span className="text-xs text-slate-500">Across assets:</span>
                    <div className="flex flex-wrap gap-1">
                      {pattern.affected_assets.map(a => (
                        <span key={a} className="text-[10px] uppercase font-bold text-slate-400 border border-slate-200 px-1.5 py-0.5 rounded">{a}</span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-blue-50/50 border border-blue-100 p-3 rounded-lg mt-2">
                    <p className="text-xs text-blue-800 font-medium flex items-start gap-2">
                      <Lightbulb className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                      {pattern.preventative_warning}
                    </p>
                  </div>
                  
                  <div className="mt-3 text-right">
                    <button 
                      onClick={() => navigate('/documents', { state: { searchQuery: pattern.affected_assets[0] } })}
                      className="text-xs font-medium text-blue-600 hover:text-blue-800 inline-flex items-center transition-colors"
                    >
                      View underlying incident reports <ArrowRight className="w-3 h-3 ml-1 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  </div>
                </div>
              ))}
              
              {patterns.length === 0 && (
                <div className="py-8 text-center text-sm text-slate-500">
                  No systemic patterns detected in historical database.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
