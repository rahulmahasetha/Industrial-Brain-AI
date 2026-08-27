import re

with open('frontend/src/pages/AICopilot.tsx', 'r') as f:
    content = f.read()

# We need to replace the entire `export default function AICopilot() { ... }` block.
# We will find the start of `export default function AICopilot()` and replace from there to the end.

start_idx = content.find('export default function AICopilot() {')
if start_idx == -1:
    print("Could not find AICopilot()")
    exit(1)

pre_content = content[:start_idx]

new_copilot = """export default function AICopilot() {
  const { profile } = useUser();
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [printMessageIndex, setPrintMessageIndex] = useState<number | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchSessions = async () => {
    try {
      const data = await apiClient.get('/chat/sessions');
      setSessions(data);
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].id);
      } else if (data.length === 0) {
        // Create initial session if none exist
        const newSession = await apiClient.post('/chat/sessions', { title: 'New Chat' });
        setSessions([newSession]);
        setCurrentSessionId(newSession.id);
      }
    } catch (e) {
      console.error('Failed to fetch sessions', e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const loadSessionHistory = async (sessionId: number) => {
    try {
      const history = await apiClient.get(`/chat/history?session_id=${sessionId}`);
      if (history && history.length > 0) {
        setMessages(history);
      } else {
        setMessages([
          {
            role: 'assistant',
            content: 'Hello! I am your FreshFlow Beverages Enterprise Intelligence Assistant. Ask me about equipment failures, maintenance risk, SOPs, inspections, food safety compliance, or expert recommendations.',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (currentSessionId) {
      loadSessionHistory(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  const handleNewChat = async () => {
    try {
      const newSession = await apiClient.post('/chat/sessions', { title: 'New Chat' });
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
    } catch (e) {
      console.error('Failed to create new chat', e);
    }
  };

  const handleRenameSession = async (id: number, newTitle: string) => {
    try {
      await apiClient.put(`/chat/sessions/${id}`, { title: newTitle });
      setSessions(prev => prev.map(s => s.id === id ? { ...s, title: newTitle } : s));
    } catch (e) {
      console.error('Failed to rename session', e);
    }
  };

  const handleDeleteSession = async (id: number) => {
    try {
      await apiClient.delete(`/chat/sessions/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) {
        setCurrentSessionId(null); // will trigger load first session next time or blank
        setMessages([]);
        fetchSessions();
      }
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  };

  const handleClearChat = async () => {
    if (currentSessionId) {
      try {
        await apiClient.delete(`/chat/sessions/${currentSessionId}`);
        handleNewChat(); // replace it
      } catch (error) {
        console.error('Failed to clear chat history:', error);
      }
    }
  };

  const handleCopy = (text: string, id: number) => {
    let copyText = text;
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed === 'object') {
        if (parsed.answer) copyText = parsed.answer;
        else copyText = JSON.stringify(parsed, null, 2);
      }
    } catch(e) {}
    
    navigator.clipboard.writeText(copyText);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1000);
  };

  const handleDelete = async (index: number) => {
    let deletedIds: (number | undefined)[] = [];
    
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages[index].role === 'user' && index + 1 < newMessages.length && newMessages[index + 1].role === 'assistant') {
        deletedIds = [newMessages[index].id, newMessages[index + 1].id];
        newMessages.splice(index, 2);
      } else {
        deletedIds = [newMessages[index].id];
        newMessages.splice(index, 1);
      }
      return newMessages;
    });

    for (const id of deletedIds) {
      if (id) {
        try {
          await apiClient.delete(`/chat/history/${id}`);
        } catch (error) {
          console.error('Failed to delete message from backend:', error);
        }
      }
    }
  };

  const handleRegenerate = async (index: number) => {
    if (index === 0 || messages[index - 1].role !== 'user') return;
    
    const userQuery = messages[index - 1].content;
    const msgToRegenerate = messages[index];
    setRegeneratingIndex(index);
    
    if (msgToRegenerate.id) {
      try {
        await apiClient.delete(`/chat/history/${msgToRegenerate.id}`);
      } catch (error) {
        console.error('Failed to delete old regenerated message from backend:', error);
      }
    }
    
    try {
      const response = await apiClient.post('/chat', { message: userQuery, session_id: currentSessionId, history: [] });
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[index] = response;
        return newMsgs;
      });
    } catch (error) {
      console.error('Regenerate error', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[index] = { role: 'assistant', content: 'Sorry, I encountered an error.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
        return newMsgs;
      });
    } finally {
      setRegeneratingIndex(null);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    let activeSessionId = currentSessionId;
    if (!activeSessionId) {
      const newSession = await apiClient.post('/chat/sessions', { title: text.substring(0, 30) });
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      activeSessionId = newSession.id;
    }

    const userMsg = {
      role: 'user',
      content: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Create a temporary bot message
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isStreaming: true
        }
      ]);

      const response = await fetch(`${API_ORIGIN}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: activeSessionId, history: [] })
      });

      if (!response.ok) throw new Error('Stream failed');
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let streamedContent = '';

      if (reader) {
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            
            // SSE parsing
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                  done = true;
                  break;
                }
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.content) {
                    streamedContent += parsed.content;
                    setMessages(prev => {
                      const newMsgs = [...prev];
                      const last = newMsgs[newMsgs.length - 1];
                      if (last.role === 'assistant') {
                        last.content = streamedContent;
                      }
                      return newMsgs;
                    });
                  } else if (parsed.response_type) {
                    // Replace the message with the final fully parsed object once done
                    setMessages(prev => {
                      const newMsgs = [...prev];
                      newMsgs[newMsgs.length - 1] = parsed;
                      return newMsgs;
                    });
                    
                    // Auto-rename chat based on first query
                    if (messages.length <= 1) {
                        const newTitle = (parsed.intent || text).substring(0, 30);
                        handleRenameSession(activeSessionId as number, newTitle);
                    }
                  }
                } catch (e) {
                  // Partial chunk or non-JSON
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        if (last.role === 'assistant') {
           last.content = 'Sorry, I encountered an error communicating with the backend.';
           last.isStreaming = false;
        }
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        if (last && last.role === 'assistant') {
           last.isStreaming = false;
        }
        return newMsgs;
      });
    }
  };

  const suggestions = useMemo(() => [
    'Why did Bottle Filling Machine FM101 stop?',
    'What is the predictive risk for Air Compressor AC101?',
    'Show incidents related to bottle jam failures',
    'Show startup SOP for Bottle Filling Machine FM101.',
  ], []);

  return (
    <div className="flex h-[calc(100vh-5rem)] bg-background">
      
      {/* Sidebar for Chat History */}
      <div className="w-64 border-r border-border/50 bg-muted/10 flex flex-col hidden md:flex shrink-0">
        <div className="p-4 border-b border-border/50">
          <Button onClick={handleNewChat} className="w-full justify-start gap-2" variant="outline">
            <Plus className="h-4 w-4" /> New Chat
          </Button>
        </div>
        <ScrollArea className="flex-1 p-2">
          <div className="space-y-1">
            {sessions.map(session => (
              <div 
                key={session.id} 
                className={cn(
                  "group flex items-center justify-between p-2 rounded-lg text-sm cursor-pointer hover:bg-muted/50 transition-colors",
                  currentSessionId === session.id ? "bg-muted font-medium" : "text-muted-foreground"
                )}
                onClick={() => setCurrentSessionId(session.id)}
              >
                <div className="flex flex-col min-w-0 overflow-hidden">
                  <span className="truncate">{session.title}</span>
                  <span className="text-[10px] text-muted-foreground/70">{new Date(session.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                   <button 
                     onClick={(e) => { 
                       e.stopPropagation(); 
                       const newName = prompt("Rename chat:", session.title); 
                       if (newName) handleRenameSession(session.id, newName); 
                     }}
                     className="p-1 hover:text-foreground text-muted-foreground rounded"
                   >
                     <Edit2 className="h-3.5 w-3.5" />
                   </button>
                   <button 
                     onClick={(e) => { 
                       e.stopPropagation(); 
                       if (confirm("Delete this chat?")) handleDeleteSession(session.id); 
                     }}
                     className="p-1 hover:text-red-500 text-muted-foreground rounded"
                   >
                     <Trash2 className="h-3.5 w-3.5" />
                   </button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex shrink-0 items-center justify-between border-b border-border/50 bg-background/80 px-6 py-2.5 backdrop-blur-sm print:hidden">
          <div className="flex items-center gap-2">
            <div className="md:hidden flex h-7 w-7 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <MessageSquarePlus className="h-4 w-4" onClick={handleNewChat} />
            </div>
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
              <BrainCircuit className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm font-semibold">AI Copilot</span>
            <Badge variant="outline" className="ml-1 rounded-full border-emerald-500/40 bg-emerald-500/10 text-[10px] text-emerald-500">Live</Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={handleClearChat} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-red-500">
              <Trash2 className="h-3.5 w-3.5" /> Clear Chat
            </Button>
            <Button variant="ghost" size="sm" onClick={() => { setPrintMessageIndex(null); setTimeout(() => window.print(), 100); }} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
              <Download className="h-3.5 w-3.5" /> Export PDF
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 print:hidden">
          <div className="mx-auto w-full max-w-4xl space-y-6 px-4 py-8">

            {/* Welcome Header */}
            {messages.length <= 1 && (
              <div className="mb-8 mt-6 text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-primary/5 ring-1 ring-primary/20 text-primary shadow-md">
                  <BrainCircuit className="h-7 w-7" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight">Industrial Brain AI Copilot</h1>
                <p className="mt-1.5 text-sm text-muted-foreground">Enterprise GraphRAG · Equipment, SOPs, incidents, and predictive risk</p>
              </div>
            )}

            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              if (!isUser && idx === 0 && messages.length === 1) return null;

              return (
                <div key={idx} className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
                  {isUser ? (
                    <div className="flex max-w-[85%] items-end gap-3 sm:max-w-[75%]">
                      <div className="flex flex-col items-end">
                        <div className="rounded-2xl rounded-tr-sm bg-primary px-5 py-3.5 text-[15px] leading-relaxed text-primary-foreground shadow-sm">
                          {msg.content}
                        </div>
                        <span className="mt-1.5 mr-1 text-[10px] text-muted-foreground/70">{msg.time}</span>
                      </div>
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full border border-primary/20 bg-primary/10 sm:h-9 sm:w-9">
                        {profile?.photo_url ? (
                          <img src={profile.photo_url} alt="User" className="h-full w-full object-cover" />
                        ) : (
                          <span className="text-xs font-semibold text-primary">{profile?.name?.charAt(0) || 'U'}</span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex w-full max-w-[95%] items-start gap-3 sm:max-w-[85%]">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 shadow-sm sm:h-9 sm:w-9">
                        <Bot className="h-4 w-4 text-primary sm:h-5 sm:w-5" />
                      </div>
                      <div className="flex flex-1 flex-col overflow-hidden">
                        <div className="rounded-2xl rounded-tl-sm border border-border/60 bg-card shadow-sm overflow-hidden">
                          {msg.isStreaming ? (
                            <div className="px-5 py-4 whitespace-pre-wrap leading-relaxed">
                               {msg.content}
                               <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-primary align-middle" />
                            </div>
                          ) : msg.response_type === 'root_cause_analysis' || msg.response_type === 'predictive_maintenance' ? (
                            <EnterpriseResponse msg={msg} onSendMessage={sendMessage} />
                          ) : (
                            <div className="px-1 py-1">
                               <MarkdownMessage content={msg.content} intent={msg.intent} equipment={msg.enterprise?.equipment} />
                            </div>
                          )}
                          
                          {!msg.isStreaming && regeneratingIndex !== idx && (
                            <div className="flex items-center justify-between border-t border-border/40 bg-muted/20 px-4 sm:px-6 py-2.5 text-[10px] text-muted-foreground">
                              <span>{msg.time}</span>
                              <div className="flex items-center gap-3.5">
                                <button onClick={() => handleCopy(msg.content, idx)} className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                                  {copiedId === idx ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                                  <span>{copiedId === idx ? 'Copied' : 'Copy'}</span>
                                </button>
                                {idx > 0 && (
                                  <button onClick={() => handleRegenerate(idx)} disabled={isLoading || regeneratingIndex !== null} className="flex items-center gap-1.5 hover:text-foreground transition-colors disabled:opacity-50">
                                    <RefreshCcw className="h-3.5 w-3.5" />
                                    <span>Regenerate</span>
                                  </button>
                                )}
                                <button onClick={() => { setPrintMessageIndex(idx); setTimeout(() => window.print(), 100); }} className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                                  <Download className="h-3.5 w-3.5" />
                                  <span>PDF</span>
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {isLoading && messages[messages.length-1]?.role !== 'assistant' && (
              <div className="flex w-full gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 shadow-sm">
                  <Bot className="h-4 w-4 text-primary animate-pulse" />
                </div>
                <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-border/60 bg-card px-5 py-3.5 shadow-sm">
                  <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce" />
                  <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.25s]" />
                  <div className="h-2 w-2 rounded-full bg-primary/70 animate-bounce [animation-delay:-.5s]" />
                  <span className="ml-2 text-xs text-muted-foreground">Analyzing plant data…</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} className="h-2" />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="shrink-0 border-t border-border/50 bg-background/90 px-4 pb-5 pt-3 print:hidden backdrop-blur-sm">
          <div className="mx-auto w-full max-w-4xl">
            {/* Quick Suggestions */}
            {messages.length <= 1 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {suggestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="rounded-full border border-border/60 bg-muted/40 px-3 py-1 text-xs text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
            
            <div className="relative flex items-end gap-2 rounded-2xl border border-border/60 bg-card p-1.5 shadow-sm focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center">
                <Sparkles className="h-5 w-5 text-primary/70" />
              </div>
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(inputMessage);
                  }
                }}
                placeholder="Ask about equipment health, downtime RCA, or standard operating procedures..."
                className="max-h-32 min-h-[44px] w-full resize-none bg-transparent py-2.5 text-[15px] placeholder:text-muted-foreground/60 focus:outline-none"
                rows={1}
                disabled={isLoading}
              />
              <div className="flex items-center gap-2 pr-1 pb-1">
                <Button
                  size="icon"
                  className={cn('h-9 w-9 rounded-xl transition-all', inputMessage.trim() ? 'bg-primary text-primary-foreground shadow-md hover:bg-primary/90' : 'bg-muted text-muted-foreground hover:bg-muted')}
                  onClick={() => sendMessage(inputMessage)}
                  disabled={!inputMessage.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="mt-2 text-center text-[10px] text-muted-foreground/70">
              Industrial Brain AI can make mistakes. Verify critical maintenance procedures.
            </div>
          </div>
        </div>
      </div>
      
      {/* Hidden Printable Report */}
      <div className="hidden print:block">
        {printMessageIndex !== null && messages[printMessageIndex] && (
          <PrintableReport message={messages[printMessageIndex]} />
        )}
      </div>
    </div>
  );
}
"""

with open('frontend/src/pages/AICopilot.tsx', 'w') as f:
    f.write(pre_content + new_copilot)

