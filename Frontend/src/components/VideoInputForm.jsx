import { useState } from 'react'
import { motion } from 'framer-motion'
import { FiYoutube, FiInstagram, FiArrowRight, FiCheckCircle } from 'react-icons/fi'

const VideoInputForm = ({ onSubmit, loading }) => {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [instagramUrl, setInstagramUrl] = useState('')
  const [youtubeValid, setYoutubeValid] = useState(false)
  const [instagramValid, setInstagramValid] = useState(false)

  const validateYoutube = (url) => {
    const patterns = [
      /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/,
      /^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/([\w-]+)/
    ]
    const isValid = patterns.some(pattern => pattern.test(url))
    setYoutubeValid(isValid)
    return isValid
  }

  const validateInstagram = (url) => {
    const patterns = [
      /^(https?:\/\/)?(www\.)?instagram\.com\/reel\/([\w-]+)/,
      /^(https?:\/\/)?(www\.)?instagram\.com\/p\/([\w-]+)/
    ]
    const isValid = patterns.some(pattern => pattern.test(url))
    setInstagramValid(isValid)
    return isValid
 }

  const handleYoutubeChange = (e) => {
    const url = e.target.value
    setYoutubeUrl(url)
    if (url) validateYoutube(url)
    else setYoutubeValid(false)
  }

  const handleInstagramChange = (e) => {
    const url = e.target.value
    setInstagramUrl(url)
    if (url) validateInstagram(url)
    else setInstagramValid(false)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (youtubeUrl && instagramUrl && youtubeValid && instagramValid) {
      onSubmit(youtubeUrl, instagramUrl)
    }
  }

  const isFormValid = youtubeValid && instagramValid && !loading

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl shadow-xl overflow-hidden"
    >
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <h2 className="text-xl font-semibold text-white">Compare Videos</h2>
        <p className="text-blue-100 text-sm mt-1">Enter YouTube and Instagram Reel URLs for AI analysis</p>
      </div>
      
      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* YouTube Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <FiYoutube className="w-5 h-5 text-red-500" />
            YouTube Video URL
          </label>
          <div className="relative">
            <input
              type="url"
              value={youtubeUrl}
              onChange={handleYoutubeChange}
              placeholder="https://youtube.com/watch?v=... or https://youtu.be/..."
              className={`w-full px-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition pr-12 ${
                youtubeValid ? 'border-green-500 bg-green-50' : youtubeUrl ? 'border-red-500 bg-red-50' : 'border-gray-200'
              }`}
              required
            />
            {youtubeValid && (
              <FiCheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500 w-5 h-5" />
            )}
          </div>
          {youtubeUrl && !youtubeValid && (
            <p className="text-xs text-red-500 mt-1">Please enter a valid YouTube URL</p>
          )}
        </div>
        
        {/* Instagram Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <FiInstagram className="w-5 h-5 text-pink-500" />
            Instagram Reel URL
          </label>
          <div className="relative">
            <input
              type="url"
              value={instagramUrl}
              onChange={handleInstagramChange}
              placeholder="https://instagram.com/reel/... or https://instagram.com/p/..."
              className={`w-full px-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition pr-12 ${
                instagramValid ? 'border-green-500 bg-green-50' : instagramUrl ? 'border-red-500 bg-red-50' : 'border-gray-200'
              }`}
              required
            />
            {instagramValid && (
              <FiCheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500 w-5 h-5" />
            )}
          </div>
          {instagramUrl && !instagramValid && (
            <p className="text-xs text-red-500 mt-1">Please enter a valid Instagram Reel URL</p>
          )}
        </div>
        
        {/* Submit Button */}
        <button
          type="submit"
          disabled={!isFormValid}
          className={`w-full py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all transform ${
            isFormValid
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 hover:scale-105 shadow-lg'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing...
            </>
          ) : (
            <>
              Analyze Videos
              <FiArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
        
        {/* Info Note */}
        <div className="text-xs text-gray-500 text-center bg-gray-50 p-3 rounded-lg">
          <p>🔍 Instagram data availability may vary. The system uses multiple fallback methods.</p>
          <p className="mt-1">💡 For best results, use public videos with available transcripts.</p>
        </div>
      </form>
    </motion.div>
  )
}

export default VideoInputForm