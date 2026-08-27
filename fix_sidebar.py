import re

with open('frontend/src/pages/AICopilot.tsx', 'r') as f:
    content = f.read()

# 1. Update the sidebar layout to use fixed/z-50 on mobile and relative on desktop.
old_sidebar_container = """      {/* Sidebar for Chat History */}
      {sidebarOpen && (
        <div className="w-64 border-r border-border/50 bg-muted/10 hidden md:flex flex-col shrink-0 animate-in slide-in-from-left-4 duration-200">
          <div className="p-4 border-b border-border/50 flex items-center justify-between">"""

new_sidebar_container = """      {/* Sidebar for Chat History */}
      {sidebarOpen && (
        <>
        <div className="md:hidden fixed inset-0 z-40 bg-background/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
        <div className="w-64 border-r border-border/50 bg-muted/10 flex flex-col shrink-0 animate-in slide-in-from-left-4 duration-200 fixed inset-y-0 left-0 z-50 md:relative md:inset-auto h-[calc(100vh-5rem)] md:h-auto bg-background md:bg-muted/10">
          <div className="p-4 border-b border-border/50 flex items-center justify-between">"""

content = content.replace(old_sidebar_container, new_sidebar_container)

# 2. Update the click handler for selecting a session to auto-close on mobile.
old_click = "onClick={() => setCurrentSessionId(session.id)}"
new_click = "onClick={() => { setCurrentSessionId(session.id); if (window.innerWidth < 768) setSidebarOpen(false); }}"

content = content.replace(old_click, new_click)

# 3. Ensure the PanelLeftOpen toggle button in the header is visible on mobile too when sidebar is closed.
# Earlier I added hidden md:flex to it.
old_toggle_btn = """            {!sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} className="h-8 w-8 -ml-2 hidden md:flex text-muted-foreground hover:text-foreground">
                <PanelLeftOpen className="h-4 w-4" />
              </Button>
            )}"""

new_toggle_btn = """            {!sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} className="h-8 w-8 -ml-2 text-muted-foreground hover:text-foreground">
                <PanelLeftOpen className="h-4 w-4" />
              </Button>
            )}"""

content = content.replace(old_toggle_btn, new_toggle_btn)

# 4. We also need to close the Fragment `<>` we opened for the mobile overlay.
old_sidebar_end = """        </ScrollArea>
      </div>
      )}"""

new_sidebar_end = """        </ScrollArea>
      </div>
      </>
      )}"""

content = content.replace(old_sidebar_end, new_sidebar_end)

with open('frontend/src/pages/AICopilot.tsx', 'w') as f:
    f.write(content)

print("Sidebar responsiveness patched successfully.")
