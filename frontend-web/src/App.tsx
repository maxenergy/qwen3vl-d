import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import Dashboard from './pages/Dashboard'
import ProjectList from './pages/Projects/ProjectList'
import ProjectDetail from './pages/Projects/ProjectDetail'
import Generation from './pages/Generation'
import Images from './pages/Images'
import Annotation from './pages/Annotation'
import Datasets from './pages/Datasets'
import Training from './pages/Training'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="projects/:projectId/generation" element={<Generation />} />
          <Route path="projects/:projectId/images" element={<Images />} />
          <Route path="projects/:projectId/annotation" element={<Annotation />} />
          <Route path="projects/:projectId/datasets" element={<Datasets />} />
          <Route path="projects/:projectId/training" element={<Training />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
