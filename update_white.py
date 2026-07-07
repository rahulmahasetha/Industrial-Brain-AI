with open('frontend/src/pages/AICopilot.tsx', 'r') as f:
    content = f.read()

# Replace the main container to enforce bg-white
old_main = '<div className="flex h-[calc(100vh-5rem)] flex-col">'
new_main = '<div className="flex h-[calc(100vh-5rem)] flex-col bg-white text-slate-900">'
content = content.replace(old_main, new_main)

# Replace the user bubble to be simple light gray
old_bubble = 'className="rounded-3xl bg-secondary px-5 py-3.5 text-base text-foreground shadow-sm"'
new_bubble = 'className="rounded-3xl bg-gray-100 px-5 py-3.5 text-base text-gray-900 shadow-sm"'
content = content.replace(old_bubble, new_bubble)

# Input container styling
old_input_container = 'className="relative flex items-center rounded-3xl border border-border/60 bg-background/80 shadow-sm backdrop-blur-md transition-shadow focus-within:shadow-md focus-within:border-border"'
new_input_container = 'className="relative flex items-center rounded-3xl border border-gray-200 bg-white shadow-sm transition-shadow focus-within:shadow-md focus-within:border-gray-300"'
content = content.replace(old_input_container, new_input_container)

# Input field styling
old_input = 'className="flex-1 border-0 bg-transparent px-2 py-6 text-base shadow-none focus-visible:ring-0 placeholder:text-muted-foreground/70"'
new_input = 'className="flex-1 border-0 bg-transparent px-2 py-6 text-base text-slate-900 shadow-none focus-visible:ring-0 placeholder:text-gray-400"'
content = content.replace(old_input, new_input)

# Avatar
old_bot = 'className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-background shadow-sm"'
new_bot = 'className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm"'
content = content.replace(old_bot, new_bot)

with open('frontend/src/pages/AICopilot.tsx', 'w') as f:
    f.write(content)
