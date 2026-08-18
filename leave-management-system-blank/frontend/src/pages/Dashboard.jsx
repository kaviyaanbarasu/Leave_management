import React, { useState, useEffect } from 'react';
import { 
  Users, 
  MapPin, 
  Clock, 
  Calendar, 
  PlayCircle, 
  XCircle, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Check,
  X,
  Trash2,
  Filter,
  TrendingUp,
  Sparkles,
  Award,
  Shield,
  FilePlus2
} from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';
import OutboxAccordion from '../components/OutboxAccordion';

export default function Dashboard({ setActiveTab }) {
  const { currentUser, isAdmin } = useAuth();
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const [employees, setEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [userBalances, setUserBalances] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Accrual state
  const [accrualYear, setAccrualYear] = useState(currentYear);
  const [accrualMonth, setAccrualMonth] = useState(currentMonth);
  const [accrualRunning, setAccrualRunning] = useState(false);
  const [accrualResult, setAccrualResult] = useState(null);

  // Filters
  const [filterLocation, setFilterLocation] = useState(currentUser?.location_id || 'ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [holidayYear, setHolidayYear] = useState(currentYear);

  // Approval Progress Modal State
  const [selectedProgressRequest, setSelectedProgressRequest] = useState(null);
  const [approvalHistoryData, setApprovalHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const handleOpenProgress = async (req) => {
    setSelectedProgressRequest(req);
    setHistoryLoading(true);
    setApprovalHistoryData([]);
    try {
      const history = await api.getApprovalHistory(req.request_id);
      setApprovalHistoryData(history || []);
    } catch (err) {
      console.error('Failed to load approval history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadData = async () => {
    if (!currentUser) return;
    setLoading(true);
    setError(null);
    try {
      if (isAdmin) {
        const [emps, locs, reqs, hols] = await Promise.all([
          api.getEmployees(),
          api.getLocations(),
          api.getLeaveRequests(),
          api.getHolidays(null, holidayYear),
        ]);
        setEmployees(emps);
        setLocations(locs);
        setLeaveRequests(reqs);
        setHolidays(hols);
      } else {
        const [reqs, hols, bals] = await Promise.all([
          api.getLeaveRequests(currentUser.employee_id),
          api.getHolidays(currentUser.location_id, holidayYear),
          api.getEmployeeBalances(currentUser.employee_id),
        ]);
        setLeaveRequests(reqs);
        setHolidays(hols);
        setUserBalances(bals);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [holidayYear, currentUser]);

  const handleApproveRequest = async (requestId) => {
    try {
      await api.approveLeaveRequest(requestId);
      setActionSuccess(`Leave request ${requestId} has been APPROVED.`);
      setTimeout(() => setActionSuccess(null), 5000);
      await loadData();
    } catch (err) {
      alert(`Error approving request: ${err.message}`);
    }
  };

  const handleRejectRequest = async (requestId) => {
    if (!window.confirm(`Are you sure you want to reject leave request ${requestId}? This will release the reserved balance back to available.`)) {
      return;
    }
    try {
      await api.rejectLeaveRequest(requestId);
      setActionSuccess(`Leave request ${requestId} has been REJECTED. Reserved days released.`);
      setTimeout(() => setActionSuccess(null), 5000);
      await loadData();
    } catch (err) {
      alert(`Error rejecting request: ${err.message}`);
    }
  };

  const handleCancelRequest = async (requestId) => {
    if (!window.confirm(`Are you sure you want to cancel leave request ${requestId}? This will release the reserved pending balance.`)) {
      return;
    }
    try {
      await api.cancelLeaveRequest(requestId);
      setActionSuccess(`Leave request ${requestId} has been CANCELLED.`);
      setTimeout(() => setActionSuccess(null), 5000);
      await loadData();
    } catch (err) {
      alert(`Error cancelling request: ${err.message}`);
    }
  };

  const handleDeleteRequest = async (requestId) => {
    if (!window.confirm(`Delete record for request ${requestId}?`)) return;
    try {
      await api.deleteLeaveRequest(requestId);
      setActionSuccess(`Leave request ${requestId} deleted.`);
      setTimeout(() => setActionSuccess(null), 5000);
      await loadData();
    } catch (err) {
      alert(`Error deleting request: ${err.message}`);
    }
  };

  const handleRunAccrual = async () => {
    setAccrualRunning(true);
    setAccrualResult(null);
    try {
      const res = await api.runAccrual({
        year: parseInt(accrualYear, 10),
        month: parseInt(accrualMonth, 10),
      });
      setAccrualResult(res);
      setActionSuccess(`Accrual executed successfully for ${accrualMonth}/${accrualYear}: ${res.total_accrued} items accrued.`);
      setTimeout(() => setActionSuccess(null), 6000);
      await loadData();
    } catch (err) {
      alert(`Error running accrual: ${err.message}`);
    } finally {
      setAccrualRunning(false);
    }
  };

  // Scoped calculation for metrics
  // Scoped calculation for metrics
  const myRequests = leaveRequests.filter(r => r.employee_id === currentUser?.employee_id);
  const pendingRequests = (isAdmin ? leaveRequests : myRequests).filter(r => r.status.startsWith('PENDING'));
  const approvedRequests = (isAdmin ? leaveRequests : myRequests).filter(r => r.status === 'APPROVED');
  
  // Total available days for the current user
  const totalAvailableDays = userBalances?.balances?.reduce((sum, b) => sum + (b.available || 0), 0) || 0;
  const totalUsedDays = userBalances?.balances?.reduce((sum, b) => sum + (b.used || 0), 0) || 0;

  // Filter leave requests
  const filteredRequests = leaveRequests.filter((r) => {
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'PENDING') {
        if (!r.status.startsWith('PENDING')) return false;
      } else if (r.status !== filterStatus) {
        return false;
      }
    }
    if (isAdmin && filterLocation !== 'ALL') {
      const emp = employees.find(e => e.employee_id === r.employee_id);
      if (emp && emp.location_id !== filterLocation) return false;
    }
    return true;
  });

  // Filter holidays
  const filteredHolidays = holidays.filter((h) => {
    if (isAdmin && filterLocation !== 'ALL') {
      return h.location_id === filterLocation;
    }
    if (!isAdmin) {
      return h.location_id === currentUser?.location_id;
    }
    return true;
  });

  const getStatusBadge = (status, approverName) => {
    switch (status) {
      case 'APPROVED':
        return <span className="badge badge-approved" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.3)' }}><Check size={12} /> Approved</span>;
      case 'PENDING_MANAGER':
        return (
          <span className="badge badge-pending" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#facc15', border: '1px solid rgba(234, 179, 8, 0.3)' }}>
            <Clock size={12} /> Tier 1: Manager Review {approverName ? `(${approverName})` : ''}
          </span>
        );
      case 'PENDING_HR':
        return (
          <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            <Clock size={12} /> Tier 2: HR Admin Review
          </span>
        );
      case 'PENDING':
        return <span className="badge badge-pending"><Clock size={12} /> Pending Review</span>;
      case 'REJECTED':
        return <span className="badge badge-rejected" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)' }}><X size={12} /> Rejected</span>;
      case 'CANCELLED':
        return <span className="badge badge-cancelled"><XCircle size={12} /> Cancelled</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const isManagerOrAdmin = isAdmin || currentUser?.role === 'MANAGER' || currentUser?.role === 'HR_ADMIN';

  return (
    <div className="animate-fade-in">
      {/* Welcome Banner */}
      <div className="flex-between mb-4" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>
            Welcome back, {currentUser?.name}!
          </h2>
          <p className="text-muted">
            {isAdmin ? (
              <span><strong>HR Administrator View:</strong> Viewing company-wide leave requests, balances, and global office configurations.</span>
            ) : currentUser?.role === 'MANAGER' ? (
              <span><strong>Engineering Manager Workspace:</strong> Manage direct report leave approvals, view your personal balance, and apply for executive leaves.</span>
            ) : (
              <span><strong>Employee Workspace ({currentUser?.location_id} Office):</strong> Showing your personal balances, your leave requests, and {currentUser?.location_id} public holidays.</span>
            )}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {isManagerOrAdmin && (
            <button className="btn btn-secondary" onClick={() => setActiveTab('approvals')}>
              <Clock size={16} />
              Approvals Inbox
            </button>
          )}
          <button className="btn btn-primary" onClick={() => setActiveTab('apply')}>
            <FilePlus2 size={16} />
            Apply For Leave
          </button>
        </div>
      </div>

      {/* Action Required Callout for Managers */}
      {isManagerOrAdmin && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.12) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.2)',
              color: '#818cf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Shield size={20} />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                Multi-Tier Approval Authority Active
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                You have review and sign-off authority for team leave applications. Decisions trigger real-time email notifications.
              </div>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('approvals')}
            className="btn btn-primary btn-sm"
            style={{ background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)' }}
          >
            Review Team Approvals
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="alert alert-success animate-fade-in mb-4">
          <CheckCircle2 size={18} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-danger mb-4">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Scoped Metric Cards */}
      <div className="metrics-grid">
        {!isAdmin ? (
          <>
            <div className="metric-card">
              <div className="metric-icon emerald">
                <Calendar size={24} />
              </div>
              <div className="metric-info">
                <h4>My Available Leave</h4>
                <div className="value">{totalAvailableDays.toFixed(1)} Days</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon amber">
                <Clock size={24} />
              </div>
              <div className="metric-info">
                <h4>My Pending Requests</h4>
                <div className="value">{pendingRequests.length}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon indigo">
                <CheckCircle2 size={24} />
              </div>
              <div className="metric-info">
                <h4>My Approved Leaves</h4>
                <div className="value">{approvedRequests.length}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon purple">
                <MapPin size={24} />
              </div>
              <div className="metric-info">
                <h4>My Office Location</h4>
                <div className="value" style={{ fontSize: '1.25rem' }}>{currentUser?.location_id} Office</div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="metric-card">
              <div className="metric-icon indigo">
                <Users size={24} />
              </div>
              <div className="metric-info">
                <h4>Active Employees</h4>
                <div className="value">{employees.length}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon amber">
                <Clock size={24} />
              </div>
              <div className="metric-info">
                <h4>Pending Approvals</h4>
                <div className="value">{pendingRequests.length}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon purple">
                <MapPin size={24} />
              </div>
              <div className="metric-info">
                <h4>Global Locations</h4>
                <div className="value">{locations.length}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon emerald">
                <TrendingUp size={24} />
              </div>
              <div className="metric-info">
                <h4>Total Requests</h4>
                <div className="value">{leaveRequests.length}</div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* My Leave Entitlements Breakdown (For Regular Employee) */}
      {!isAdmin && userBalances && (
        <div className="card mb-4">
          <div className="card-header">
            <div className="card-title">
              <Award size={20} className="text-primary" />
              <span>My Real-Time Balances ({currentUser?.location_id} Scoped)</span>
            </div>
            <span className="badge badge-grade">Band {currentUser?.grade}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {userBalances.balances?.map((b) => (
              <div key={b.leave_type_id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span className="badge badge-leave">{b.leave_type_name || b.leave_type_id}</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>{b.available} Days</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  <div className="flex-between"><span>Opening:</span> <span>{b.opening_balance}</span></div>
                  <div className="flex-between"><span>Accrued:</span> <span>+{b.accrued}</span></div>
                  <div className="flex-between"><span>Used:</span> <span>-{b.used}</span></div>
                  <div className="flex-between"><span>Pending Reserved:</span> <span>{b.pending > 0 ? `-${b.pending}` : '0'}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Admin Monthly Accrual Box */}
      {isAdmin && (
        <div className="card mb-4" style={{ border: '1px solid rgba(99, 102, 241, 0.3)' }}>
          <div className="card-header">
            <div className="card-title">
              <Sparkles size={20} className="text-primary" />
              <span>Monthly Accrual Execution (Deterministic & Idempotent)</span>
            </div>
            <span className="badge badge-postgres">HR Admin Tool</span>
          </div>

          <p className="text-muted mb-3" style={{ fontSize: '0.875rem' }}>
            Accrues monthly leave entitlements for all active employees based on location, grade, and tenure policies. Running multiple times for the same month safely skips already-accrued balances.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label className="form-label" style={{ margin: 0, fontSize: '0.85rem' }}>Year:</label>
              <select
                className="form-select"
                style={{ width: '100px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                value={accrualYear}
                onChange={(e) => setAccrualYear(parseInt(e.target.value, 10))}
              >
                {[currentYear - 1, currentYear, currentYear + 1].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label className="form-label" style={{ margin: 0, fontSize: '0.85rem' }}>Month:</label>
              <select
                className="form-select"
                style={{ width: '130px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                value={accrualMonth}
                onChange={(e) => setAccrualMonth(parseInt(e.target.value, 10))}
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1, 1).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="btn btn-primary btn-sm"
              onClick={handleRunAccrual}
              disabled={accrualRunning}
            >
              <PlayCircle size={16} />
              {accrualRunning ? 'Calculating Accruals...' : `Execute Accruals for ${accrualMonth}/${accrualYear}`}
            </button>

            {accrualResult && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setAccrualResult(null)}
              >
                Hide Breakdown
              </button>
            )}
          </div>

          {/* Accrual Detailed Explanation Table */}
          {accrualResult && (
            <div className="mt-4 animate-fade-in" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h4 style={{ margin: 0, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <TrendingUp size={16} className="text-primary" />
                  <span>Accrual Ledger & Policy Audit Breakdown ({accrualResult.month}/{accrualResult.year})</span>
                </h4>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Total Processed: <strong>{accrualResult.total_processed}</strong> | Total Accrued: <strong className="text-success">{accrualResult.total_accrued}</strong>
                </div>
              </div>

              <div className="table-responsive">
                <table className="data-table" style={{ fontSize: '0.825rem' }}>
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Leave Type</th>
                      <th>Grade</th>
                      <th>Policy Applied</th>
                      <th>Rate</th>
                      <th>Prev Balance</th>
                      <th>Accrued</th>
                      <th>New Balance</th>
                      <th>Status</th>
                      <th>Reason / Explanation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accrualResult.details?.map((item, idx) => (
                      <tr key={`${item.employee_id}-${item.leave_type_id}-${idx}`}>
                        <td>
                          <strong>{item.employee_name || item.employee_id}</strong>
                          <div className="font-mono text-muted" style={{ fontSize: '0.75rem' }}>{item.employee_id}</div>
                        </td>
                        <td>
                          <span className="badge badge-leave">{item.leave_type_name || item.leave_type_id}</span>
                        </td>
                        <td>
                          <span className="badge badge-grade">{item.grade}</span>
                        </td>
                        <td>
                          <div>{item.policy_name || 'None'}</div>
                          {item.max_balance > 0 && (
                            <div className="text-muted" style={{ fontSize: '0.75rem' }}>Cap: {item.max_balance}d</div>
                          )}
                        </td>
                        <td className="font-mono">{item.monthly_accrual ? `+${item.monthly_accrual}d` : '—'}</td>
                        <td className="font-mono">{item.previous_balance.toFixed(2)}</td>
                        <td className="font-mono">
                          {item.actual_accrual > 0 ? (
                            <strong className="text-success">+{item.actual_accrual.toFixed(2)}</strong>
                          ) : (
                            <span className="text-muted">0.00</span>
                          )}
                        </td>
                        <td className="font-mono" style={{ fontWeight: 600 }}>{item.new_balance.toFixed(2)}</td>
                        <td>
                          {item.status === 'ACCRUED' ? (
                            <span className="badge badge-approved" style={{ fontSize: '0.75rem' }}>Accrued</span>
                          ) : item.status === 'CAPPED_AT_MAX' ? (
                            <span className="badge badge-pending" style={{ fontSize: '0.75rem' }}>Capped</span>
                          ) : item.status === 'SKIPPED_ALREADY_ACCRUED' ? (
                            <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)', fontSize: '0.75rem' }}>
                              Idempotent Skip
                            </span>
                          ) : (
                            <span className="badge badge-danger" style={{ fontSize: '0.75rem' }}>No Policy</span>
                          )}
                        </td>
                        <td style={{ maxWidth: '280px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                          {item.reason}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Grid: Leave Requests & Public Holidays */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Leave Requests Card */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
            <div className="card-title">
              <Clock size={20} className="text-primary" />
              <span>{isAdmin ? 'All Leave Requests' : 'My Leave Requests'}</span>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
                <Filter size={14} className="text-muted" />
                <span className="text-muted">Status:</span>
                <select
                  className="form-select"
                  style={{ width: '120px', padding: '0.3rem 0.5rem', fontSize: '0.825rem' }}
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <option value="ALL">All Status</option>
                  <option value="PENDING">Pending</option>
                  <option value="APPROVED">Approved</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
              </div>

              {isAdmin && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
                  <span className="text-muted">Location:</span>
                  <select
                    className="form-select"
                    style={{ width: '100px', padding: '0.3rem 0.5rem', fontSize: '0.825rem' }}
                    value={filterLocation}
                    onChange={(e) => setFilterLocation(e.target.value)}
                  >
                    <option value="ALL">All</option>
                    {locations.map(l => (
                      <option key={l.location_id} value={l.location_id}>{l.location_id}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  {isAdmin && <th>Employee</th>}
                  <th>Leave Type</th>
                  <th>Date Range</th>
                  <th>Working Days</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={isAdmin ? "8" : "7"} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                      No leave requests found.
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((req) => {
                    const emp = employees.find(e => e.employee_id === req.employee_id);
                    const isPending = req.status.startsWith('PENDING');
                    const isMyRequest = req.employee_id === currentUser?.employee_id;

                    return (
                      <tr key={req.request_id}>
                        <td className="font-mono" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                          {req.request_id}
                        </td>
                        {isAdmin && (
                          <td>
                            <strong>{emp?.name || req.employee_name || req.employee_id}</strong>
                            <div className="text-muted" style={{ fontSize: '0.75rem' }}>
                              {emp?.location_id} • Band {emp?.grade}
                            </div>
                          </td>
                        )}
                        <td>
                          <span className="badge badge-leave">{req.leave_type_id}</span>
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>
                          {req.start_date} &rarr; {req.end_date}
                        </td>
                        <td>
                          <strong className="text-primary">{req.working_days} Days</strong>
                        </td>
                        <td style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.825rem' }}>
                          {req.reason}
                        </td>
                        <td>{getStatusBadge(req.status, req.current_approver_name)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                              onClick={() => handleOpenProgress(req)}
                              title="View multi-level approval progress"
                            >
                              Approval Progress
                            </button>

                            {isAdmin && isPending && (
                              <>
                                <button
                                  className="btn btn-success btn-sm"
                                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                  onClick={() => handleApproveRequest(req.request_id)}
                                  title="Approve leave request"
                                >
                                  <Check size={13} /> Approve
                                </button>
                                <button
                                  className="btn btn-danger btn-sm"
                                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                  onClick={() => handleRejectRequest(req.request_id)}
                                  title="Reject leave request"
                                >
                                  <X size={13} /> Reject
                                </button>
                              </>
                            )}

                            {isPending && isMyRequest && (
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: '#fbbf24' }}
                                onClick={() => handleCancelRequest(req.request_id)}
                                title="Cancel leave request and release reserved days"
                              >
                                Cancel
                              </button>
                            )}

                            {isAdmin && (
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.25rem 0.4rem', color: '#ef4444' }}
                                onClick={() => handleDeleteRequest(req.request_id)}
                                title="Delete record"
                              >
                                <Trash2 size={13} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Collapsible Email & Notification Outbox Section */}
        <div style={{ gridColumn: 'span 2' }}>
          <OutboxAccordion defaultOpen={false} />
        </div>

        {/* Public Holidays Widget (Scoped to User's Office Location) */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div className="card-title">
              <Calendar size={20} className="text-primary" />
              <span>
                {isAdmin ? `Public Holidays Calendar (${holidayYear})` : `${currentUser?.location_id} Office Public Holidays (${holidayYear})`}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select
                className="form-select"
                style={{ width: '100px', padding: '0.3rem 0.5rem', fontSize: '0.825rem' }}
                value={holidayYear}
                onChange={(e) => setHolidayYear(parseInt(e.target.value, 10))}
              >
                {[currentYear - 1, currentYear, currentYear + 1, currentYear + 2].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Holiday Name</th>
                  <th>Date</th>
                  <th>Office Location</th>
                  <th>Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {filteredHolidays.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                      No holidays configured for year {holidayYear}.
                    </td>
                  </tr>
                ) : (
                  filteredHolidays.map((h) => (
                    <tr key={h.holiday_id}>
                      <td><strong>{h.name}</strong></td>
                      <td className="font-mono">{h.date}</td>
                      <td><span className="badge badge-location">{h.location_id}</span></td>
                      <td><span className="badge badge-grade">{h.type || 'PUBLIC'}</span></td>
                      <td className="text-muted" style={{ fontSize: '0.825rem' }}>{h.description || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sequential Multi-Level Approval Progress Modal */}
      {selectedProgressRequest && (
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
            maxWidth: '620px',
            padding: '2rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                  Sequential Approval Progress
                </h3>
                <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
                  Request {selectedProgressRequest.request_id} &bull; {selectedProgressRequest.working_days} Days ({selectedProgressRequest.leave_type_id})
                </p>
              </div>
              <button
                onClick={() => setSelectedProgressRequest(null)}
                className="btn btn-secondary btn-sm"
              >
                Close
              </button>
            </div>

            {/* Overall Status Banner */}
            <div style={{
              padding: '1rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overall Request Status</div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', marginTop: '0.2rem' }}>
                  {getStatusBadge(selectedProgressRequest.status, selectedProgressRequest.current_approver_name)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Date Range</div>
                <div style={{ fontSize: '0.9rem', color: '#f8fafc', fontWeight: 600, marginTop: '0.2rem' }}>
                  {selectedProgressRequest.start_date} &rarr; {selectedProgressRequest.end_date}
                </div>
              </div>
            </div>

            {historyLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
                <RefreshCw size={24} className="spinning" style={{ margin: '0 auto 0.5rem' }} />
                <p>Loading approval chain...</p>
              </div>
            ) : approvalHistoryData.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center' }}>No approval steps found.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {approvalHistoryData.map((step, idx) => {
                  const isApproved = step.status === 'APPROVED';
                  const isRejected = step.status === 'REJECTED';
                  const isPending = step.status === 'PENDING';
                  const isCurrent = step.tier_level === selectedProgressRequest.current_tier && isPending;

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
                        {isApproved ? '✓' : isRejected ? '✗' : isCurrent ? '●' : '○'}
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
                            color: isRejected ? '#fca5a5' : '#cbd5e1',
                            background: isRejected ? 'rgba(239, 68, 68, 0.1)' : 'rgba(0, 0, 0, 0.2)',
                            padding: '0.4rem 0.6rem',
                            borderRadius: '6px',
                            border: isRejected ? '1px solid rgba(239, 68, 68, 0.2)' : 'none',
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
