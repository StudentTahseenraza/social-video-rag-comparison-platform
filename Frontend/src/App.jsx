import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster, toast } from 'react-hot-toast'
import VideoInputForm from './components/VideoInputForm'
import VideoCard from './components/VideoCard'
import ChatWindow from './components/ChatWindow'
import LoadingModal from './components/LoadingModal'
import Header from './components/Header'
import MetricsPanel from './components/MetricsPanel'
import './App.css'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [videoA, setVideoA] = useState(null)
  const [videoB, setVideoB] = useState(null)
  const [engagementA, setEngagementA] = useState(null)
  const [engagementB, setEngagementB] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState('')
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [error, setError] = useState(null)

  const handleProcessVideos = async (youtubeUrl, instagramUrl) => {
    setLoading(true)
    setError(null)
    setLoadingProgress(0)
    
    const steps = [
      { step: 'Extracting YouTube metadata...', progress: 10 },
      { step: 'Fetching YouTube transcript...', progress: 25 },
      { step: 'Processing Instagram reel...', progress: 40 },
      { step: 'Generating transcript from audio...', progress: 60 },
      { step: 'Calculating engagement rates...', progress: 75 },
      { step: 'Creating embeddings & storing in vector DB...', progress: 90 },
      { step: 'Initializing chat session...', progress: 100 }
    ]
    
    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        setLoadingStep(steps[stepIndex].step)
        setLoadingProgress(steps[stepIndex].progress)
        stepIndex++
      }
    }, 2000)
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/process-videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: youtubeUrl, instagram_url: instagramUrl })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to process videos')
      }
      
      const data = await response.json()
      setSessionId(data.session_id)
      setVideoA(data.video_a)
      setVideoB(data.video_b)
      setEngagementA(data.engagement_a)
      setEngagementB(data.engagement_b)
      
      toast.success('Videos processed successfully!', {
        duration: 4000,
        icon: '🎉',
        style: { background: '#10B981', color: 'white' }
      })
      
    } catch (err) {
      console.error('Error:', err)
      setError(err.message)
      toast.error(err.message, {
        duration: 5000,
        icon: '❌',
        style: { background: '#EF4444', color: 'white' }
      })
    } finally {
      clearInterval(interval)
      setLoading(false)
      setLoadingStep('')
      setLoadingProgress(0)
    }
  }

  const resetApp = () => {
    setSessionId(null)
    setVideoA(null)
    setVideoB(null)
    setEngagementA(null)
    setEngagementB(null)
    setError(null)
    toast('Ready for new comparison!', { icon: '🔄' })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <Toaster position="top-right" />
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {!sessionId ? (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
            >
              <VideoInputForm onSubmit={handleProcessVideos} loading={loading} />
              
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700"
                >
                  <div className="flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={resetApp} className="text-red-600 hover:text-red-800 font-medium">
                      Try Again
                    </button>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {/* Header with Actions */}
              <div className="mb-6 flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Video Analysis Dashboard</h2>
                  <p className="text-gray-600 mt-1">Comparing performance metrics and engagement</p>
                </div>
                <button
                  onClick={resetApp}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  New Comparison
                </button>
              </div>
              
              {/* Metrics Panel - Side by Side Comparison */}
              <MetricsPanel 
                videoA={videoA} 
                videoB={videoB} 
                engagementA={engagementA} 
                engagementB={engagementB} 
              />
              
              {/* Side by Side Video Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <VideoCard video={videoA} engagement={engagementA} label="Video A" />
                <VideoCard video={videoB} engagement={engagementB} label="Video B" />
              </div>
              
              {/* Chat Interface */}
              <ChatWindow 
                sessionId={sessionId}
                videoAId={videoA.video_id}
                videoBId={videoB.video_id}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      
      <LoadingModal isOpen={loading} step={loadingStep} progress={loadingProgress} />
    </div>
  )
}

export default App