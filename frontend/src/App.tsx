import { Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

import Dashboard from '@/pages/Dashboard';
import SessionPage from '@/pages/Session';
import CompanyPage from '@/pages/Company';
import HeaderBar from '@/components/layout/HeaderBar';

export default function App() {
  const location = useLocation();

  if (location.pathname === '/') {
    return <Dashboard />;
  }

  return (
    <div className="min-h-screen bg-[#f6f7fb]">
      <HeaderBar />
      <main className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto">
        <Suspense fallback={<div className="text-center py-10">Loading…</div>}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/sessions/:id" element={<SessionPage />} />
            <Route path="/companies/:companyId" element={<CompanyPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
