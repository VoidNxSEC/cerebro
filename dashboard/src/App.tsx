import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { Layout } from '@/components/dashboard/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Projects } from '@/pages/Projects'
import { Intelligence } from '@/pages/Intelligence'
import { Briefing } from '@/pages/Briefing'
import { Settings } from '@/pages/Settings'
import { Metrics } from '@/pages/Metrics'
import { Chat } from '@/pages/Chat'
import { Agents } from '@/pages/Agents'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectName" element={<Projects />} />
          <Route path="/intelligence" element={<Intelligence />} />
          <Route path="/briefing" element={<Briefing />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
      <Toaster />
    </BrowserRouter>
  )
}

export default App
