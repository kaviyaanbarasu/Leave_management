import React from 'react';
import { 
  CalendarDays, 
  Users, 
  MapPin, 
  FilePlus2, 
  LayoutDashboard, 
  ExternalLink 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, healthStatus }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'apply', label: 'Apply Leave', icon: FilePlus2 },
    { id: 'employees', label: 'Employees & Balances', icon: Users },
    { id: 'locations', label: 'Locations & Policies', icon: MapPin },
  ];

  return (
    <header className="navbar">
      <div className="nav-wrapper">
        <a href="#" className="brand" onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}>
          <div className="brand-icon">
            <CalendarDays size={20} />
          </div>
          <span>Dynamic PTO System</span>
        </a>

        <nav className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-btn ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}

          <a 
            href="http://127.0.0.1:8000/docs" 
            target="_blank" 
            rel="noreferrer" 
            className="nav-btn"
            title="Open FastAPI Swagger Documentation"
          >
            <ExternalLink size={16} />
            <span>FastAPI Docs</span>
          </a>
        </nav>

        <div className="system-status">
          <span className="status-dot"></span>
          <span>{healthStatus ? 'API Connected' : 'Connecting...'}</span>
        </div>
      </div>
    </header>
  );
}
