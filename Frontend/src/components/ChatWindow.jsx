import { useState, useRef, useEffect } from 'react'

function ChatWindow({ sessionId, videoAId, videoBId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input, timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setStreamingMessage('')

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
          video_a_id: videoAId,
          video_b_id: videoBId
        })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let citations = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullResponse += parsed.content
                setStreamingMessage(fullResponse)
              }
              if (parsed.citations) {
                citations = parsed.citations
              }
              if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (e) {
                console.error(e)
              // Skip invalid JSON
            }
          }
        }
      }

      // Add assistant message to history
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: fullResponse,
        citations: citations,
        timestamp: new Date()
      }])
      setStreamingMessage('')
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md flex flex-col h-[600px]">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold">Chat with Videos</h2>
        <p className="text-sm text-gray-600">
          Ask questions comparing these two videos
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              
              {msg.citations?.length > 0 && (
                <div className="mt-2 text-xs opacity-75">
                  Sources: {msg.citations.map(c => c.source).join(', ')}
                </div>
              )}
              
              <div className="text-xs mt-1 opacity-50">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {streamingMessage && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 max-w-[70%]">
              <div className="whitespace-pre-wrap">{streamingMessage}</div>
              <div className="text-xs mt-1 text-gray-500">Streaming...</div>
            </div>
          </div>
        )}
        
        {loading && !streamingMessage && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about these videos..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            Send
          </button>
        </div>
        
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setInput("Why did Video A get more engagement than Video B?")}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
          >
            📊 Compare engagement
          </button>
          <button
            onClick={() => setInput("Compare the hooks in the first 5 seconds")}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
          >
            🎯 Compare hooks
          </button>
          <button
            onClick={() => setInput("Suggest improvements for B based on what worked in A")}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
          >
            💡 Suggest improvements
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatWindow