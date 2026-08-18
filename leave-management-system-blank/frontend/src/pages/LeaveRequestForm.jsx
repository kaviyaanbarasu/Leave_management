import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  User, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Send, 
  Info,
  CalendarCheck,
  Building,
  Search,
  Award,
  Briefcase,
  MapPin,
  X,
  ShieldCheck,
  UserCheck
} from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';

export default function LeaveRequestForm({ setActiveTab }) {
  const { currentUser, isAdmin } = useAuth();
  const todayStr = new Date().toISOString().split('T')[0];
  const tomorrowStr = new Date(Date.now() + 86400000).toISOString().split('T')[0];

  const [employees, setEmployees] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(currentUser);
  const [applyForOther, setApplyForOther] = useState(false);

  const [availableLeaveTypes, setAvailableLeaveTypes] = useState([]);
  const [selectedLeaveTypeId, setSelectedLeaveTypeId] = useState('');
  const [startDate, setStartDate] = useState(todayStr);
  const [endDate, setEndDate] = useState(tomorrowStr);
  const [reason, setReason] = useState('');

  const [employeeBalances, setEmployeeBalances] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const dropdownRef = useRef(null);

  // Sync selected employee when currentUser changes
  useEffect(() => {
    if (!applyForOther && currentUser) {
      setSelectedEmployee(currentUser);
      setSearchQuery(`${currentUser.name} (${currentUser.employee_id})`);
    }
  }, [currentUser, applyForOther]);

  // Load all employees if HR Admin
  useEffect(() => {
    if (isAdmin) {
      api.getEmployees()
        .then((emps) => setEmployees(emps))
        .catch(console.error);
    }
  }, [isAdmin]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectEmployee = (emp) => {
    setSelectedEmployee(emp);
    setSearchQuery(`${emp.name} (${emp.employee_id})`);
    setIsDropdownOpen(false);
  };

  const filteredEmployees = employees.filter((emp) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      emp.name.toLowerCase().includes(q) ||
      emp.employee_id.toLowerCase().includes(q) ||
      (emp.grade && emp.grade.toLowerCase().includes(q)) ||
      (emp.department && emp.department.toLowerCase().includes(q)) ||
      (emp.location_id && emp.location_id.toLowerCase().includes(q))
    );
  });

  // When selected employee changes, load available leave types and balances for their location
  useEffect(() => {
    if (!selectedEmployee) return;

    // Fetch leave types for employee location
    api.getLeaveTypes(selectedEmployee.location_id)
      .then((types) => {
        setAvailableLeaveTypes(types);
        if (types.length > 0) {
          setSelectedLeaveTypeId(types[0].leave_type_id);
        } else {
          setSelectedLeaveTypeId('');
        }
      })
      .catch((err) => setErrorMessage(err.message));

    // Fetch balances
    api.getEmployeeBalances(selectedEmployee.employee_id)
      .then((bals) => setEmployeeBalances(bals))
      .catch(() => setEmployeeBalances(null));
  }, [selectedEmployee]);

  // Live preview calculation when dates, employee, or leave type change
  useEffect(() => {
    if (!selectedEmployee || !selectedLeaveTypeId || !startDate || !endDate) {
      setPreviewData(null);
      return;
    }

    setPreviewLoading(true);
    api.previewLeave({
      employee_id: selectedEmployee.employee_id,
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
  }, [selectedEmployee, selectedLeaveTypeId, startDate, endDate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee) {
      setErrorMessage("Please select an employee.");
      return;
    }
    if (!reason.trim()) {
      setErrorMessage("Please enter a reason for your leave request.");
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setSubmissionResult(null);

    try {
      const res = await api.createLeaveRequest({
        employee_id: selectedEmployee.employee_id,
        leave_type_id: selectedLeaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim(),
      });
      setSubmissionResult(res);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedBalanceItem = employeeBalances?.balances?.find(b => b.leave_type_id === selectedLeaveTypeId);

  return (
    <div className="animate-fade-in" style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileText size={22} className="text-primary" />
            <span>Apply For Leave</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="badge badge-location">{selectedEmployee?.location_id} Office</span>
            <span className="badge badge-grade">Band {selectedEmployee?.grade}</span>
          </div>
        </div>

        {submissionResult ? (
          <div className="alert alert-success" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1rem', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.15rem', fontWeight: 700 }}>
              <CheckCircle2 size={24} className="text-success" />
              <span>Leave Request Created Successfully!</span>
            </div>

            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-color)' }}>
              Your leave request for <strong>{selectedEmployee?.name}</strong> was saved to PostgreSQL and your balance has been atomically reserved. 
              The request is now pending review by a manager or HR.
            </p>

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
                  setReason('');
                }}
              >
                Submit Another Request
              </button>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('dashboard')}
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {errorMessage && (
              <div className="alert alert-danger mb-4">
                <AlertTriangle size={18} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Admin Toggle: Apply for Another Employee */}
            {isAdmin && (
              <div className="alert alert-info mb-4" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} />
                  <span><strong>HR Admin Mode:</strong> You can apply for yourself or on behalf of another employee.</span>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setApplyForOther(!applyForOther);
                    if (applyForOther) {
                      setSelectedEmployee(currentUser);
                    }
                  }}
                >
                  {applyForOther ? 'Apply For Myself' : 'Search Another Employee'}
                </button>
              </div>
            )}

            {/* Search Bar for HR Admin (if toggled) */}
            {isAdmin && applyForOther && (
              <div className="form-group" style={{ position: 'relative' }} ref={dropdownRef}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Search size={15} /> Search Employee Directory
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Type name, ID, or grade (e.g. 'ar', 'sharma', 'E101')..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setIsDropdownOpen(true);
                    }}
                    onFocus={() => setIsDropdownOpen(true)}
                    style={{ paddingLeft: '2.5rem', paddingRight: '2rem' }}
                  />
                  <Search size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery('');
                        setIsDropdownOpen(true);
                      }}
                      style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {isDropdownOpen && (
                  <div 
                    className="autocomplete-dropdown animate-fade-in"
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      zIndex: 50,
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-lg)',
                      maxHeight: '240px',
                      overflowY: 'auto',
                      marginTop: '0.35rem',
                    }}
                  >
                    {filteredEmployees.map((emp) => (
                      <div
                        key={emp.employee_id}
                        onClick={() => selectEmployee(emp)}
                        style={{
                          padding: '0.75rem 1rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          cursor: 'pointer',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {emp.name} <span className="font-mono text-muted" style={{ fontSize: '0.8rem' }}>({emp.employee_id})</span>
                          </div>
                          <div className="text-muted" style={{ fontSize: '0.775rem' }}>
                            {emp.designation} • {emp.department}
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                          <span className="badge badge-grade">{emp.grade}</span>
                          <span className="badge badge-location">{emp.location_id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Separate Dedicated Fields for Name, ID, Grade, Dept, Designation, Location */}
            {selectedEmployee && (
              <div 
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.25rem',
                  marginBottom: '1.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary)' }}>
                    Applicant Profile & Scoped Location
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>
                    Locked to Authenticated User
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                  {/* Name */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <User size={13} style={{ display: 'inline', marginRight: '4px' }} /> Employee Name
                    </label>
                    <input 
                      type="text" 
                      className="form-control" 
                      value={selectedEmployee.name} 
                      readOnly 
                      style={{ background: 'rgba(0,0,0,0.25)', fontWeight: 600 }} 
                    />
                  </div>

                  {/* ID */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      Employee ID
                    </label>
                    <input 
                      type="text" 
                      className="form-control font-mono" 
                      value={selectedEmployee.employee_id} 
                      readOnly 
                      style={{ background: 'rgba(0,0,0,0.25)' }} 
                    />
                  </div>

                  {/* Grade */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <Award size={13} style={{ display: 'inline', marginRight: '4px' }} /> Grade
                    </label>
                    <div 
                      className="form-control" 
                      style={{ 
                        background: 'rgba(0,0,0,0.25)', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        fontWeight: 700 
                      }}
                    >
                      <span>{selectedEmployee.grade}</span>
                      <span className="badge badge-grade" style={{ margin: 0 }}>Band {selectedEmployee.grade}</span>
                    </div>
                  </div>

                  {/* Department */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <Briefcase size={13} style={{ display: 'inline', marginRight: '4px' }} /> Department
                    </label>
                    <input 
                      type="text" 
                      className="form-control" 
                      value={selectedEmployee.department} 
                      readOnly 
                      style={{ background: 'rgba(0,0,0,0.25)' }} 
                    />
                  </div>

                  {/* Designation */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      Designation
                    </label>
                    <input 
                      type="text" 
                      className="form-control" 
                      value={selectedEmployee.designation} 
                      readOnly 
                      style={{ background: 'rgba(0,0,0,0.25)' }} 
                    />
                  </div>

                  {/* Office Location */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <MapPin size={13} style={{ display: 'inline', marginRight: '4px' }} /> Office Location
                    </label>
                    <div 
                      className="form-control" 
                      style={{ 
                        background: 'rgba(0,0,0,0.25)', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        fontWeight: 600 
                      }}
                    >
                      <span>{selectedEmployee.location_id} Office</span>
                      <span className="badge badge-location" style={{ margin: 0 }}>{selectedEmployee.location_id}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Leave Type & Available Balance */}
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Building size={15} /> Leave Type ({selectedEmployee?.location_id} Office Specific)
                </label>
                <select
                  className="form-select"
                  value={selectedLeaveTypeId}
                  onChange={(e) => setSelectedLeaveTypeId(e.target.value)}
                  required
                >
                  {availableLeaveTypes.length === 0 ? (
                    <option value="">No leave types configured for {selectedEmployee?.location_id}</option>
                  ) : (
                    availableLeaveTypes.map((lt) => (
                      <option key={lt.leave_type_id} value={lt.leave_type_id}>
                        {lt.name} ({lt.description || lt.leave_type_id})
                      </option>
                    ))
                  )}
                </select>
              </div>

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
                  {selectedBalanceItem ? `${selectedBalanceItem.available} Days Available` : 'Loading balance...'}
                  {selectedBalanceItem?.pending > 0 && (
                    <span className="text-muted" style={{ fontSize: '0.8rem', marginLeft: 'auto', fontWeight: 400 }}>
                      ({selectedBalanceItem.pending} reserved)
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Dynamic Date Pickers */}
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Calendar size={15} /> Start Date
                </label>
                <input
                  type="date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <CalendarCheck size={15} /> End Date
                </label>
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
                    <span>Location-Aware Working Day Preview ({selectedEmployee?.location_id})</span>
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
                placeholder="State the reason for requesting leave (e.g. Annual Vacation, Personal, Medical)..."
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.875rem' }}
              disabled={submitting || (previewData && !previewData.is_valid) || availableLeaveTypes.length === 0 || !selectedEmployee}
            >
              <Send size={18} />
              {submitting ? 'Submitting to PostgreSQL...' : 'Submit Leave Request'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
