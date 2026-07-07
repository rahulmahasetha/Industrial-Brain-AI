import re

with open('frontend/src/pages/AICopilot.tsx', 'r') as f:
    content = f.read()

start_marker = "  return (\n    <div className=\"flex h-[calc(100vh-8rem)] flex-col space-y-4\">"
end_marker = "    </div>\n  );\n}\n"

new_ui = """  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      {/* Scrollable Chat Canvas */}
      <ScrollArea className="flex-1">
        <div className="mx-auto w-full max-w-4xl space-y-8 p-4 sm:p-8">
          
          {/* ChatGPT-style Header (Only visible at top) */}
          {messages.length <= 1 && (
            <div className="mb-12 mt-10 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <BrainCircuit className="h-8 w-8" />
              </div>
              <h1 className="text-3xl font-semibold tracking-tight">AI Copilot</h1>
              <p className="mt-2 text-muted-foreground">Enterprise GraphRAG Assistant</p>
            </div>
          )}

          {/* Chat Messages */}
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            
            # Skip the initial greeting if it's the only message and we want a clean center, 
            # but we'll render it to be safe.
            if (!isUser && idx === 0 && messages.length === 1) return null;

            return (
              <div key={idx} className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
                <div className={cn('flex max-w-[85%] gap-4', isUser ? 'flex-row-reverse' : 'flex-row')}>
                  
                  {/* Avatar for AI only */}
                  {!isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-background shadow-sm">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div className="min-w-0">
                    {isUser ? (
                      <div className="rounded-3xl bg-secondary px-5 py-3.5 text-base text-foreground shadow-sm">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none pb-2">
                        <EnterpriseResponse msg={msg} />
                      </div>
                    )}
                    <div className={cn('mt-1.5 px-2 text-[11px] text-muted-foreground', isUser ? 'text-right' : 'text-left')}>
                      {msg.time}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex w-full justify-start">
              <div className="flex max-w-[85%] gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-background shadow-sm">
                  <Bot className="h-4 w-4 text-primary animate-pulse" />
                </div>
                <div className="flex items-center gap-2 rounded-2xl bg-muted/30 px-5 py-3 text-sm text-muted-foreground">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce" />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:-.3s]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:-.5s]" />
                  <span className="ml-2">Analyzing plant data...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={scrollRef} className="h-4" />
        </div>
      </ScrollArea>

      {/* Floating Input Area */}
      <div className="mx-auto w-full max-w-4xl px-4 pb-4">
        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="mb-4 flex flex-wrap justify-center gap-2">
            {suggestions.map((q) => (
              <Badge
                key={q}
                variant="outline"
                className="cursor-pointer rounded-full border-border/50 bg-background/50 px-3 py-1.5 text-sm font-normal text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                onClick={() => sendMessage(q)}
              >
                {q}
              </Badge>
            ))}
          </div>
        )}

        <div className="relative flex items-center rounded-3xl border border-border/60 bg-background/80 shadow-sm backdrop-blur-md transition-shadow focus-within:shadow-md focus-within:border-border">
          <Button variant="ghost" size="icon" className="ml-2 h-10 w-10 shrink-0 rounded-full text-muted-foreground hover:bg-muted/50 hover:text-foreground">
            <Paperclip className="h-5 w-5" />
          </Button>
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage(inputMessage)}
            placeholder="Ask AI Copilot..."
            className="flex-1 border-0 bg-transparent px-2 py-6 text-base shadow-none focus-visible:ring-0 placeholder:text-muted-foreground/70"
          />
          <Button 
            onClick={() => sendMessage(inputMessage)} 
            disabled={isLoading || !inputMessage.trim()}
            className="mr-2 h-10 w-10 shrink-0 rounded-full bg-primary transition-transform active:scale-95"
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-2 text-center text-[10px] text-muted-foreground">
          AI Copilot can make mistakes. Verify critical engineering decisions.
        </div>
      </div>
    </div>
  );
}
"""

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_ui + content[end_idx:]
    with open('frontend/src/pages/AICopilot.tsx', 'w') as f:
        f.write(new_content)
    print("UI successfully replaced.")
else:
    print("Could not find the return block to replace.")
