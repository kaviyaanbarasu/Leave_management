import React, { useState } from 'react';
import {
  Lock,
  User,
  ArrowRight,
  AlertCircle,
  Building,
  ShieldCheck,
  KeyRound,
  Eye,
  EyeOff
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, loading, error } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username.trim()) {
      setLocalError('Please enter your Employee ID or Work Email.');
      return;
    }

    setLocalError(null);

    try {
      await login(username.trim(), password || 'password123');
    } catch (err) {
      setLocalError(err.message);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem 1rem',
        background:
          'radial-gradient(ellipse at 50% 15%, rgba(99, 102, 241, 0.12), transparent 70%), var(--bg-body)'
      }}
    >
      <div style={{ maxWidth: '460px', width: '100%' }}>

        {/* Brand & Portal Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'var(--accent-gradient)',
              boxShadow: '0 10px 25px rgba(99, 102, 241, 0.4)',
              marginBottom: '1rem',
              color: '#fff'
            }}
          >
            <Building size={32} />
          </div>

          <h1
            style={{
              fontSize: '1.85rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              marginBottom: '0.35rem',
              letterSpacing: '-0.02em'
            }}
          >
            Employee Leave Portal
          </h1>

          <p className="text-muted" style={{ fontSize: '0.9rem' }}>
            Sign in to access your personal leave balances and requests
          </p>
        </div>

        {/* Secure Sign In Card */}
        <div
          className="card"
          style={{
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '2rem'
          }}
        >

          {/* Authentication Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.5rem',
              paddingBottom: '1rem',
              borderBottom: '1px solid var(--border-color)'
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 700,
                fontSize: '1.05rem',
                color: 'var(--text-primary)'
              }}
            >
              <Lock size={18} className="text-primary" />
              <span>Secure Authentication</span>
            </div>

            <span
              className="badge badge-postgres"
              style={{ fontSize: '0.7rem' }}
            >
              SSL Encrypted
            </span>
          </div>

          {/* Error Message */}
          {(localError || error) && (
            <div
              className="alert alert-danger mb-4"
              style={{
                fontSize: '0.85rem',
                padding: '0.75rem 1rem'
              }}
            >
              <AlertCircle size={16} />
              <span>{localError || error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>

            {/* Username / Employee ID */}
            <div className="form-group mb-3">
              <label
                className="form-label"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontSize: '0.85rem'
                }}
              >
                <User size={14} />
                Employee ID or Email
              </label>

              <input
                type="text"
                className="form-control"
                placeholder="e.g. E101 or vijeshthamodharan@gmail.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                required
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.95rem'
                }}
              />
            </div>

            {/* Password */}
            <div className="form-group mb-4">
              <label
                className="form-label"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontSize: '0.85rem'
                }}
              >
                <KeyRound size={14} />
                Password
              </label>

              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-control"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    padding: '0.75rem 2.75rem 0.75rem 1rem',
                    fontSize: '0.95rem'
                  }}
                  required
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '0.85rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                  tabIndex={-1}
                  aria-label={
                    showPassword ? 'Hide password' : 'Show password'
                  }
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '0.85rem',
                fontSize: '1rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
              disabled={loading}
            >
              <span>
                {loading ? 'Verifying Profile...' : 'Sign In'}
              </span>
              <ArrowRight size={18} />
            </button>
          </form>
        </div>

        {/* Security & Confidentiality Footer */}
        <div
          style={{
            textAlign: 'center',
            marginTop: '1.5rem',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem'
          }}
        >
          <ShieldCheck size={15} className="text-success" />
          <span>
            Strict individual confidentiality enforced. Only your personal
            records will load.
          </span>
        </div>

      </div>
    </div>
  );
}