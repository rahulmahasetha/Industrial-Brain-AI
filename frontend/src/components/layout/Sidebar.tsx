import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Network, Bot, Activity, ShieldCheck, UserCog, Box, Settings, Brain, Layers3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Document Hub', href: '/documents', icon: FileText },
  { name: 'Page Index', href: '/page-index', icon: Layers3 },
  { name: 'Knowledge Graph', href: '/graph', icon: Network },
  { name: 'AI Copilot', href: '/copilot', icon: Bot },
  { name: 'Asset Intelligence', href: '/assets', icon: Box },
  { name: 'Root Cause Analysis', href: '/rca', icon: Activity },
  { name: 'Compliance Center', href: '/compliance', icon: ShieldCheck },
  { name: 'Expert Knowledge', href: '/expert', icon: UserCog },
];

export function Sidebar() {
  return (
    <div className="flex h-full w-[260px] flex-col border-r border-border/40 bg-card/30 backdrop-blur-sm hidden md:flex">
      <div className="flex h-16 shrink-0 items-center gap-3 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
          <Brain className="h-5 w-5" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-foreground">FreshFlow Brain</span>
      </div>
      
      <div className="flex-1 overflow-y-auto px-4 py-4 custom-scrollbar">
        <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-3 px-2">Overview</div>
        <nav className="space-y-1 mb-8">
          {navigation.slice(0, 5).map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'group flex items-center rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={cn("mr-3 h-4 w-4 flex-shrink-0 transition-colors", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
                  {item.name}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-3 px-2">Intelligence</div>
        <nav className="space-y-1">
          {navigation.slice(5).map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'group flex items-center rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={cn("mr-3 h-4 w-4 flex-shrink-0 transition-colors", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
                  {item.name}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="p-4 mt-auto">
        <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-[13px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-all">
          <Settings className="h-4 w-4 flex-shrink-0" />
          Settings
        </button>
      </div>
    </div>
  );
}
