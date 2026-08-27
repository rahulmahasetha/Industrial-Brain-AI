import re

with open('frontend/src/pages/AICopilot.tsx', 'r') as f:
    content = f.read()

# We want to replace sendMessage to not use streaming.
old_send_message = """
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
            const lines = chunk.split('\\n');
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
"""

new_send_message = """
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
      const response = await apiClient.post('/chat', { message: text, session_id: activeSessionId, history: [] });
      setMessages(prev => [...prev, response]);
      
      // Auto-rename chat based on first query
      if (messages.length <= 1) {
          const newTitle = (response.intent || text).substring(0, 30);
          handleRenameSession(activeSessionId as number, newTitle);
      }
    } catch (error) {
      console.error('Chat error', error);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error communicating with the backend.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
"""

# replace carefully
start_idx = content.find('const sendMessage = async (text: string) => {')
if start_idx != -1:
    end_idx = content.find('const suggestions = useMemo(() => [', start_idx)
    
    if end_idx != -1:
        new_content = content[:start_idx] + new_send_message.strip() + '\n\n  ' + content[end_idx:]
        with open('frontend/src/pages/AICopilot.tsx', 'w') as f:
            f.write(new_content)
        print("Success")
    else:
        print("Could not find end of sendMessage")
else:
    print("Could not find start of sendMessage")

