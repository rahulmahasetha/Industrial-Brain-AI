import os
import glob

pages_dir = 'frontend/src/pages'
tsx_files = glob.glob(os.path.join(pages_dir, '*.tsx'))

# Helper to find and replace standard page headers
def enhance_header(content, title_keywords):
    # This is a bit tricky, but most pages have:
    # <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
    #   <div>
    #     <h1 className="text-3xl font-bold tracking-tight">Title</h1>
    #     <p className="text-muted-foreground mt-1">Subtitle</p>
    #   </div>
    # ...
    
    # We will just replace common space-y-6 with space-y-8 for better breathing room
    content = content.replace('className="space-y-6"', 'className="space-y-8"')
    
    # Make headers larger and sleeker
    content = content.replace('text-3xl font-bold tracking-tight', 'text-3xl font-bold tracking-tight text-foreground')
    content = content.replace('text-muted-foreground mt-1', 'text-sm text-muted-foreground mt-1.5')
    
    return content

for path in tsx_files:
    # Skip AICopilot because we manually overhauled it earlier
    if 'AICopilot' in path:
        continue
        
    with open(path, 'r') as f:
        content = f.read()
        
    updated_content = enhance_header(content, [])
    
    # Fix any hardcoded borders on cards if they exist
    updated_content = updated_content.replace('border-2 border-primary/20', 'border border-border/40 shadow-sm')
    updated_content = updated_content.replace('bg-muted/50', 'bg-muted/30')
    
    with open(path, 'w') as f:
        f.write(updated_content)

print("Pages structurally enhanced.")
