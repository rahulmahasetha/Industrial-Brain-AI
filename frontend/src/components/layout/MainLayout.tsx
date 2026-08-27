import { Outlet, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export default function MainLayout() {
  const location = useLocation();
  const isCopilot = location.pathname.startsWith('/copilot');
  return (
    <div className="flex h-screen overflow-hidden bg-white print:h-auto print:block print:overflow-visible">
      <div className="print:hidden h-full">
        <Sidebar />
      </div>
      <div className="flex flex-col flex-1 overflow-hidden print:block print:overflow-visible">
        <div className="print:hidden">
          <Header />
        </div>
        <main className={cn("flex-1 overflow-y-auto bg-slate-50/50 print:overflow-visible print:bg-white print:p-0", !isCopilot ? "p-5 sm:p-7" : "flex flex-col overflow-hidden")}>
          <div className={cn("mx-auto print:max-w-none print:w-full", !isCopilot ? "max-w-7xl" : "w-full flex-1 flex flex-col min-h-0")}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
