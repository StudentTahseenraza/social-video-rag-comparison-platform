import { motion } from 'framer-motion'
import { FiGithub, FiTrendingUp, FiMessageCircle, FiVideo } from 'react-icons/fi'

const Header = () => {
  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-40 backdrop-blur-sm bg-white/95"
    >
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <FiTrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                RAG Video Chatbot
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                AI-Powered Video Analysis & Comparison
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
              <FiVideo className="w-4 h-4" />
              <span>YouTube + Instagram</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
              <FiMessageCircle className="w-4 h-4" />
              <span>RAG + LangGraph</span>
            </div>
            <a
              href="https://github.com/yourusername/rag-chatbot"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-gray-900 transition"
            >
              <FiGithub className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </motion.header>
  )
}

export default Header