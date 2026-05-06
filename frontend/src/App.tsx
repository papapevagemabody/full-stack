import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import RedactionPage from './pages/RedactionPage';
import About from './pages/About';
import Login from './pages/Login';
import Register from './pages/Register';
import NotFound from './pages/NotFound';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import RoleProtectedRoute from './components/Auth/RoleProtectedRoute';
import SystemStatus from './pages/SystemStatus';
import UserProfile from './pages/UserProfile';
import UserManagement from './pages/UserManagement';
import UserCatalog from './pages/UserCatalog';
import './styles/globals.css';

function App() {
  return (
    <AuthProvider>
      <HelmetProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/about" element={<About />} />
              <Route path="/status" element={<SystemStatus />} />

              <Route
                path="/redaction"
                element={
                  <ProtectedRoute>
                    <RedactionPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <UserProfile />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/catalog"
                element={
                  <ProtectedRoute>
                    <UserCatalog />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/users"
                element={
                  <RoleProtectedRoute requiredRoles={['admin']}>
                    <UserManagement />
                  </RoleProtectedRoute>
                }
              />

              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </Router>
      </HelmetProvider>
    </AuthProvider>
  );
}

export default App;
