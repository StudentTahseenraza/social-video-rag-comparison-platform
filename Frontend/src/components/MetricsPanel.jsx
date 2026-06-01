import { motion } from 'framer-motion'
import { FiEye, FiHeart, FiMessageCircle } from 'react-icons/fi'

const MetricsPanel = ({ videoA, videoB, engagementA, engagementB }) => {
  const formatNumber = (num) => {
    if (!num) return 'N/A'
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const getEngagementColor = (rate) => {
    if (!rate) return 'text-gray-400'
    if (rate > 10) return 'text-green-600'
    if (rate > 5) return 'text-blue-600'
    return 'text-yellow-600'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-gray-100"
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Performance Overview</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Video A Metrics */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-semibold text-blue-900">Video A (YouTube)</span>
            <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">
              {videoA?.creator || 'Unknown'}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <MetricItem icon={<FiEye />} label="Views" value={formatNumber(videoA?.views)} />
            <MetricItem icon={<FiHeart />} label="Likes" value={formatNumber(videoA?.likes)} />
            <MetricItem icon={<FiMessageCircle />} label="Comments" value={formatNumber(videoA?.comments)} />
          </div>
          <div className="mt-3 pt-3 border-t border-blue-200">
            <div className="flex justify-between items-center">
              <span className="text-sm text-blue-700">Engagement Rate</span>
              <span className={`text-xl font-bold ${getEngagementColor(engagementA?.engagement_rate)}`}>
                {engagementA?.engagement_rate ? `${engagementA.engagement_rate.toFixed(2)}%` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
        
        {/* Video B Metrics */}
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-semibold text-purple-900">Video B (Instagram)</span>
            <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded">
              {videoB?.creator || 'Unknown'}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <MetricItem icon={<FiEye />} label="Views" value={formatNumber(videoB?.views)} />
            <MetricItem icon={<FiHeart />} label="Likes" value={formatNumber(videoB?.likes)} />
            <MetricItem icon={<FiMessageCircle />} label="Comments" value={formatNumber(videoB?.comments)} />
          </div>
          <div className="mt-3 pt-3 border-t border-purple-200">
            <div className="flex justify-between items-center">
              <span className="text-sm text-purple-700">Engagement Rate</span>
              <span className={`text-xl font-bold ${getEngagementColor(engagementB?.engagement_rate)}`}>
                {engagementB?.engagement_rate ? `${engagementB.engagement_rate.toFixed(2)}%` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

const MetricItem = ({ icon, label, value }) => (
  <div className="text-center">
    <div className="text-blue-600 text-lg mb-1">{icon}</div>
    <div className="font-bold text-gray-900">{value}</div>
    <div className="text-xs text-gray-500">{label}</div>
  </div>
)

export default MetricsPanel