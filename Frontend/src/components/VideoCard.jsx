
function VideoCard({ video, engagement, label }) {
  if (!video) return null

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {video.thumbnail_url && (
        <img 
          src={video.thumbnail_url} 
          alt={video.title}
          className="w-full h-48 object-cover"
        />
      )}
      
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-lg">{label}</h3>
          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
            {video.platform}
          </span>
        </div>
        
        <h4 className="font-medium text-gray-900 mb-2 line-clamp-2">
          {video.title}
        </h4>
        
        <p className="text-sm text-gray-600 mb-1">
          Creator: {video.creator}
        </p>
        
        <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
          <div>
            <span className="text-gray-500">Views:</span>
            <span className="ml-2 font-medium">
              {video.views?.toLocaleString() || 'N/A'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Likes:</span>
            <span className="ml-2 font-medium">
              {video.likes?.toLocaleString() || 'N/A'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Comments:</span>
            <span className="ml-2 font-medium">
              {video.comments?.toLocaleString() || 'N/A'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Duration:</span>
            <span className="ml-2 font-medium">
              {video.duration ? `${Math.floor(video.duration / 60)}:${video.duration % 60}` : 'N/A'}
            </span>
          </div>
        </div>
        
        {engagement && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Engagement Rate:</span>
              <span className="text-lg font-bold text-blue-600">
                {engagement.engagement_rate ? `${engagement.engagement_rate.toFixed(2)}%` : 'N/A'}
              </span>
            </div>
            {engagement.message && (
              <p className="text-xs text-gray-500 mt-1">{engagement.message}</p>
            )}
          </div>
        )}
        
        {video.hashtags?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {video.hashtags.slice(0, 5).map(tag => (
              <span key={tag} className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default VideoCard