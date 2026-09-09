import { Routes, Route } from 'react-router-dom'

import Produtos from '../pages/Produtos'
import ProdutoForm from '../pages/ProdutoForm'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/produtos" element={<Produtos />} />
      <Route path="/produtos/criar" element={<ProdutoForm />} />
      <Route path="/produtos/:id" element={<ProdutoForm />} />
    </Routes>
  )
}

export default AppRoutes