import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout.jsx'
import Home from './pages/Home.jsx'
import VariantAnalysis from './pages/VariantAnalysis.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<VariantAnalysis />} />
          <Route path="/analyze/:variantId" element={<VariantAnalysis />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
