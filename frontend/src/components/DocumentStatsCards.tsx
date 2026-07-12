import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { FolderGit } from 'lucide-react';

interface CategoryCount {
  name: string;
  count: number;
  icon: string;
  description: string;
}

interface DocumentStatsCardsProps {
  refreshTrigger?: number; // External trigger to refresh stats
}

const CATEGORY_THEMES: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  "Inspection Records": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-100", glow: "hover:shadow-emerald-500/10 hover:border-emerald-300" },
  "Safety & Incidents": { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-100", glow: "hover:shadow-amber-500/10 hover:border-amber-300" },
  "QA Report": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-100", glow: "hover:shadow-blue-500/10 hover:border-blue-300" },
  "Root Cause Analysis": { bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-100", glow: "hover:shadow-cyan-500/10 hover:border-cyan-300" },
  "Standard Operating Procedures": { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-100", glow: "hover:shadow-indigo-500/10 hover:border-indigo-300" },
  "Compliance Certificate": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-100", glow: "hover:shadow-purple-500/10 hover:border-purple-300" },
  "Equipment Manuals": { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-100", glow: "hover:shadow-sky-500/10 hover:border-sky-300" },
  "Document": { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-200", glow: "hover:shadow-slate-500/10 hover:border-slate-300" },
  "Maintenance Records": { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-100", glow: "hover:shadow-teal-500/10 hover:border-teal-300" },
  "Maintenance": { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-100", glow: "hover:shadow-teal-500/10 hover:border-teal-300" },
};

const DEFAULT_THEME = { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200", glow: "hover:shadow-indigo-500/10 hover:border-indigo-300" };

export function DocumentStatsCards({ refreshTrigger = 0 }: DocumentStatsCardsProps) {
  const [stats, setStats] = useState<CategoryCount[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data: CategoryCount[] = await apiClient.get('/documents/stats/category-counts');
      setStats(data);
      
      // Calculate total
      const total = data.reduce((sum, item) => sum + item.count, 0);
      setTotalDocuments(total);
    } catch (err) {
      console.error('Failed to fetch document statistics:', err);
      setError('Failed to load statistics');
      setStats([]);
      setTotalDocuments(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Poll every 5 seconds to update stats in real-time
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  if (isLoading && stats.length === 0) {
    return (
      <div className="space-y-4">
        {/* Total loading skeleton */}
        <div className="h-28 bg-slate-900/50 border border-slate-800 rounded-lg animate-pulse" />
        
        {/* Grid loading skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-900/50 border border-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Total Documents Card - Premium Light Layout */}
      <div className="relative overflow-hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="absolute right-0 top-0 w-64 h-64 bg-indigo-50 rounded-full blur-3xl -z-10 translate-x-1/2 -translate-y-1/2 pointer-events-none" />
        
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm">
              <FolderGit className="w-7 h-7" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Indexed Knowledge</p>
              <h2 className="text-4xl font-extrabold text-slate-900 tracking-tight mt-1">{totalDocuments}</h2>
              <p className="text-sm text-slate-500 mt-1">Total ingested files in PostgreSQL database</p>
            </div>
          </div>
          <div className="flex items-center gap-6 bg-slate-50 border border-slate-200 rounded-xl px-6 py-4 shadow-sm shrink-0">
            <div className="text-center">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Categories</p>
              <p className="text-2xl font-bold text-slate-800">{stats.length}</p>
            </div>
            <div className="h-10 w-px bg-slate-200" />
            <div className="text-center">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Status</p>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
                Connected
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Statistics Grid - Clean Light Mode */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((stat) => {
          const theme = CATEGORY_THEMES[stat.name] || DEFAULT_THEME;
          return (
            <div 
              key={stat.name}
              className={`group bg-white border border-slate-200 rounded-xl p-5 transition-all duration-300 hover:-translate-y-1 shadow-sm ${theme.glow}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl border shadow-sm ${theme.bg} ${theme.border} group-hover:scale-110 transition-transform duration-300`}>
                  {stat.icon}
                </div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Count</span>
              </div>
              
              <h3 className="font-semibold text-xs text-slate-600 mb-1 group-hover:text-slate-900 line-clamp-2 tracking-wide transition-colors">
                {stat.name}
              </h3>
              
              <p className={`text-2xl font-extrabold ${theme.text}`}>
                {stat.count}
              </p>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="bg-red-950/20 border border-red-500/20 rounded-lg p-3 text-xs text-red-400">
          {error}
        </div>
      )}

      {stats.length === 0 && !isLoading && (
        <div className="text-center py-8 bg-slate-900/20 border border-slate-800 rounded-xl">
          <p className="text-sm text-slate-500">No documents yet. Start by uploading documents above.</p>
        </div>
      )}
    </div>
  );
}

export default DocumentStatsCards;
