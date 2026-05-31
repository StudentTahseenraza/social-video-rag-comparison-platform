import { motion, AnimatePresence } from 'framer-motion'

const LoadingModal = ({ isOpen, step, progress }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4"
          >
            <div className="text-center">
              {/* Animated Icon */}
              <div className="mb-6 flex justify-center">
                <div className="relative">
                  <div className="w-20 h-20 border-4 border-blue-200 rounded-full animate-pulse"></div>
                  <div className="absolute top-0 left-0 w-20 h-20 border-4 border-blue-600 rounded-full animate-spin" style={{ borderTopColor: 'transparent' }}></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-8 h-8 text-blue-600 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              {/* Loading Text */}
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Processing Videos
              </h3>
              <p className="text-gray-600 mb-6">
                {step || "Initializing..."}
              </p>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4 overflow-hidden">
                <motion.div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              
              {/* Progress Percentage */}
              <p className="text-sm text-gray-500 mb-2">
                {Math.round(progress)}% Complete
              </p>
              
              {/* Animated Steps */}
              <div className="mt-6 space-y-2">
                <StepIndicator 
                  text="Extracting metadata" 
                  active={progress >= 10}
                  completed={progress > 25}
                />
                <StepIndicator 
                  text="Fetching transcripts" 
                  active={progress >= 40}
                  completed={progress > 60}
                />
                <StepIndicator 
                  text="Generating embeddings" 
                  active={progress >= 75}
                  completed={progress > 90}
                />
                <StepIndicator 
                  text="Ready for chat" 
                  active={progress >= 100}
                  completed={progress >= 100}
                />
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

const StepIndicator = ({ text, active, completed }) => {
  return (
    <div className="flex items-center gap-3">
      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${completed ? 'bg-green-500' : active ? 'bg-blue-500 animate-pulse' : 'bg-gray-300'}`}>
        {completed && (
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>
      <span className={`text-sm ${completed ? 'text-gray-700' : active ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
        {text}
      </span>
    </div>
  )
}

export default LoadingModal