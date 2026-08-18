import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { Mail, RefreshCw, X, Send, CheckCircle2, Clock, Eye, AlertCircle, Trash2, RotateCw } from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';

export default function EmailOutboxModal({ isOpen, onClose }) {
  const { currentUser } = useAuth();
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [testEmailInput, setTestEmailInput] = useState('');
  const [testEmailStatus, setTestEmailStatus] = useState(null);
  const [showTestPanel, setShowTestPanel] = useState(false);

  const fetchOutbox = async () => {
    setLoading(true);
    try {
      const data = await api.getNotificationOutbox(50, currentUser?.employee_id);
      setEmails(data || []);
      if (data && data.length > 0) {
        setSelectedEmail((prev) => {
          if (!prev) return data[0];
          const found = data.find((d) => d.id === prev.id);
          return found || data[0];
        });
      } else {
        setSelectedEmail(null);
      }
    } catch (err) {
      console.error('Failed to fetch outbox logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearOutbox = async () => {
    if (!window.confirm('Are you sure you want to clear your notification outbox history?')) return;
    try {
      await api.clearNotificationOutbox(currentUser?.employee_id);
      await fetchOutbox();
    } catch (err) {
      console.error('Failed to clear outbox:', err);
    }
  };

  const handleRetryNotification = async (notificationId) => {
    setActionLoading(true);
    try {
      const res = await api.retryNotification(notificationId);
      alert(res.message || 'Notification retried successfully.');
      await fetchOutbox();
    } catch (err) {
      alert(`Retry failed: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendTestEmail = async (e) => {
    e?.preventDefault();
    const targetEmail = testEmailInput.trim() || currentUser?.email;
    if (!targetEmail) return;

    setActionLoading(true);
    setTestEmailStatus(null);
    try {
      const res = await api.sendTestEmail(targetEmail);
      setTestEmailStatus({ success: true, message: res.message || `Test email dispatched to ${targetEmail}` });
      await fetchOutbox();
    } catch (err) {
      setTestEmailStatus({ success: false, message: err.message || 'Failed to dispatch test email.' });
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchOutbox();
      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, currentUser]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        background: 'rgba(10, 15, 30, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 999999,
        padding: '1.5rem',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#0f172a',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '1050px',
          height: '88vh',
          maxHeight: '820px',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255, 255, 255, 0.02)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#818cf8',
              }}
            >
              <Mail size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc' }}>
                  Gmail & System Notification Outbox
                </h3>
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '999px',
                    background: 'rgba(99, 102, 241, 0.2)',
                    color: '#818cf8',
                    fontWeight: 600,
                  }}
                >
                  GMAIL_SMTP
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
                User Mailbox: <strong>{currentUser?.name}</strong> ({currentUser?.email}) &bull; {emails.length} items
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {currentUser?.role === 'HR_ADMIN' && (
              <button
                onClick={() => setShowTestPanel((p) => !p)}
                className="btn btn-secondary btn-sm"
                style={{
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  borderColor: showTestPanel ? '#6366f1' : undefined,
                  color: showTestPanel ? '#818cf8' : undefined,
                }}
              >
                <Send size={13} />
                <span>Test Email</span>
              </button>
            )}

            {emails.length > 0 && (
              <button
                onClick={handleClearOutbox}
                className="btn btn-secondary btn-sm"
                title="Clear Outbox Logs"
                style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#94a3b8' }}
              >
                <Trash2 size={13} />
                <span>Clear</span>
              </button>
            )}

            <button
              onClick={fetchOutbox}
              disabled={loading}
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <RefreshCw size={13} className={loading ? 'spinning' : ''} />
              <span>Refresh</span>
            </button>

            <button
              onClick={onClose}
              className="btn btn-secondary btn-sm"
              title="Close Outbox (Esc)"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: '#f87171',
                borderColor: 'rgba(239, 68, 68, 0.3)',
                background: 'rgba(239, 68, 68, 0.1)',
                cursor: 'pointer',
              }}
            >
              <X size={15} />
              <span>Close</span>
            </button>
          </div>
        </div>

        {/* Optional Admin Test Email Drawer */}
        {showTestPanel && currentUser?.role === 'HR_ADMIN' && (
          <div
            style={{
              background: 'rgba(99, 102, 241, 0.08)',
              borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
              padding: '0.75rem 1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
            }}
          >
            <div style={{ fontSize: '0.825rem', color: '#cbd5e1' }}>
              <strong>Admin Gmail Test Tool:</strong> Send an immediate verification message via{' '}
              <code>leavemanagementsystem45@gmail.com</code>
            </div>
            <form onSubmit={handleSendTestEmail} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="email"
                placeholder={currentUser?.email || 'recipient@gmail.com'}
                value={testEmailInput}
                onChange={(e) => setTestEmailInput(e.target.value)}
                style={{
                  background: '#090d16',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.8rem',
                  color: '#f8fafc',
                  width: '240px',
                }}
              />
              <button
                type="submit"
                disabled={actionLoading}
                className="btn btn-primary btn-sm"
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.85rem' }}
              >
                {actionLoading ? 'Sending...' : 'Send Test'}
              </button>
            </form>
            {testEmailStatus && (
              <div
                style={{
                  fontSize: '0.75rem',
                  color: testEmailStatus.success ? '#4ade80' : '#f87171',
                  maxWidth: '300px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {testEmailStatus.message}
              </div>
            )}
          </div>
        )}

        {/* Content Body: Split Left (List) / Right (Preview) */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Left Email List */}
          <div
            style={{
              width: '38%',
              borderRight: '1px solid var(--border-color)',
              overflowY: 'auto',
              background: 'rgba(15, 23, 42, 0.6)',
            }}
          >
            {emails.length === 0 ? (
              <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: '#64748b' }}>
                <Mail size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
                <p style={{ fontSize: '0.9rem', margin: 0, fontWeight: 500 }}>No notifications recorded yet.</p>
                <p style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                  Submit a leave request to trigger sequential Gmail notifications.
                </p>
              </div>
            ) : (
              emails.map((em) => {
                const isSelected = selectedEmail && selectedEmail.id === em.id;
                const isSent = em.status === 'SENT';
                const isFailed = em.status === 'FAILED';

                return (
                  <div
                    key={em.id}
                    onClick={() => setSelectedEmail(em)}
                    style={{
                      padding: '0.9rem 1.2rem',
                      borderBottom: '1px solid var(--border-color)',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                      borderLeft: isSelected ? '3px solid #6366f1' : '3px solid transparent',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '0.35rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          padding: '0.12rem 0.45rem',
                          borderRadius: '4px',
                          background:
                            em.notification_type === 'ACTION_REQUIRED'
                              ? 'rgba(234, 179, 8, 0.15)'
                              : em.notification_type === 'REJECTION'
                              ? 'rgba(239, 68, 68, 0.15)'
                              : 'rgba(34, 197, 94, 0.15)',
                          color:
                            em.notification_type === 'ACTION_REQUIRED'
                              ? '#facc15'
                              : em.notification_type === 'REJECTION'
                              ? '#f87171'
                              : '#4ade80',
                          border: `1px solid ${
                            em.notification_type === 'ACTION_REQUIRED'
                              ? 'rgba(234, 179, 8, 0.3)'
                              : em.notification_type === 'REJECTION'
                              ? 'rgba(239, 68, 68, 0.3)'
                              : 'rgba(34, 197, 94, 0.3)'
                          }`,
                        }}
                      >
                        {em.notification_type}
                      </span>

                      {/* Status pill */}
                      <span
                        style={{
                          fontSize: '0.675rem',
                          fontWeight: 600,
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          background: isSent
                            ? 'rgba(34, 197, 94, 0.1)'
                            : isFailed
                            ? 'rgba(239, 68, 68, 0.1)'
                            : 'rgba(234, 179, 8, 0.1)',
                          color: isSent ? '#4ade80' : isFailed ? '#f87171' : '#facc15',
                        }}
                      >
                        {isSent ? <CheckCircle2 size={11} /> : isFailed ? <AlertCircle size={11} /> : <Clock size={11} />}
                        {em.status || 'SENT'}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: '#f1f5f9',
                        marginBottom: '0.25rem',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {em.subject}
                    </div>

                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span>
                        To: <strong>{em.recipient_name || em.to_email}</strong>
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                        {new Date(em.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Right Email Viewer */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.5rem',
              background: '#020617',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {selectedEmail ? (
              <div>
                <div
                  style={{
                    padding: '1rem 1.25rem',
                    background: '#0f172a',
                    border: '1px solid var(--border-color)',
                    borderRadius: '10px',
                    marginBottom: '1.25rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                      {selectedEmail.subject}
                    </div>
                    {currentUser?.role === 'HR_ADMIN' && selectedEmail.status === 'FAILED' && (
                      <button
                        onClick={() => handleRetryNotification(selectedEmail.id)}
                        disabled={actionLoading}
                        className="btn btn-secondary btn-sm"
                        style={{
                          fontSize: '0.75rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          color: '#38bdf8',
                        }}
                      >
                        <RotateCw size={12} className={actionLoading ? 'spinning' : ''} />
                        <span>Retry Delivery</span>
                      </button>
                    )}
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'auto 1fr',
                      gap: '0.35rem 1rem',
                      fontSize: '0.8rem',
                      color: '#94a3b8',
                    }}
                  >
                    <div>
                      <strong>System Sender:</strong>
                    </div>
                    <div style={{ color: '#e2e8f0' }}>leavemanagementsystem45@gmail.com</div>

                    <div>
                      <strong>Recipient:</strong>
                    </div>
                    <div style={{ color: '#e2e8f0' }}>
                      {selectedEmail.recipient_name} &lt;{selectedEmail.to_email}&gt;
                    </div>

                    <div>
                      <strong>Delivery Mode:</strong>
                    </div>
                    <div style={{ color: '#818cf8', fontWeight: 600 }}>
                      {selectedEmail.delivery_mode || 'GMAIL_SMTP'} (smtp.gmail.com:587)
                    </div>

                    <div>
                      <strong>Status:</strong>
                    </div>
                    <div
                      style={{
                        color:
                          selectedEmail.status === 'SENT'
                            ? '#4ade80'
                            : selectedEmail.status === 'FAILED'
                            ? '#f87171'
                            : '#facc15',
                        fontWeight: 600,
                      }}
                    >
                      {selectedEmail.status || 'SENT'}
                    </div>

                    <div>
                      <strong>Timestamp:</strong>
                    </div>
                    <div>{new Date(selectedEmail.timestamp).toLocaleString()}</div>
                  </div>

                  {selectedEmail.error_message && (
                    <div
                      style={{
                        marginTop: '0.75rem',
                        padding: '0.5rem 0.75rem',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.25)',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        color: '#fca5a5',
                      }}
                    >
                      <strong>Delivery Diagnostics:</strong> {selectedEmail.error_message}
                    </div>
                  )}
                </div>

                {/* Render HTML content */}
                <div
                  style={{
                    background: '#ffffff',
                    borderRadius: '12px',
                    padding: '1rem',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
                  }}
                >
                  <div dangerouslySetInnerHTML={{ __html: selectedEmail.html_content }} />
                </div>
              </div>
            ) : (
              <div style={{ margin: 'auto', textAlign: 'center', color: '#64748b' }}>
                <Eye size={40} style={{ opacity: 0.4, marginBottom: '0.75rem' }} />
                <p>Select an email from the left pane to preview its rendered content.</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '0.75rem 1.5rem',
            borderTop: '1px solid var(--border-color)',
            background: 'rgba(255, 255, 255, 0.02)',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <span style={{ fontSize: '0.8rem', color: '#64748b', marginRight: 'auto' }}>
            Press{' '}
            <kbd
              style={{
                background: '#1e293b',
                padding: '0.15rem 0.4rem',
                borderRadius: '4px',
                border: '1px solid #334155',
              }}
            >
              ESC
            </kbd>{' '}
            or click outside to dismiss
          </span>
          <button onClick={onClose} className="btn btn-secondary btn-sm" style={{ padding: '0.4rem 1rem', fontWeight: 600 }}>
            Close Outbox
          </button>
        </div>
      </div>
    </div>
  );

  return ReactDOM.createPortal(modalContent, document.body);
}
