import React, { useState } from 'react';
import { 
  CalendarDays, 
  Users, 
  MapPin, 
  FilePlus2, 
  LayoutDashboard, 
  LogOut,
  User,
  ShieldCheck,
  Mail,
  CheckSquare
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import EmailOutboxModal from './EmailOutboxModal';

export default function Navbar({ activeTab, setActiveTab, healthStatus }) {
  const { currentUser, logout, isAdmin } = useAuth();
  const [showOutbox, setShowOutbox] = useState(false);

  const isManagerOrAdmin = isAdmin || currentUser?.role === 'MANAGER' || currentUser?.role === 'HR_ADMIN';

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'apply', label: 'Apply Leave', icon: FilePlus2 },
    ...(isManagerOrAdmin ? [{ id: 'approvals', label: 'Approvals Inbox', icon: CheckSquare }] : []),
    { id: 'employees', label: isAdmin ? 'Employees & Directory' : 'My Balances', icon: Users },
    { id: 'locations', label: isAdmin ? 'Locations & Policies' : 'My Office Location', icon: MapPin },
  ];

  return (
    <header className="navbar">
      <EmailOutboxModal isOpen={showOutbox} onClose={() => setShowOutbox(false)} />
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
        </nav>

        {/* Authenticated User Profile & Email Notifications & Sign Out */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Email Outbox Button */}
          <button
            onClick={() => setShowOutbox(prev => !prev)}
            className="btn btn-secondary btn-sm"
            title="Toggle Email & Gmail Notification Outbox"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              background: showOutbox ? 'rgba(99, 102, 241, 0.25)' : 'rgba(99, 102, 241, 0.08)',
              padding: '0.45rem 0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Mail size={15} />
            <span>Outbox</span>
          </button>
          {currentUser && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.6rem',
              padding: '0.35rem 0.75rem',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)'
            }}>
              <div style={{ 
                width: '28px', 
                height: '28px', 
                borderRadius: '50%', 
                background: 'var(--accent-gradient)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '0.8rem', 
                fontWeight: 700, 
                color: '#fff' 
              }}>
                {currentUser.name ? currentUser.name.charAt(0) : 'U'}
              </div>
              
              <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
                <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {currentUser.name}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {currentUser.location_id} Office &bull; Band {currentUser.grade}
                </div>
              </div>
            </div>
          )}

          {currentUser && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={logout}
              title="Sign out of your account"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: '#f87171',
                padding: '0.45rem 0.75rem',
                fontWeight: 600
              }}
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          )}

          <div className="system-status">
            <span className="status-dot"></span>
            <span>{healthStatus ? 'Live' : 'Connecting...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
