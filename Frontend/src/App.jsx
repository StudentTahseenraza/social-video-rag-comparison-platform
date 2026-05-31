import { useState } from 'react'
import VideoInputForm from './components/VideoInputForm'
import VideoCard from './components/VideoCard'
import ChatWindow from './components/ChatWindow'
import './App.css'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [videoA, setVideoA] = useState(null)
  const [videoB, setVideoB] = useState(null)
  const [engagementA, setEngagementA] = useState(null)
  const [engagementB, setEngagementB] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleProcessVideos = async (youtubeUrl, instagramUrl) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/process-videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: youtubeUrl, instagram_url: instagramUrl })
      })
      
      if (!response.ok) throw new Error('Failed to process videos')
      
      const data = await response.json()
      setSessionId(data.session_id)
      setVideoA(data.video_a)
      setVideoB(data.video_b)
      setEngagementA(data.engagement_a)
      setEngagementB(data.engagement_b)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            RAG Video Chatbot
          </h1>
          <p className="text-gray-600 mt-2">
            Compare YouTube and Instagram videos with AI
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <VideoInputForm onSubmit={handleProcessVideos} loading={loading} />
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            Error: {error}
          </div>
        )}
        
        {(videoA || videoB) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            <VideoCard video={videoA} engagement={engagementA} label="Video A" />
            <VideoCard video={videoB} engagement={engagementB} label="Video B" />
          </div>
        )}
        
        {sessionId && videoA && videoB && (
          <div className="mt-8">
            <ChatWindow 
              sessionId={sessionId}
              videoAId={videoA.video_id}
              videoBId={videoB.video_id}
            />
          </div>
        )}
      </main>
    </div>
  )
}

export default App