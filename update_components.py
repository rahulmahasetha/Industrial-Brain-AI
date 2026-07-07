import re
import os

def update_file(path, replacements):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)

# Update Card
update_file('frontend/src/components/ui/card.tsx', [
    ('rounded-lg border bg-card text-card-foreground shadow-sm',
     'rounded-2xl border border-border/60 bg-card/80 backdrop-blur-md text-card-foreground shadow-sm transition-all duration-300 hover:shadow-md'),
    ('p-6 pt-0', 'p-6 pt-2'),
    ('p-6', 'p-6'),
    ('flex flex-col space-y-1.5 p-6', 'flex flex-col space-y-1.5 p-6 pb-4'),
])

# Update Button
update_file('frontend/src/components/ui/button.tsx', [
    ('rounded-md text-sm font-medium',
     'rounded-xl text-sm font-medium transition-all duration-200 active:scale-[0.98]'),
    ('h-10 px-4 py-2', 'h-10 px-5 py-2'),
    ('shadow hover:bg-primary/90', 'shadow-sm shadow-primary/20 hover:bg-primary/90'),
])

# Update Input
update_file('frontend/src/components/ui/input.tsx', [
    ('flex h-10 w-full rounded-md border border-input bg-background',
     'flex h-10 w-full rounded-xl border border-input/60 bg-background/50 shadow-sm transition-all'),
    ('focus-visible:ring-ring focus-visible:ring-offset-2',
     'focus-visible:ring-primary/30 focus-visible:border-primary/50 focus-visible:bg-background'),
])

# Update Table
update_file('frontend/src/components/ui/table.tsx', [
    ('hover:bg-muted/50 data-[state=selected]:bg-muted',
     'hover:bg-muted/40 data-[state=selected]:bg-muted/60 transition-colors duration-200'),
    ('border-b', 'border-b border-border/40'),
    ('text-muted-foreground', 'text-muted-foreground font-medium uppercase tracking-wider text-[11px]'),
])

# Update Badge
update_file('frontend/src/components/ui/badge.tsx', [
    ('rounded-full', 'rounded-lg'), # More modern linear-style badges
    ('border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
     'border-transparent bg-primary/10 text-primary hover:bg-primary/20'),
    ('border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
     'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80'),
    ('border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
     'border-transparent bg-destructive/10 text-destructive hover:bg-destructive/20'),
])

print("Global UI Components Updated.")
