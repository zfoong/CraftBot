import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AgentBridge } from './agent/AgentBridge'
import './styles/global.css'

// Initialize agent bridge connection
const craftbotWsUrl = import.meta.env.VITE_CRAFTBOT_WS_URL || 'ws://localhost:7926'
AgentBridge.initialize(craftbotWsUrl)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
