import { useEffect } from 'react'
import { MainView } from './views/MainView'
import { AppController } from './controllers/AppController'
import { useAgentAware } from './agent/hooks'

// Initialize the controller
const controller = new AppController()

function App() {
  // Make the app state agent-aware
  const state = useAgentAware('App', {
    initialized: true,
    componentName: 'App',
  })

  useEffect(() => {
    // Start the controller on mount
    controller.initialize()

    return () => {
      // Cleanup on unmount
      controller.cleanup()
    }
  }, [])

  return (
    <div className="app">
      <MainView controller={controller} />
    </div>
  )
}

export default App
