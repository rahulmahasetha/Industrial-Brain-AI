import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';

interface CategoryCount {
  name: string;
  count: number;
  icon: string;
  description: string;
}

interface DocumentStatsCardsProps {
  refreshTrigger?: number; // External trigger to refresh stats
}

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
        <div className="h-20 bg-muted rounded-lg animate-pulse" />
        
        {/* Grid loading skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Total Documents Card - Minimalist Design */}
      <div className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">Total Documents</p>
            <p className="text-4xl font-semibold text-slate-900 dark:text-slate-50">{totalDocuments}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">Across all categories</p>
          </div>
          <span className="text-5xl opacity-20">📄</span>
        </div>
      </div>

      {/* Category Statistics Grid - Clean & Professional */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <div 
            key={stat.name}
            className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg p-5 transition-all hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <span className="text-3xl">{stat.icon}</span>
            </div>
            
            <h3 className="font-medium text-sm text-slate-700 dark:text-slate-300 mb-1 line-clamp-2">
              {stat.name}
            </h3>
            
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
              {stat.count}
            </p>
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {stats.length === 0 && !isLoading && (
        <div className="text-center py-8 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg">
          <p className="text-sm text-slate-500 dark:text-slate-400">No documents yet. Start by uploading documents above.</p>
        </div>
      )}
    </div>
  );
}

export default DocumentStatsCards;
