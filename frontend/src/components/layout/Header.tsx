import { useState, useEffect, useRef } from 'react';
import { Bell, Search, Box, FileText, AlertTriangle, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api';
import { useNavigate } from 'react-router-dom';

export function Header() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await apiClient.get(`/search?q=${encodeURIComponent(query)}`);
        setResults(res || []);
      } catch (error) {
        console.error("Search failed", error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'asset': return <Box className="h-4 w-4 text-blue-500" />;
      case 'document': return <FileText className="h-4 w-4 text-emerald-500" />;
      case 'incident': return <AlertTriangle className="h-4 w-4 text-rose-500" />;
      default: return <Search className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <header className="sticky top-0 z-40 flex h-[60px] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 gap-4">
      {/* Search */}
      <div className="relative w-full max-w-sm group" ref={dropdownRef}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-blue-600" />
          <Input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => {
              if (query.trim()) setShowDropdown(true);
            }}
            placeholder="Search assets, documents, incidents..."
            className="w-full bg-slate-50 pl-9 pr-8 h-9 border-slate-200 text-sm rounded-lg transition-all focus-visible:bg-white focus-visible:ring-1 focus-visible:ring-blue-500/30 focus-visible:border-blue-300 placeholder:text-slate-400"
          />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400 animate-spin" />
          )}
        </div>

        {/* Dropdown Results */}
        {showDropdown && query.trim() && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg border border-slate-200 shadow-xl overflow-hidden z-50">
            {isSearching && results.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500">Searching database...</div>
            ) : results.length > 0 ? (
              <div className="max-h-80 overflow-y-auto">
                <div className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/80 sticky top-0 border-b border-slate-100">
                  Global Search Results
                </div>
                {results.map((r, i) => (
                  <button
                    key={`${r.result_type}-${r.id}-${i}`}
                    onClick={() => {
                      setShowDropdown(false);
                      navigate(r.link);
                    }}
                    className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-slate-50 border-b border-slate-50 last:border-0 transition-colors"
                  >
                    <div className="mt-0.5 p-1.5 rounded-md bg-slate-100">
                      {getIcon(r.result_type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-800 truncate">{r.title}</p>
                      <p className="text-xs text-slate-500 truncate mt-0.5">{r.subtitle}</p>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center">
                <p className="text-sm font-medium text-slate-800">No matches found</p>
                <p className="text-xs text-slate-500 mt-1">Try a different keyword</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3 shrink-0">
        {/* System status */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-semibold text-emerald-700">Operational</span>
        </div>

        {/* Divider */}
        <div className="h-5 w-px bg-slate-200" />

        {/* Notifications */}
        <button className="relative flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-blue-600 ring-1 ring-white" />
        </button>
      </div>
    </header>
  );
}
