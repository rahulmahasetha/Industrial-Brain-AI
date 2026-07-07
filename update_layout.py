import os

# --- MainLayout.tsx ---
main_layout = """import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function MainLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-background p-4 sm:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
"""
with open('frontend/src/components/layout/MainLayout.tsx', 'w') as f:
    f.write(main_layout)


# --- Header.tsx ---
header = """import { Bell, Search, User, Command } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between border-b border-border/40 bg-background/70 px-6 backdrop-blur-xl transition-all">
      <div className="flex flex-1 items-center gap-4">
        <div className="relative w-full max-w-md group">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground transition-colors group-focus-within:text-primary" />
          <Input
            type="search"
            placeholder="Search assets, documents, incidents..."
            className="w-full bg-muted/30 pl-10 pr-12 h-9 border-transparent transition-all focus-visible:bg-background focus-visible:ring-1 focus-visible:ring-primary/30 rounded-full text-sm"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-[10px] text-muted-foreground font-medium pointer-events-none">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="relative h-9 w-9 rounded-full text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-background"></span>
        </Button>
        <div className="h-6 w-[1px] bg-border mx-2"></div>
        <button className="flex items-center gap-3 rounded-full py-1 pl-1 pr-3 hover:bg-muted/50 transition-colors">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary border border-primary/20">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden md:flex flex-col text-left">
            <span className="text-[13px] font-semibold leading-none text-foreground">Rahul M.</span>
            <span className="text-[11px] text-muted-foreground mt-0.5">Lead Engineer</span>
          </div>
        </button>
      </div>
    </header>
  );
}
"""
with open('frontend/src/components/layout/Header.tsx', 'w') as f:
    f.write(header)


# --- Sidebar.tsx ---
sidebar = """import { NavLink } from 'react-router-dom';
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
"""
with open('frontend/src/components/layout/Sidebar.tsx', 'w') as f:
    f.write(sidebar)

print("Layout updated.")
