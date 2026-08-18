import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import LeaveRequestForm from './pages/LeaveRequestForm';
import EmployeeList from './pages/EmployeeList';
import LocationList from './pages/LocationList';
import { api } from './api/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [healthStatus, setHealthStatus] = useState(false);

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await api.checkHealth();
        if (res && res.status === 'healthy') {
          setHealthStatus(true);
        }
      } catch {
        setHealthStatus(false);
      }
    };

    checkApi();
    const interval = setInterval(checkApi, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        healthStatus={healthStatus} 
      />

      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} />}
        {activeTab === 'apply' && <LeaveRequestForm setActiveTab={setActiveTab} />}
        {activeTab === 'employees' && <EmployeeList />}
        {activeTab === 'locations' && <LocationList />}
      </main>

      <footer style={{ 
        textAlign: 'center', 
        padding: '2rem 1.5rem', 
        borderTop: '1px solid var(--border-color)', 
        color: 'var(--text-muted)', 
        fontSize: '0.85rem' 
      }}>
        <p><strong>Dynamic PTO & Leave Management System MVP</strong> &bull; Location-aware Holidays &bull; Configurable Weekend Rules &bull; Idempotent Monthly Accrual</p>
        <p style={{ marginTop: '0.25rem', fontSize: '0.775rem' }}>Strict domain isolation: Employee belongs to Location &bull; LeaveType belongs to Location &bull; No direct associations</p>
      </footer>
    </div>
  );
}
