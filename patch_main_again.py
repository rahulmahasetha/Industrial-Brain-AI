import re

with open('frontend/src/components/layout/MainLayout.tsx', 'r') as f:
    content = f.read()

# Change main tag
old_main = '<main className={cn("flex-1 overflow-y-auto bg-slate-50/50 print:overflow-visible print:bg-white print:p-0", !isCopilot && "p-5 sm:p-7")}>'
new_main = '<main className={cn("flex-1 overflow-y-auto bg-slate-50/50 print:overflow-visible print:bg-white print:p-0", !isCopilot ? "p-5 sm:p-7" : "flex flex-col overflow-hidden")}>'
content = content.replace(old_main, new_main)

# Change div tag
old_div = '<div className={cn("mx-auto print:max-w-none print:w-full", !isCopilot ? "max-w-7xl" : "w-full h-full")}>'
new_div = '<div className={cn("mx-auto print:max-w-none print:w-full", !isCopilot ? "max-w-7xl" : "w-full flex-1 flex flex-col min-h-0")}>'
content = content.replace(old_div, new_div)

with open('frontend/src/components/layout/MainLayout.tsx', 'w') as f:
    f.write(content)

print("MainLayout patched again successfully.")
