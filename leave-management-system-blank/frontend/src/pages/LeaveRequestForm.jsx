import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  User, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Send, 
  Info 
} from 'lucide-react';
import { api } from '../api/api';

export default function LeaveRequestForm({ setActiveTab }) {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [availableLeaveTypes, setAvailableLeaveTypes] = useState([]);
  const [selectedLeaveTypeId, setSelectedLeaveTypeId] = useState('');
  const [startDate, setStartDate] = useState('2026-10-19');
  const [endDate, setEndDate] = useState('2026-10-22');
  const [reason, setReason] = useState('Festival vacation');

  const [employeeBalances, setEmployeeBalances] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Load all employees on mount
  useEffect(() => {
    api.getEmployees()
      .then((emps) => {
        setEmployees(emps);
        if (emps.length > 0) {
          setSelectedEmployeeId(emps[0].employee_id);
        }
      })
      .catch((err) => setErrorMessage(err.message));
  }, []);

  // When selected employee changes, load available leave types and balances
  useEffect(() => {
    if (!selectedEmployeeId) return;

    const emp = employees.find(e => e.employee_id === selectedEmployeeId);
    if (!emp) return;

    // Fetch leave types for employee location
    api.getLeaveTypes(emp.location_id)
      .then((types) => {
        setAvailableLeaveTypes(types);
        if (types.length > 0) {
          setSelectedLeaveTypeId(types[0].leave_type_id);
        }
      })
      .catch((err) => setErrorMessage(err.message));

    // Fetch balances
    api.getEmployeeBalances(emp.employee_id)
      .then((bals) => setEmployeeBalances(bals))
      .catch(() => setEmployeeBalances(null));
  }, [selectedEmployeeId, employees]);

  // Live preview calculation when dates, employee, or leave type change
  useEffect(() => {
    if (!selectedEmployeeId || !selectedLeaveTypeId || !startDate || !endDate) {
      setPreviewData(null);
      return;
    }

    setPreviewLoading(true);
    api.previewLeave({
      employee_id: selectedEmployeeId,
      leave_type_id: selectedLeaveTypeId,
      start_date: startDate,
      end_date: endDate,
    })
      .then((data) => {
        setPreviewData(data);
      })
      .catch((err) => {
        setPreviewData({
          is_valid: false,
          message: err.message,
          total_calendar_days: 0,
          working_days: 0,
          current_available_balance: 0,
          projected_remaining_balance: 0,
        });
      })
      .finally(() => setPreviewLoading(false));
  }, [selectedEmployeeId, selectedLeaveTypeId, startDate, endDate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    setSubmissionResult(null);

    try {
      const res = await api.createLeaveRequest({
        employee_id: selectedEmployeeId,
        leave_type_id: selectedLeaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason: reason,
      });
      setSubmissionResult(res);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedEmployee = employees.find(e => e.employee_id === selectedEmployeeId);
  const selectedBalanceItem = employeeBalances?.balances?.find(b => b.leave_type_id === selectedLeaveTypeId);

  return (
    <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileText size={22} className="text-primary" />
            <span>Submit New Leave Request</span>
          </div>
          <span className="badge badge-grade">Atomic Reservation</span>
        </div>

        {submissionResult ? (
          <div className="alert alert-success" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1rem', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem', fontWeight: 700 }}>
              <CheckCircle2 size={24} className="text-success" />
              <span>Leave Request Created Successfully!</span>
            </div>

            <div className="calc-preview-card" style={{ width: '100%', marginTop: '0.5rem' }}>
              <div className="calc-preview-grid">
                <div className="calc-stat">
                  <div className="label">Request ID</div>
                  <div className="stat-val font-mono highlight">{submissionResult.request_id}</div>
                </div>
                <div className="calc-stat">
                  <div className="label">Status</div>
                  <div className="stat-val warning">PENDING</div>
                </div>
                <div className="calc-stat">
                  <div className="label">Working Days Reserved</div>
                  <div className="stat-val highlight">{submissionResult.reserved_days} Days</div>
                </div>
                <div className="calc-stat">
                  <div className="label">Remaining Available</div>
                  <div className="stat-val success">{submissionResult.remaining_available_balance} Days</div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => {
                  setSubmissionResult(null);
                  setReason('Vacation');
                }}
              >
                Submit Another Request
              </button>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('dashboard')}
              >
                View Dashboard
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {errorMessage && (
              <div className="alert alert-danger">
                <AlertTriangle size={18} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Employee Selector */}
            <div className="form-group">
              <label className="form-label">Select Employee</label>
              <select
                className="form-select"
                value={selectedEmployeeId}
                onChange={(e) => setSelectedEmployeeId(e.target.value)}
                required
              >
                {employees.map((emp) => (
                  <option key={emp.employee_id} value={emp.employee_id}>
                    {emp.name} ({emp.employee_id}) — {emp.designation} [{emp.location_id}] (Grade: {emp.grade})
                  </option>
                ))}
              </select>
            </div>

            {selectedEmployee && (
              <div className="alert alert-info" style={{ padding: '0.75rem 1rem', fontSize: '0.85rem' }}>
                <Info size={16} />
                <span>
                  <strong>{selectedEmployee.name}</strong> belongs to <strong>{selectedEmployee.location_id}</strong> location. 
                  Weekend configuration and holidays for {selectedEmployee.location_id} will be applied automatically.
                </span>
              </div>
            )}

            <div className="form-row">
              {/* Leave Type Selector */}
              <div className="form-group">
                <label className="form-label">Leave Type (Location Specific)</label>
                <select
                  className="form-select"
                  value={selectedLeaveTypeId}
                  onChange={(e) => setSelectedLeaveTypeId(e.target.value)}
                  required
                >
                  {availableLeaveTypes.map((lt) => (
                    <option key={lt.leave_type_id} value={lt.leave_type_id}>
                      {lt.name} ({lt.description || lt.leave_type_id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Current Balance Display */}
              <div className="form-group">
                <label className="form-label">Current Available Balance</label>
                <div 
                  className="form-control" 
                  style={{ 
                    background: 'rgba(0,0,0,0.3)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    fontWeight: 700, 
                    color: '#34d399' 
                  }}
                >
                  {selectedBalanceItem ? `${selectedBalanceItem.available} Days Available` : 'Loading...'}
                  {selectedBalanceItem?.pending > 0 && (
                    <span className="text-muted" style={{ fontSize: '0.8rem', marginLeft: 'auto', fontWeight: 400 }}>
                      ({selectedBalanceItem.pending} pending)
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Date Pickers */}
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">End Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Live Calculation Preview Card */}
            {previewData && (
              <div className="calc-preview-card mb-4">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                    <Clock size={16} className="text-primary" />
                    <span>Real-Time Working Day & Balance Preview</span>
                  </div>
                  {previewLoading && <span className="text-muted" style={{ fontSize: '0.8rem' }}>Calculating...</span>}
                </div>

                <div className="calc-preview-grid">
                  <div className="calc-stat">
                    <div className="label">Total Calendar Days</div>
                    <div className="stat-val">{previewData.total_calendar_days}</div>
                  </div>

                  <div className="calc-stat">
                    <div className="label">Calculated Working Days</div>
                    <div className="stat-val highlight">{previewData.working_days} Days</div>
                  </div>

                  <div className="calc-stat">
                    <div className="label">Current Available</div>
                    <div className="stat-val">{previewData.current_available_balance} Days</div>
                  </div>

                  <div className="calc-stat">
                    <div className="label">Projected Remaining</div>
                    <div className={`stat-val ${previewData.projected_remaining_balance >= 0 ? 'success' : 'warning'}`}>
                      {previewData.projected_remaining_balance} Days
                    </div>
                  </div>
                </div>

                {!previewData.is_valid && previewData.message && (
                  <div className="alert alert-danger" style={{ marginTop: '1rem', marginBottom: 0, padding: '0.5rem 0.75rem' }}>
                    <AlertTriangle size={16} />
                    <span>{previewData.message}</span>
                  </div>
                )}
              </div>
            )}

            {/* Reason */}
            <div className="form-group">
              <label className="form-label">Reason for Leave</label>
              <textarea
                className="form-control"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Specify the reason for requesting leave..."
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.875rem' }}
              disabled={submitting || (previewData && !previewData.is_valid)}
            >
              <Send size={18} />
              {submitting ? 'Submitting & Reserving Days...' : 'Submit Leave Request'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
