import React, { useState, useEffect } from 'react';
import { 
  Users, 
  MapPin, 
  Clock, 
  Calendar, 
  PlayCircle, 
  XCircle, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw 
} from 'lucide-react';
import { api } from '../api/api';

export default function Dashboard({ setActiveTab }) {
  const [employees, setEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Accrual state
  const [accrualYear, setAccrualYear] = useState(2026);
  const [accrualMonth, setAccrualMonth] = useState(8);
  const [accrualRunning, setAccrualRunning] = useState(false);
  const [accrualResult, setAccrualResult] = useState(null);

  const [filterLocation, setFilterLocation] = useState('ALL');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [emps, locs, reqs, hols] = await Promise.all([
        api.getEmployees(),
        api.getLocations(),
        api.getLeaveRequests(),
        api.getHolidays(null, 2026),
      ]);
      setEmployees(emps);
      setLocations(locs);
      setLeaveRequests(reqs);
      setHolidays(hols);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCancelRequest = async (requestId) => {
    if (!window.confirm(`Are you sure you want to cancel leave request ${requestId}? This will release the reserved pending balance.`)) {
      return;
    }
    try {
      await api.cancelLeaveRequest(requestId);
      await loadData();
    } catch (err) {
      alert(`Error cancelling request: ${err.message}`);
    }
  };

  const handleRunAccrual = async () => {
    setAccrualRunning(true);
    setAccrualResult(null);
    try {
      const res = await api.runAccrual({ year: parseInt(accrualYear, 10), month: parseInt(accrualMonth, 10) });
      setAccrualResult(res);
      await loadData();
    } catch (err) {
      alert(`Accrual run error: ${err.message}`);
    } finally {
      setAccrualRunning(false);
    }
  };

  const pendingRequestsCount = leaveRequests.filter(r => r.status === 'PENDING').length;
  const filteredHolidays = filterLocation === 'ALL' 
    ? holidays 
    : holidays.filter(h => h.location_id === filterLocation);

  const employeeMap = Object.fromEntries(employees.map(e => [e.employee_id, e]));

  return (
    <div className="animate-fade-in">
      {/* Header & Accrual Bar */}
      <div className="flex-between mb-4" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Dynamic Leave Management Dashboard</h2>
          <p className="text-muted">Real-time balances, location-aware working days & dynamic accrual operations.</p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading} title="Refresh data">
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setActiveTab('apply')}>
            + New Leave Request
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="metrics-grid">
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
          <div className="metric-icon purple">
            <MapPin size={24} />
          </div>
          <div className="metric-info">
            <h4>Office Locations</h4>
            <div className="value">{locations.length}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon amber">
            <Clock size={24} />
          </div>
          <div className="metric-info">
            <h4>Pending Requests</h4>
            <div className="value">{pendingRequestsCount}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon emerald">
            <Calendar size={24} />
          </div>
          <div className="metric-info">
            <h4>Configured Holidays (2026)</h4>
            <div className="value">{holidays.length}</div>
          </div>
        </div>
      </div>

      {/* Monthly Accrual Trigger Box */}
      <div className="card mb-4" style={{ border: '1px solid rgba(99, 102, 241, 0.3)' }}>
        <div className="card-header">
          <div className="card-title">
            <PlayCircle size={22} className="text-primary" />
            <span>Monthly Accrual Execution (Idempotent Demo Runner)</span>
          </div>
          <span className="badge badge-grade">Deterministic Engine</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label className="form-label" style={{ margin: 0 }}>Year:</label>
            <select 
              className="form-select" 
              style={{ width: '100px' }}
              value={accrualYear} 
              onChange={(e) => setAccrualYear(e.target.value)}
            >
              <option value={2026}>2026</option>
              <option value={2027}>2027</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label className="form-label" style={{ margin: 0 }}>Month:</label>
            <select 
              className="form-select" 
              style={{ width: '140px' }}
              value={accrualMonth} 
              onChange={(e) => setAccrualMonth(e.target.value)}
            >
              <option value={1}>January (01)</option>
              <option value={2}>February (02)</option>
              <option value={3}>March (03)</option>
              <option value={4}>April (04)</option>
              <option value={5}>May (05)</option>
              <option value={6}>June (06)</option>
              <option value={7}>July (07)</option>
              <option value={8}>August (08)</option>
              <option value={9}>September (09)</option>
              <option value={10}>October (10)</option>
              <option value={11}>November (11)</option>
              <option value={12}>December (12)</option>
            </select>
          </div>

          <button 
            className="btn btn-primary"
            onClick={handleRunAccrual}
            disabled={accrualRunning}
          >
            <PlayCircle size={16} />
            {accrualRunning ? 'Executing Accrual...' : 'Run Monthly Accrual'}
          </button>
        </div>

        {accrualResult && (
          <div className="alert alert-info mt-4" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              <CheckCircle2 size={18} className="text-success" />
              <span>Accrual Results for {accrualResult.month}/{accrualResult.year} ({accrualResult.total_accrued} newly credited out of {accrualResult.total_processed} eligible items):</span>
            </div>
            <div style={{ marginTop: '0.5rem', width: '100%', fontSize: '0.85rem' }}>
              <div className="table-responsive">
                <table className="data-table" style={{ background: 'transparent' }}>
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Leave Type</th>
                      <th>Accrued Added</th>
                      <th>Previous Bal</th>
                      <th>New Bal</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accrualResult.details.map((d, i) => (
                      <tr key={i}>
                        <td className="font-mono">{d.employee_id}</td>
                        <td><span className="badge badge-leave">{d.leave_type_id}</span></td>
                        <td>+{d.accrued_amount.toFixed(2)}</td>
                        <td>{d.previous_balance.toFixed(2)}</td>
                        <td><strong>{d.new_balance.toFixed(2)}</strong></td>
                        <td>
                          {d.status === 'ACCRUED' && <span className="badge badge-approved">ACCRUED</span>}
                          {d.status === 'SKIPPED_ALREADY_ACCRUED' && <span className="badge badge-pending">SKIPPED (ALREADY ACCRUED)</span>}
                          {d.status === 'CAPPED_AT_MAX' && <span className="badge badge-grade">CAPPED AT MAX</span>}
                          {d.status === 'NO_POLICY' && <span className="badge badge-cancelled">NO POLICY</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Recent Leave Requests */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div className="card-title">
              <Clock size={20} className="text-primary" />
              <span>Leave Requests & Pending Reservations</span>
            </div>
            <span className="badge badge-location">{leaveRequests.length} Total</span>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Employee</th>
                  <th>Leave Type</th>
                  <th>Dates</th>
                  <th>Cal / Work Days</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {leaveRequests.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                      No leave requests yet. Click "+ New Leave Request" to submit one.
                    </td>
                  </tr>
                ) : (
                  leaveRequests.map((req) => {
                    const emp = employeeMap[req.employee_id];
                    return (
                      <tr key={req.request_id}>
                        <td className="font-mono" style={{ fontWeight: 600 }}>{req.request_id}</td>
                        <td>
                          <div><strong>{emp ? emp.name : req.employee_id}</strong></div>
                          <div className="text-muted" style={{ fontSize: '0.775rem' }}>
                            {emp ? `${emp.designation} (${emp.location_id})` : req.employee_id}
                          </div>
                        </td>
                        <td><span className="badge badge-leave">{req.leave_type_id}</span></td>
                        <td>
                          <div style={{ fontSize: '0.85rem' }}>{req.start_date} → {req.end_date}</div>
                          <div className="text-muted" style={{ fontSize: '0.75rem' }}>{req.reason}</div>
                        </td>
                        <td>
                          <strong>{req.working_days} working</strong>
                          <div className="text-muted" style={{ fontSize: '0.75rem' }}>({req.total_calendar_days} calendar)</div>
                        </td>
                        <td>
                          {req.status === 'PENDING' && <span className="badge badge-pending">PENDING (RESERVED)</span>}
                          {req.status === 'CANCELLED' && <span className="badge badge-cancelled">CANCELLED</span>}
                          {req.status === 'APPROVED' && <span className="badge badge-approved">APPROVED</span>}
                          {req.status === 'REJECTED' && <span className="badge badge-rejected">REJECTED</span>}
                        </td>
                        <td>
                          {req.status === 'PENDING' && (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleCancelRequest(req.request_id)}
                              title="Cancel request and release pending days"
                            >
                              <XCircle size={14} />
                              Cancel
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Upcoming Location Holidays */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Calendar size={20} className="text-primary" />
            <span>2026 Location Holiday Calendars</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="text-muted" style={{ fontSize: '0.85rem' }}>Location:</span>
            <select
              className="form-select"
              style={{ width: '180px', padding: '0.35rem 0.65rem', fontSize: '0.85rem' }}
              value={filterLocation}
              onChange={(e) => setFilterLocation(e.target.value)}
            >
              <option value="ALL">All Locations</option>
              {locations.map(loc => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name} ({loc.location_id})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Location</th>
                <th>Holiday Name</th>
                <th>Calendar Date</th>
                <th>Type</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {filteredHolidays.map((h) => (
                <tr key={h.holiday_id}>
                  <td><span className="badge badge-location">{h.location_id}</span></td>
                  <td><strong>{h.name}</strong></td>
                  <td className="font-mono">{h.date}</td>
                  <td><span className="badge badge-leave">{h.type || 'PUBLIC'}</span></td>
                  <td className="text-muted">{h.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
