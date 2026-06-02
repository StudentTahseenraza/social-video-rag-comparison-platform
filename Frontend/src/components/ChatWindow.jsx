import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FiSend, FiCopy, FiMessageSquare, FiTrendingUp, FiTarget, FiUser, FiZap } from 'react-icons/fi'
import ReactMarkdown from 'react-markdown'
import { toast } from 'react-hot-toast'

const ChatWindow = ({ sessionId, videoAId, videoBId }) => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [streamingCitations, setStreamingCitations] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard!', { icon: '📋', duration: 2000 })
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
      id: Date.now()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setStreamingMessage('')
    setStreamingCitations([])

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';


    try {
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
          video_a_id: videoAId,
          video_b_id: videoBId
        })
      });

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
                setStreamingCitations(citations)
              }
              if (parsed.thinking) {
                // Show thinking indicator
                setStreamingMessage(prev => prev + ' 🤔')
              }
              if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (e) {
              console.error(e);
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
        timestamp: new Date(),
        id: Date.now() + 1
      }])
      setStreamingMessage('')
      setStreamingCitations([])

    } catch (error) {
      console.error('Chat error:', error)
      toast.error(error.message)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${error.message}. Please try again.`,
        timestamp: new Date(),
        isError: true
      }])
    } finally {
      setLoading(false)
    }
  }

  const suggestedQuestions = [
    { text: "Why did Video A get more engagement?", icon: <FiTrendingUp /> },
    { text: "What's the engagement rate of each?", icon: <FiTarget /> },
    { text: "Who's the creator of Video B?", icon: <FiUser /> },
    { text: "Suggest improvements for B", icon: <FiZap /> }
  ]

  return (
    <div className="bg-white rounded-xl shadow-lg flex flex-col h-[650px] overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <FiMessageSquare className="w-5 h-5 text-blue-600" />
              Video Analysis Chat
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Ask questions comparing these two videos
            </p>
          </div>
          <div className="text-xs text-gray-500">
            {messages.length} messages
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gray-50">
        {messages.length === 0 && !streamingMessage && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
              <FiMessageSquare className="w-10 h-10 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Start the Conversation</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Ask about engagement rates, content strategies, or get AI-powered suggestions to improve your videos.
            </p>

            {/* Suggested Questions */}
            <div className="mt-6 grid grid-cols-2 gap-2 max-w-lg mx-auto">
              {suggestedQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q.text)}
                  className="text-left p-2 text-sm bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition flex items-center gap-2"
                >
                  <span className="text-blue-500">{q.icon}</span>
                  <span className="text-gray-700">{q.text}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div
              key={msg.id || idx}
              initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white'
                  : msg.isError
                    ? 'bg-red-50 border border-red-200 text-red-700'
                    : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
                  }`}
              >
                {msg.role === 'assistant' && !msg.isError && (
                  <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                    <span className="font-medium">🤖 AI Assistant</span>
                    <button
                      onClick={() => copyToClipboard(msg.content)}
                      className="hover:text-blue-600 transition"
                    >
                      <FiCopy className="w-3 h-3" />
                    </button>
                  </div>
                )}

                <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-500 mb-1">📚 Sources:</p>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((citation, i) => (
                        <span key={i} className="text-xs bg-gray-100 px-2 py-1 rounded-full">
                          {citation.source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Streaming Message */}
        {streamingMessage && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex justify-start"
          >
            <div className="bg-white border border-gray-200 rounded-2xl p-4 max-w-[80%] shadow-sm">
              <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                <span className="font-medium">🤖 AI Assistant</span>
                <span className="text-green-500 animate-pulse">● Typing</span>
              </div>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{streamingMessage}</ReactMarkdown>
              </div>
              {streamingCitations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-500">Loading sources...</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {loading && !streamingMessage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-white border border-gray-200 rounded-2xl p-4">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-5 border-t bg-white">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about these videos..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
          >
            <FiSend className="w-4 h-4" />
            Send
          </button>
        </div>

        <p className="text-xs text-gray-400 mt-3 text-center">
          💡 Try asking about engagement rates, hook comparisons, or improvement suggestions
        </p>
      </div>
    </div>
  )
}

export default ChatWindow