import re

with open('frontend/src/components/layout/MainLayout.tsx', 'r') as f:
    content = f.read()

# Add useLocation
if "useLocation" not in content:
    content = content.replace("import { Outlet } from 'react-router-dom';", "import { Outlet, useLocation } from 'react-router-dom';\nimport { cn } from '@/lib/utils';")

# Add location hook
old_func = "export default function MainLayout() {"
new_func = "export default function MainLayout() {\n  const location = useLocation();\n  const isCopilot = location.pathname.startsWith('/copilot');"
if "const location = useLocation();" not in content:
    content = content.replace(old_func, new_func)

# Change main tag
old_main = '<main className="flex-1 overflow-y-auto bg-slate-50/50 p-5 sm:p-7 print:overflow-visible print:bg-white print:p-0">'
new_main = '<main className={cn("flex-1 overflow-y-auto bg-slate-50/50 print:overflow-visible print:bg-white print:p-0", !isCopilot && "p-5 sm:p-7")}>'
content = content.replace(old_main, new_main)

# Change div tag
old_div = '<div className="mx-auto max-w-7xl print:max-w-none print:w-full">'
new_div = '<div className={cn("mx-auto print:max-w-none print:w-full", !isCopilot ? "max-w-7xl" : "w-full h-full")}>'
content = content.replace(old_div, new_div)

with open('frontend/src/components/layout/MainLayout.tsx', 'w') as f:
    f.write(content)

print("MainLayout patched successfully.")
