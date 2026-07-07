import { Bell, Search, User, Command } from 'lucide-react';
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
