import { useState } from 'react'
import { motion } from 'framer-motion'
import { FiEye, FiHeart, FiMessageCircle, FiUser, FiHash, FiClock, FiCalendar } from 'react-icons/fi'
import { formatDistanceToNow } from 'date-fns'

const VideoCard = ({ video, engagement, label }) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  
  if (!video) return null

  const formatNumber = (num) => {
    if (!num) return 'N/A'
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getPlatformColor = () => {
    return video.platform === 'youtube' ? 'bg-red-500' : 'bg-gradient-to-r from-purple-500 to-pink-500'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      whileHover={{ y: -4 }}
      className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100 hover:shadow-xl transition-all duration-300"
    >
      {/* Header with Platform Badge */}
      <div className="relative">
        {video.thumbnail_url && (
          <>
            {!imageLoaded && (
              <div className="w-full h-48 bg-gradient-to-r from-gray-200 to-gray-300 animate-pulse" />
            )}
            <img 
              src={video.thumbnail_url} 
              alt={video.title}
              className={`w-full h-48 object-cover transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
              onLoad={() => setImageLoaded(true)}
            />
          </>
        )}
        
        {/* Platform Badge */}
        <div className={`absolute top-4 left-4 ${getPlatformColor()} text-white px-3 py-1 rounded-full text-xs font-semibold shadow-lg`}>
          {video.platform.toUpperCase()}
        </div>
        
        {/* Duration Badge */}
        {video.duration && (
          <div className="absolute bottom-4 right-4 bg-black/70 text-white px-2 py-1 rounded text-xs font-mono">
            {formatDuration(video.duration)}
          </div>
        )}
        
        {/* Video Label */}
        <div className={`absolute top-4 right-4 w-12 h-12 rounded-full ${label === 'Video A' ? 'bg-blue-500' : 'bg-purple-500'} text-white flex items-center justify-center font-bold text-xl shadow-lg`}>
          {label === 'Video A' ? 'A' : 'B'}
        </div>
      </div>
      
      {/* Content */}
      <div className="p-5">
        <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition">
          {video.title}
        </h3>
        
        {/* Creator */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <FiUser className="w-4 h-4" />
          <span>{video.creator}</span>
          {video.creator_followers && (
            <span className="text-xs text-gray-400">
              • {formatNumber(video.creator_followers)} followers
            </span>
          )}
        </div>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-3 mb-4 pb-4 border-b">
          <MetricCard 
            icon={<FiEye className="w-4 h-4" />}
            value={formatNumber(video.views)}
            label="Views"
            color="blue"
          />
          <MetricCard 
            icon={<FiHeart className="w-4 h-4" />}
            value={formatNumber(video.likes)}
            label="Likes"
            color="red"
          />
          <MetricCard 
            icon={<FiMessageCircle className="w-4 h-4" />}
            value={formatNumber(video.comments)}
            label="Comments"
            color="green"
          />
        </div>
        
        {/* Engagement Rate */}
        {engagement && (
          <motion.div 
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg"
          >
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">Engagement Rate</span>
              <span className="text-2xl font-bold text-blue-600">
                {engagement.engagement_rate ? `${engagement.engagement_rate.toFixed(2)}%` : 'N/A'}
              </span>
            </div>
            {engagement.message && (
              <p className="text-xs text-gray-500 mt-1">{engagement.message}</p>
            )}
          </motion.div>
        )}
        
        {/* Hashtags */}
        {video.hashtags && video.hashtags.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
              <FiHash className="w-3 h-3" />
              <span>Trending Topics</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {video.hashtags.slice(0, 5).map(tag => (
                <span key={tag} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full hover:bg-gray-200 transition">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* Metadata Footer */}
        <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t">
          <div className="flex items-center gap-1">
            <FiCalendar className="w-3 h-3" />
            <span>
              {video.upload_date 
                ? formatDistanceToNow(new Date(video.upload_date), { addSuffix: true })
                : 'Date unknown'}
            </span>
          </div>
          {video.duration && (
            <div className="flex items-center gap-1">
              <FiClock className="w-3 h-3" />
              <span>{formatDuration(video.duration)}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

const MetricCard = ({ icon, value, label, color }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-green-50 text-green-600'
  }
  
  return (
    <div className="text-center">
      <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${colors[color]} mb-1`}>
        {icon}
      </div>
      <div className="font-semibold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

export default VideoCard