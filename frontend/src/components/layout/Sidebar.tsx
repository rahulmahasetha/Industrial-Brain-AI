import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Network, Bot, Activity,
  Settings, Brain, Layers3, ChevronRight, UserCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import SettingsModal from './SettingsModal';
import { useUser } from '@/contexts/UserContext';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';

const overviewNav = [
  { name: 'Dashboard',       href: '/dashboard',  icon: LayoutDashboard, color: 'text-blue-600' },
  { name: 'Document Hub',    href: '/documents',  icon: FileText,         color: 'text-teal-600' },
  { name: 'Page Index',      href: '/page-index', icon: Layers3,          color: 'text-indigo-600' },
  { name: 'Knowledge Graph', href: '/graph',      icon: Network,          color: 'text-purple-600' },
  { name: 'AI Copilot',      href: '/copilot',    icon: Bot,              color: 'text-blue-600' },
];

const intelligenceNav = [
  { name: 'Root Cause Analysis', href: '/rca',         icon: Activity,   color: 'text-orange-600' },
];

function NavItem({ item }: { item: typeof overviewNav[0] }) {
  return (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        cn(
          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-medium transition-all duration-150 relative',
          isActive ? 'nav-active' : 'nav-inactive'
        )
      }
    >
      {({ isActive }) => (
        <>
          <span className={cn(
            'flex h-6 w-6 items-center justify-center rounded-md transition-colors',
            isActive ? 'bg-blue-100' : 'bg-slate-100 group-hover:bg-slate-200'
          )}>
            <item.icon className={cn('h-3.5 w-3.5', isActive ? 'text-blue-600' : item.color)} />
          </span>
          <span className="flex-1">{item.name}</span>
          {isActive && <ChevronRight className="h-3.5 w-3.5 text-blue-500 ml-auto" />}
        </>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { profile } = useUser();

  return (
    <>
      <div className="hidden md:flex h-full w-[240px] flex-col border-r border-slate-200 bg-white">
        {/* Logo */}
        <div className="flex h-[60px] shrink-0 items-center gap-2.5 px-5 border-b border-slate-100">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 shadow-sm">
            <Brain className="h-4.5 w-4.5 text-white" style={{ height: '18px', width: '18px' }} />
          </div>
          <div>
            <div className="text-[14px] font-bold text-slate-900 leading-none">Industrial Brain</div>
            <div className="text-[10px] text-slate-400 font-medium mt-0.5">AI Platform</div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          <div>
            <div className="section-header px-1 mb-2">Platform</div>
            <nav className="space-y-0.5">
              {overviewNav.map((item) => <NavItem key={item.href} item={item} />)}
            </nav>
          </div>

          <div>
            <div className="section-header px-1 mb-2">Intelligence</div>
            <nav className="space-y-0.5">
              {intelligenceNav.map((item) => <NavItem key={item.href} item={item} />)}
            </nav>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100">
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="flex w-full items-center justify-between gap-3 rounded-lg px-2 py-2 text-[13.5px] font-medium text-slate-700 hover:bg-slate-50 transition-all duration-150"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Avatar className="h-8 w-8 rounded-md bg-slate-100">
                {profile?.photo_url ? (
                  <AvatarImage src={profile.photo_url} alt={profile.name} className="object-cover" />
                ) : (
                  <AvatarFallback className="rounded-md bg-blue-50 text-blue-700 font-semibold">
                    {profile?.name?.charAt(0) || <UserCircle className="h-4 w-4" />}
                  </AvatarFallback>
                )}
              </Avatar>
              <div className="flex flex-col text-left truncate">
                <span className="font-semibold text-sm truncate">{profile?.name || 'User'}</span>
                <span className="text-[10px] text-slate-500 truncate">{profile?.role || 'Guest'}</span>
              </div>
            </div>
            <Settings className="h-4 w-4 text-slate-400 shrink-0" />
          </button>
        </div>
      </div>
      
      <SettingsModal 
        open={isSettingsOpen} 
        onOpenChange={setIsSettingsOpen} 
      />
    </>
  );
}
