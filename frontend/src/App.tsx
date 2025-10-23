import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Posts from './pages/Posts'
import PostDetail from './pages/PostDetail'
import Jobs from './pages/Jobs'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/posts" element={<Posts />} />
        <Route path="/posts/:postId" element={<PostDetail />} />
        <Route path="/jobs" element={<Jobs />} />
      </Routes>
    </Layout>
  )
}

export default App
