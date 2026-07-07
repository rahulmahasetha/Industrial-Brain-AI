import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Activity, AlertTriangle, CheckCircle2, FileText, Settings, ShieldCheck, Box, Layers3, Network } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { apiClient } from '@/lib/api';
import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [healthData, setHealthData] = useState<any[]>([]);

  useEffect(() => {
    apiClient.get('/dashboard/stats').then(setStats).catch(console.error);

    apiClient.get('/dashboard/incidents/recent').then((data: any[]) => {
      setIncidents(data.slice(0, 5));
    }).catch(console.error);

    apiClient.get('/assets/').then((data: any[]) => {
      // Critical assets: lowest health score
      const critical = data.filter((a: any) => a.health_score < 75).slice(0, 5);
      setAssets(critical);

      // Aggregate health by type
      const typeMap: Record<string, number[]> = {};
      data.forEach((a: any) => {
        const t = a.type || 'Other';
        if (!typeMap[t]) typeMap[t] = [];
        typeMap[t].push(a.health_score);
      });
      const hd = Object.entries(typeMap).slice(0, 6).map(([name, scores]) => ({
        name: name.slice(0, 12),
        health: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      }));
      setHealthData(hd);
    }).catch(console.error);
  }, []);

  // Generate failure probability trend from incidents count per month (mocked by severity pattern)
  const failureData = [
    { name: 'Jan', prob: 12 },
    { name: 'Feb', prob: 15 },
    { name: 'Mar', prob: 14 },
    { name: 'Apr', prob: 22 },
    { name: 'May', prob: 18 },
    { name: 'Jun', prob: stats ? Math.min(90, Math.max(10, 100 - (stats.brain_score || 75))) : 25 },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1.5">Platform overview and asset intelligence</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="px-3 py-1 text-sm bg-primary/10 text-primary border-primary/20">
            <Activity className="h-4 w-4 mr-2" />
            System Healthy
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">FreshFlow Brain Score</CardTitle>
            <BrainScoreIcon />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">{stats ? `${stats.brain_score}/100` : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Avg. asset health score</p>
            <Progress value={stats?.brain_score || 0} className="h-2 mt-3" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monitored Assets</CardTitle>
            <Box className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.monitored_assets : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">{stats ? `${stats.assets_requiring_attention} requiring attention` : 'Loading...'}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Knowledge Base</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.knowledge_documents : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">{stats ? `${stats.indexed_documents} indexed, ${stats.pending_documents} pending` : 'Documents & records indexed'}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Readiness</CardTitle>
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats ? `${stats.compliance_readiness}%` : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Based on compliance records</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Indexed Pages</CardTitle>
            <Layers3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.total_indexed_pages : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Page-level retrieval units</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Page Chunks</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.total_chunks : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Used for semantic ranking</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Graph Nodes</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.total_knowledge_graph_nodes : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Documents, pages, and assets</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Relationships</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.total_relationships : '-'}</div>
            <p className="text-xs text-sm text-muted-foreground mt-1.5">Knowledge graph links</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Failure Probability Forecast</CardTitle>
            <CardDescription>Predicted aggregate risk across critical equipment classes</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={failureData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="name" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="prob" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Asset Health by Type</CardTitle>
            <CardDescription>Average health score per equipment category</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={healthData} layout="vertical" margin={{ top: 5, right: 30, left: 50, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#333" />
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis dataKey="name" type="category" stroke="#888" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: '#1e293b' }}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                />
                <Bar dataKey="health" radius={[0, 4, 4, 0]}>
                  {healthData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.health < 70 ? '#f59e0b' : '#10b981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Incidents</CardTitle>
            <CardDescription>Latest anomalies requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {incidents.length === 0 && <p className="text-sm text-muted-foreground">Loading incidents...</p>}
              {incidents.map((incident: any) => (
                <div key={incident.id} className="flex items-start gap-4">
                  <div className={`mt-0.5 rounded-full p-1.5 ${
                    incident.severity === 'high' || incident.severity === 'critical' ? 'bg-destructive/20 text-destructive' :
                    incident.severity === 'medium' ? 'bg-amber-500/20 text-amber-500' :
                    'bg-emerald-500/20 text-emerald-500'
                  }`}>
                    {incident.severity === 'high' || incident.severity === 'critical' ? <AlertTriangle className="h-4 w-4" /> :
                     incident.severity === 'medium' ? <Settings className="h-4 w-4" /> :
                     <CheckCircle2 className="h-4 w-4" />}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">{incident.title}</p>
                    <p className="text-xs text-muted-foreground">{incident.asset_tag} • Status: {incident.status}</p>
                  </div>
                  <Badge variant="outline">{incident.severity}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Critical Assets Watchlist</CardTitle>
            <CardDescription>Equipment with health score below 75%</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {assets.length === 0 && <p className="text-sm text-muted-foreground">Loading assets...</p>}
              {assets.map((asset: any) => (
                <div key={asset.id} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">{asset.tag} - {asset.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Next Maintenance: <span className={asset.next_maintenance === 'Overdue' ? 'text-destructive' : ''}>{asset.next_maintenance}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className={`text-sm font-bold ${asset.health_score < 50 ? 'text-destructive' : 'text-amber-500'}`}>
                        {Math.round(asset.health_score)}%
                      </div>
                      <div className="text-[10px] text-muted-foreground uppercase">Health</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function BrainScoreIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/>
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>
    </svg>
  )
}
