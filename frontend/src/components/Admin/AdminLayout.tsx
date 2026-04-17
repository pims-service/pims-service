import React from 'react';
import { Outlet } from 'react-router-dom';
import AdminSidebar from './AdminSidebar';

const AdminLayout: React.FC = () => {
  return (
    <div className="flex bg-zinc-50 min-h-[calc(100vh-64px)] overflow-x-hidden">
      {/* Sidebar - Fixed/Sticky on the left */}
      <AdminSidebar />
      
      {/* Main Content Area */}
      <main className="flex-grow p-10 max-w-7xl">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
