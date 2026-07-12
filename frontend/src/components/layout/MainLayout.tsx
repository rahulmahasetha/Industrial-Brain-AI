import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export default function MainLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-white print:h-auto print:block print:overflow-visible">
      <div className="print:hidden h-full">
        <Sidebar />
      </div>
      <div className="flex flex-col flex-1 overflow-hidden print:block print:overflow-visible">
        <div className="print:hidden">
          <Header />
        </div>
        <main className="flex-1 overflow-y-auto bg-slate-50/50 p-5 sm:p-7 print:overflow-visible print:bg-white print:p-0">
          <div className="mx-auto max-w-7xl print:max-w-none print:w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
