import React, { useState, useEffect } from 'react';
import { Mail, ChevronRight, ChevronDown, RefreshCw, X, Eye, CheckCircle2, AlertCircle, Clock, Trash2, RotateCw } from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';

export default function OutboxAccordion({ defaultOpen = false }) {
  const { currentUser } = useAuth();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

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

  useEffect(() => {
    if (isOpen) {
      fetchOutbox();
    }
  }, [isOpen, currentUser]);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <div
      className="card"
      style={{
        marginBottom: '1.75rem',
        padding: 0,
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
        background: '#0f172a',
      }}
    >
      {/* Interactive Collapsible Header */}
      <div
        onClick={handleToggle}
        style={{
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
          background: isOpen ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
          borderBottom: isOpen ? '1px solid var(--border-color)' : 'none',
          transition: 'background 0.2s ease',
        }}
        title={isOpen ? 'Click to close Outbox' : 'Click to open Outbox'}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#818cf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Mail size={16} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f8fafc' }}>Outbox</span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '0.1rem 0.45rem',
                  borderRadius: '999px',
                  background: 'rgba(99, 102, 241, 0.2)',
                  color: '#818cf8',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                }}
              >
                {emails.length} notifications
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '4px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#38bdf8',
                  fontWeight: 600,
                }}
              >
                GMAIL_SMTP
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Notifications for <strong>{currentUser?.name || 'User'}</strong> ({currentUser?.email}) &bull;{' '}
              {isOpen ? 'Click header or Collapse button to close' : 'Click to expand'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          {isOpen && (
            <>
              {emails.length > 0 && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearOutbox();
                  }}
                  className="btn btn-secondary btn-sm"
                  title="Clear Outbox Logs"
                  style={{
                    padding: '0.25rem 0.55rem',
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    color: '#94a3b8',
                  }}
                >
                  <Trash2 size={12} />
                  <span>Clear</span>
                </button>
              )}

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fetchOutbox();
                }}
                disabled={loading}
                className="btn btn-secondary btn-sm"
                style={{
                  padding: '0.25rem 0.55rem',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <RefreshCw size={12} className={loading ? 'spinning' : ''} />
                <span>Refresh</span>
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsOpen(false);
                }}
                className="btn btn-secondary btn-sm"
                title="Collapse Outbox"
                style={{
                  padding: '0.25rem 0.55rem',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  color: '#f87171',
                  borderColor: 'rgba(239, 68, 68, 0.3)',
                  background: 'rgba(239, 68, 68, 0.08)',
                }}
              >
                <X size={12} />
                <span>Collapse</span>
              </button>
            </>
          )}

          <div style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', paddingLeft: '0.25rem' }}>
            {isOpen ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </div>
        </div>
      </div>

      {/* Expanded Outbox Content */}
      {isOpen && (
        <>
          <div style={{ display: 'flex', minHeight: '320px', maxHeight: '440px' }}>
            {/* Email List Left */}
            <div
              style={{
                width: '42%',
                borderRight: '1px solid var(--border-color)',
                overflowY: 'auto',
                background: 'rgba(15, 23, 42, 0.5)',
              }}
            >
              {loading && emails.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                  <RefreshCw size={20} className="spinning" style={{ margin: '0 auto 0.5rem' }} />
                  <p style={{ fontSize: '0.8rem', margin: 0 }}>Loading notification records...</p>
                </div>
              ) : emails.length === 0 ? (
                <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#64748b' }}>
                  <Mail size={24} style={{ margin: '0 auto 0.5rem', opacity: 0.4 }} />
                  <p style={{ fontSize: '0.825rem', margin: 0 }}>No notifications recorded yet.</p>
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
                        padding: '0.75rem 1rem',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                        borderLeft: isSelected ? '3px solid #6366f1' : '3px solid transparent',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '0.2rem',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.675rem',
                            fontWeight: 700,
                            padding: '0.1rem 0.4rem',
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
                          }}
                        >
                          {em.notification_type}
                        </span>

                        <span
                          style={{
                            fontSize: '0.65rem',
                            fontWeight: 600,
                            padding: '0.08rem 0.35rem',
                            borderRadius: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.2rem',
                            background: isSent
                              ? 'rgba(34, 197, 94, 0.1)'
                              : isFailed
                              ? 'rgba(239, 68, 68, 0.1)'
                              : 'rgba(234, 179, 8, 0.1)',
                            color: isSent ? '#4ade80' : isFailed ? '#f87171' : '#facc15',
                          }}
                        >
                          {isSent ? <CheckCircle2 size={10} /> : isFailed ? <AlertCircle size={10} /> : <Clock size={10} />}
                          {em.status || 'SENT'}
                        </span>
                      </div>

                      <div
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          color: '#f1f5f9',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {em.subject}
                      </div>
                      <div
                        style={{
                          fontSize: '0.725rem',
                          color: '#94a3b8',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span>
                          To: <strong style={{ color: '#cbd5e1' }}>{em.recipient_name || em.to_email}</strong>
                        </span>
                        <span style={{ fontSize: '0.675rem', color: '#64748b' }}>
                          {new Date(em.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Email Preview Right */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem',
                background: '#020617',
              }}
            >
              {selectedEmail ? (
                <div>
                  <div
                    style={{
                      padding: '0.75rem 1rem',
                      background: '#0f172a',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      marginBottom: '0.75rem',
                      fontSize: '0.775rem',
                      color: '#94a3b8',
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
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                        {selectedEmail.subject}
                      </div>
                      {currentUser?.role === 'HR_ADMIN' && selectedEmail.status === 'FAILED' && (
                        <button
                          onClick={() => handleRetryNotification(selectedEmail.id)}
                          disabled={actionLoading}
                          className="btn btn-secondary btn-sm"
                          style={{
                            fontSize: '0.7rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            color: '#38bdf8',
                            padding: '0.2rem 0.5rem',
                          }}
                        >
                          <RotateCw size={11} className={actionLoading ? 'spinning' : ''} />
                          <span>Retry</span>
                        </button>
                      )}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.2rem 0.75rem' }}>
                      <div>
                        <strong>Sender:</strong>
                      </div>
                      <div style={{ color: '#e2e8f0' }}>leavemanagementsystem45@gmail.com</div>

                      <div>
                        <strong>To:</strong>
                      </div>
                      <div style={{ color: '#e2e8f0' }}>
                        {selectedEmail.recipient_name} &lt;{selectedEmail.to_email}&gt;
                      </div>

                      <div>
                        <strong>Mode:</strong>
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
                          marginTop: '0.5rem',
                          padding: '0.35rem 0.5rem',
                          background: 'rgba(239, 68, 68, 0.1)',
                          border: '1px solid rgba(239, 68, 68, 0.25)',
                          borderRadius: '4px',
                          fontSize: '0.725rem',
                          color: '#fca5a5',
                        }}
                      >
                        <strong>Diagnostics:</strong> {selectedEmail.error_message}
                      </div>
                    )}
                  </div>

                  <div
                    style={{
                      background: '#ffffff',
                      borderRadius: '8px',
                      padding: '0.85rem',
                      boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                      color: '#000',
                      fontSize: '0.85rem',
                    }}
                  >
                    <div dangerouslySetInnerHTML={{ __html: selectedEmail.html_content }} />
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '3rem 1rem' }}>
                  <Eye size={28} style={{ opacity: 0.4, margin: '0 auto 0.5rem' }} />
                  <p style={{ fontSize: '0.8rem' }}>Select an email from the left pane to preview content.</p>
                </div>
              )}
            </div>
          </div>

          {/* Collapsible Footer Bar */}
          <div
            style={{
              padding: '0.5rem 1rem',
              background: 'rgba(255, 255, 255, 0.02)',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
            }}
          >
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
            >
              <ChevronDown size={12} style={{ transform: 'rotate(180deg)', marginRight: '0.25rem' }} />
              Collapse Outbox
            </button>
          </div>
        </>
      )}
    </div>
  );
}
