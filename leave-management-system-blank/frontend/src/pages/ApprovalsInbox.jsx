import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  User, 
  Calendar, 
  FileText, 
  AlertCircle, 
  RefreshCw, 
  ShieldCheck, 
  ArrowRight,
  MessageSquare,
  MailCheck,
  Building,
  History,
  Eye
} from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';
import OutboxAccordion from '../components/OutboxAccordion';

export default function ApprovalsInbox() {
  const { currentUser, isAdmin } = useAuth();
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [activeModal, setActiveModal] = useState(null); // { type: 'APPROVE' | 'REJECT', request: req }
  const [historyModal, setHistoryModal] = useState(null); // { request: req, history: [] }
  const [historyLoading, setHistoryLoading] = useState(false);
  const [comments, setComments] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const fetchPendingApprovals = async () => {
    if (!currentUser) return;
    setLoading(true);
    try {
      const data = await api.getPendingApprovals(
        currentUser.employee_id,
        isAdmin || currentUser.role === 'HR_ADMIN'
      );
      setPendingRequests(data || []);
    } catch (err) {
      console.error('Error fetching pending approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingApprovals();
  }, [currentUser, isAdmin]);

  const showToast = (msg, type = 'success') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 4500);
  };

  const handleOpenHistory = async (req) => {
    setHistoryLoading(true);
    setHistoryModal({ request: req, history: [] });
    try {
      const historyData = await api.getApprovalHistory(req.request_id);
      setHistoryModal({ request: req, history: historyData || [] });
    } catch (err) {
      console.error('Failed to load approval history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleDecision = async () => {
    if (!activeModal) return;
    const { type, request } = activeModal;

    if (type === 'REJECT' && !comments.trim()) {
      alert('Please provide a reason for rejecting the leave request.');
      return;
    }

    setActionLoading(request.request_id);
    try {
      if (type === 'APPROVE') {
        if (request.approval_id) {
          await api.approveApprovalStep(
            request.approval_id,
            currentUser.employee_id,
            comments.trim() || 'Approved'
          );
        } else {
          await api.approveTier(
            request.request_id,
            currentUser.employee_id,
            comments.trim() || 'Approved'
          );
        }
        showToast(
          `Request ${request.request_id} for ${request.employee_name} approved! Email notification sent.`
        );
      } else {
        if (request.approval_id) {
          await api.rejectApprovalStep(
            request.approval_id,
            currentUser.employee_id,
            comments.trim()
          );
        } else {
          await api.rejectTier(
            request.request_id,
            currentUser.employee_id,
            comments.trim()
          );
        }
        showToast(
          `Request ${request.request_id} rejected. Reserved days released & email sent to ${request.employee_name}.`,
          'info'
        );
      }

      setActiveModal(null);
      setComments('');
      fetchPendingApprovals();
    } catch (err) {
      const detail = err.message || 'Failed to process approval action.';
      alert(`Action Error: ${detail}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="fade-in" style={{ padding: '2rem 0', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 99999,
          background: toastMessage.type === 'success' ? '#059669' : '#3b82f6',
          color: '#fff',
          padding: '1rem 1.5rem',
          borderRadius: '10px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontWeight: 600,
          animation: 'slideIn 0.3s ease-out',
        }}>
          <MailCheck size={20} />
          <span>{toastMessage.msg}</span>
        </div>
      )}

      {/* Header Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}>
              <ShieldCheck size={24} />
            </div>
            <div>
              <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Multi-Tier Approvals Inbox
              </h1>
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Review and approve leave applications submitted by your reporting hierarchy
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={fetchPendingApprovals}
            disabled={loading}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem',
      }}>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Pending Decisions</span>
            <div className="metric-icon" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#eab308' }}>
              <Clock size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: '#eab308' }}>{pendingRequests.length}</div>
          <div className="metric-footer">Awaiting your sequential sign-off</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Your Assigned Role</span>
            <div className="metric-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
              <User size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ fontSize: '1.4rem' }}>{currentUser?.name}</div>
          <div className="metric-footer">{currentUser?.role === 'HR_ADMIN' ? 'Head of HR & Admin' : (currentUser?.designation || 'Manager')} &bull; {currentUser?.location_id}</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Notification Engine</span>
            <div className="metric-icon" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' }}>
              <MailCheck size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ fontSize: '1.4rem', color: '#22c55e' }}>Gmail SMTP Active</div>
          <div className="metric-footer">Auto-notifies next approvers and applicant</div>
        </div>
      </div>

      {/* Pending Approvals List */}
      {loading ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={36} className="spinning" style={{ margin: '0 auto 1rem', opacity: 0.6 }} />
          <p>Loading pending team requests...</p>
        </div>
      ) : pendingRequests.length === 0 ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(34, 197, 94, 0.15)',
            color: '#22c55e',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem',
          }}>
            <CheckCircle2 size={36} />
          </div>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            All Clear! No Pending Approvals
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '450px', margin: '0.5rem auto 0', fontSize: '0.9rem' }}>
            There are currently no leave requests awaiting your review. When a team member applies for leave, it will appear here immediately.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {pendingRequests.map((req) => (
            <div
              key={req.request_id}
              className="card"
              style={{
                padding: '1.5rem',
                border: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
                transition: 'all 0.2s ease',
              }}
            >
              {/* Top Row: Applicant Profile & Tier Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    background: 'var(--accent-gradient)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    color: '#fff',
                  }}>
                    {req.employee_name.charAt(0)}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {req.employee_name}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: 'var(--text-secondary)',
                      }}>
                        {req.employee_id} &bull; Band {req.grade}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      {req.designation} &bull; {req.department} &bull; {req.location_id} Office
                    </div>
                  </div>
                </div>

                {/* Tier Status Indicator */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    padding: '0.35rem 0.85rem',
                    borderRadius: '20px',
                    background: 'rgba(99, 102, 241, 0.15)',
                    color: '#818cf8',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}>
                    <Clock size={14} />
                    <span>{req.tier_name} (Level {req.current_tier})</span>
                  </span>
                </div>
              </div>

              {/* Middle Row: Request Details Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '1.2rem',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.04)',
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Leave Category
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {req.leave_type_name}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Date Range
                  </div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {req.start_date} &rarr; {req.end_date}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Working Days Deducted
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.2rem' }}>
                    {req.working_days} Days
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Available Balance
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#4ade80', marginTop: '0.2rem' }}>
                    {req.current_available_balance} Days
                  </div>
                </div>
              </div>

              {/* Bottom Row: Reason & Actions */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', maxWidth: '500px' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Reason: </strong>
                  <em>"{req.reason}"</em>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <button
                    onClick={() => handleOpenHistory(req)}
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
                    title="View full sequential approval history"
                  >
                    <History size={15} />
                    <span>View Chain</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveModal({ type: 'REJECT', request: req });
                      setComments('');
                    }}
                    disabled={actionLoading === req.request_id}
                    className="btn btn-secondary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      color: '#f87171',
                      border: '1px solid rgba(248, 113, 113, 0.3)',
                    }}
                  >
                    <XCircle size={16} />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveModal({ type: 'APPROVE', request: req });
                      setComments('Approved');
                    }}
                    disabled={actionLoading === req.request_id}
                    className="btn btn-primary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                    }}
                  >
                    <CheckCircle2 size={16} />
                    <span>Approve Step</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Real-time Email & Notifications Outbox */}
      <OutboxAccordion defaultOpen={false} />

      {/* Decision Comments Modal */}
      {activeModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(10, 15, 30, 0.8)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1.5rem',
        }}>
          <div style={{
            background: '#0f172a',
            border: '1px solid var(--border-color)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '520px',
            padding: '2rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: activeModal.type === 'APPROVE' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: activeModal.type === 'APPROVE' ? '#22c55e' : '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                {activeModal.type === 'APPROVE' ? <CheckCircle2 size={22} /> : <XCircle size={22} />}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                  {activeModal.type === 'APPROVE' ? 'Approve Leave Request' : 'Reject Leave Request'}
                </h3>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
                  {activeModal.request.employee_name} &bull; {activeModal.request.working_days} Working Days ({activeModal.request.tier_name})
                </p>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                {activeModal.type === 'APPROVE' ? 'Reviewer Notes / Comments (Optional)' : 'Rejection Reason (Required)'}
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder={activeModal.type === 'APPROVE' ? 'Enter comments or leave wishes...' : 'Explain why this request is being rejected...'}
                rows={3}
                style={{
                  width: '100%',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  color: '#fff',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={() => setActiveModal(null)}
                disabled={actionLoading !== null}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleDecision}
                disabled={actionLoading !== null}
                className="btn btn-primary"
                style={{
                  background: activeModal.type === 'APPROVE'
                    ? 'linear-gradient(135deg, #059669 0%, #10b981 100%)'
                    : 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
                }}
              >
                {actionLoading ? 'Processing...' : (activeModal.type === 'APPROVE' ? 'Confirm Approval' : 'Confirm Rejection')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Approval History Modal */}
      {historyModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(10, 15, 30, 0.8)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1.5rem',
        }}>
          <div style={{
            background: '#0f172a',
            border: '1px solid var(--border-color)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '600px',
            padding: '2rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                  Sequential Approval Chain & History
                </h3>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
                  Request {historyModal.request.request_id} &bull; {historyModal.request.employee_name}
                </p>
              </div>
              <button
                onClick={() => setHistoryModal(null)}
                className="btn btn-secondary btn-sm"
              >
                Close
              </button>
            </div>

            {historyLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
                <RefreshCw size={24} className="spinning" style={{ margin: '0 auto 0.5rem' }} />
                <p>Loading approval chain...</p>
              </div>
            ) : historyModal.history.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center' }}>No approval steps recorded.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {historyModal.history.map((step, idx) => {
                  const isApproved = step.status === 'APPROVED';
                  const isRejected = step.status === 'REJECTED';
                  const isPending = step.status === 'PENDING';
                  const isCurrent = step.tier_level === historyModal.request.current_tier && isPending;

                  return (
                    <div
                      key={step.approval_id || idx}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '1rem',
                        padding: '1rem',
                        borderRadius: '10px',
                        background: isCurrent ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                        border: isCurrent ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)',
                      }}
                    >
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isApproved ? 'rgba(34, 197, 94, 0.2)' : isRejected ? 'rgba(239, 68, 68, 0.2)' : isCurrent ? 'rgba(234, 179, 8, 0.2)' : 'rgba(148, 163, 184, 0.1)',
                        color: isApproved ? '#4ade80' : isRejected ? '#f87171' : isCurrent ? '#facc15' : '#94a3b8',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                      }}>
                        {isApproved ? '✓' : isRejected ? '✗' : step.tier_level}
                      </div>

                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                            {step.tier_name || `Level ${step.tier_level}`}
                          </span>
                          <span style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            background: isApproved ? 'rgba(34, 197, 94, 0.15)' : isRejected ? 'rgba(239, 68, 68, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                            color: isApproved ? '#4ade80' : isRejected ? '#f87171' : '#facc15',
                          }}>
                            {step.status}
                          </span>
                        </div>

                        <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                          Approver: <strong style={{ color: '#cbd5e1' }}>{step.approver_name || step.approver_id}</strong>
                          {step.decision_at && ` &bull; ${new Date(step.decision_at).toLocaleString()}`}
                        </div>

                        {step.comments && (
                          <div style={{
                            marginTop: '0.5rem',
                            fontSize: '0.8rem',
                            fontStyle: 'italic',
                            color: '#cbd5e1',
                            background: 'rgba(0, 0, 0, 0.2)',
                            padding: '0.4rem 0.6rem',
                            borderRadius: '6px',
                          }}>
                            "{step.comments}"
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
