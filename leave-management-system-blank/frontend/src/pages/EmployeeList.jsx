import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Eye, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  Calendar, 
  Briefcase, 
  MapPin, 
  Award,
  Search,
  Filter,
  Sliders,
  Trash2,
  Edit3,
  User,
  Shield,
  Clock
} from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';

export default function EmployeeList() {
  const { currentUser, isAdmin } = useAuth();
  const todayStr = new Date().toISOString().split('T')[0];

  const [employees, setEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [myBalances, setMyBalances] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Search & Filter (for Admin)
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLocation, setFilterLocation] = useState('ALL');
  const [filterDept, setFilterDept] = useState('ALL');

  // Balance modal state (for Admin)
  const [selectedEmployeeBalances, setSelectedEmployeeBalances] = useState(null);
  const [balanceModalOpen, setBalanceModalOpen] = useState(false);
  const [balanceLoading, setBalanceLoading] = useState(false);

  // Adjust Balance modal state (for Admin)
  const [adjustModalOpen, setAdjustModalOpen] = useState(false);
  const [adjustTargetEmp, setAdjustTargetEmp] = useState(null);
  const [adjustLeaveTypeId, setAdjustLeaveTypeId] = useState('');
  const [adjustDays, setAdjustDays] = useState(0);
  const [adjustReason, setAdjustReason] = useState('Manual admin adjustment');
  const [adjustLoading, setAdjustLoading] = useState(false);
  const [adjustError, setAdjustError] = useState(null);

  // Add Employee Modal state (for Admin)
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    employee_id: '',
    name: '',
    email: '',
    department: 'Engineering',
    designation: 'Software Engineer',
    grade: 'G5',
    location_id: 'BLR',
    joining_date: todayStr,
    status: 'ACTIVE',
    role: 'EMPLOYEE',
    password: 'password123',
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [emps, locs] = await Promise.all([
          api.getEmployees(),
          api.getLocations(),
        ]);
        setEmployees(emps);
        setLocations(locs);
      } else if (currentUser) {
        const bals = await api.getEmployeeBalances(currentUser.employee_id);
        setMyBalances(bals);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isAdmin, currentUser]);

  const handleViewBalances = async (employeeId) => {
    setBalanceLoading(true);
    setBalanceModalOpen(true);
    try {
      const data = await api.getEmployeeBalances(employeeId);
      setSelectedEmployeeBalances(data);
    } catch (err) {
      alert(`Error loading balances: ${err.message}`);
      setBalanceModalOpen(false);
    } finally {
      setBalanceLoading(false);
    }
  };

  const openAdjustModal = async (emp) => {
    setAdjustTargetEmp(emp);
    setAdjustDays(0);
    setAdjustReason('Manual admin adjustment');
    setAdjustError(null);
    try {
      const data = await api.getEmployeeBalances(emp.employee_id);
      setSelectedEmployeeBalances(data);
      if (data.balances && data.balances.length > 0) {
        setAdjustLeaveTypeId(data.balances[0].leave_type_id);
      }
      setAdjustModalOpen(true);
    } catch (err) {
      alert(`Error fetching employee leave types: ${err.message}`);
    }
  };

  const handleAdjustBalance = async (e) => {
    e.preventDefault();
    if (!adjustLeaveTypeId) {
      setAdjustError("Please select a leave type to adjust.");
      return;
    }
    if (adjustDays === 0) {
      setAdjustError("Adjustment amount cannot be zero.");
      return;
    }

    setAdjustLoading(true);
    setAdjustError(null);

    try {
      await api.adjustBalance(adjustTargetEmp.employee_id, {
        leave_type_id: adjustLeaveTypeId,
        adjustment_days: parseFloat(adjustDays),
        reason: adjustReason.trim(),
      });
      setAdjustModalOpen(false);
      setActionSuccess(`Adjusted ${adjustDays > 0 ? `+${adjustDays}` : adjustDays} days for ${adjustTargetEmp.name} (${adjustLeaveTypeId})`);
      setTimeout(() => setActionSuccess(null), 5000);
      await loadData();
    } catch (err) {
      setAdjustError(err.message);
    } finally {
      setAdjustLoading(false);
    }
  };

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    setAddLoading(true);
    setAddError(null);

    try {
      await api.createEmployee(newEmployee);
      setAddModalOpen(false);
      setActionSuccess(`Employee ${newEmployee.name} (${newEmployee.employee_id}) created with auto-initialized balances!`);
      setTimeout(() => setActionSuccess(null), 5000);
      setNewEmployee({
        employee_id: '',
        name: '',
        email: '',
        department: 'Engineering',
        designation: 'Software Engineer',
        grade: 'G5',
        location_id: locations.length > 0 ? locations[0].location_id : 'BLR',
        joining_date: todayStr,
        status: 'ACTIVE',
        role: 'EMPLOYEE',
        password: 'password123',
      });
      await loadData();
    } catch (err) {
      setAddError(err.message);
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteEmployee = async (employeeId, name) => {
    if (!window.confirm(`Delete employee ${name} (${employeeId}) and all associated records?`)) {
      return;
    }
    try {
      await api.deleteEmployee(employeeId);
      setActionSuccess(`Employee ${name} has been removed.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(`Error deleting employee: ${err.message}`);
    }
  };

  // Filter employees for Admin
  const filteredEmployees = employees.filter((emp) => {
    if (filterLocation !== 'ALL' && emp.location_id !== filterLocation) return false;
    if (filterDept !== 'ALL' && emp.department !== filterDept) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matchName = emp.name.toLowerCase().includes(q);
      const matchId = emp.employee_id.toLowerCase().includes(q);
      const matchEmail = emp.email.toLowerCase().includes(q);
      const matchDesig = emp.designation.toLowerCase().includes(q);
      return matchName || matchId || matchEmail || matchDesig;
    }
    return true;
  });

  const departments = Array.from(new Set(employees.map(e => e.department).filter(Boolean)));

  // If regular employee, show personal profile and entitlements
  if (!isAdmin) {
    return (
      <div className="animate-fade-in" style={{ maxWidth: '840px', margin: '0 auto' }}>
        <div className="flex-between mb-4">
          <div>
            <h2>My Leave Balances & Entitlements</h2>
            <p className="text-muted">Live view of your available, accrued, used, and reserved leave days in {currentUser?.location_id}.</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
              Role: {currentUser?.role === 'HR_ADMIN' ? 'HR Admin' : currentUser?.role === 'MANAGER' ? 'Manager' : 'Employee'}
            </span>
            <span className="badge badge-grade">Grade: {currentUser?.grade}</span>
          </div>
        </div>

        {/* Employee Profile Summary */}
        <div className="card mb-4">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>EMPLOYEE NAME</div>
              <div style={{ fontWeight: 600, fontSize: '1.05rem' }}>{currentUser?.name}</div>
              <div className="font-mono text-muted" style={{ fontSize: '0.8rem' }}>{currentUser?.employee_id}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>DEPARTMENT & DESIGNATION</div>
              <div>{currentUser?.designation}</div>
              <div className="text-muted" style={{ fontSize: '0.8rem' }}>{currentUser?.department}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>ASSIGNED LOCATION</div>
              <div style={{ fontWeight: 600 }}>{currentUser?.location_id} Office</div>
              <span className="badge badge-location" style={{ marginTop: '0.25rem' }}>{currentUser?.location_id} Scoped</span>
            </div>
          </div>
        </div>

        {/* Balances Breakdown Cards */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Award size={20} className="text-primary" />
              <span>Leave Type Balances</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {myBalances?.balances?.map((b) => (
              <div 
                key={b.leave_type_id}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div>
                    <span className="badge badge-leave" style={{ fontSize: '0.85rem' }}>{b.leave_type_name || b.leave_type_id}</span>
                    <span className="font-mono text-muted" style={{ fontSize: '0.75rem', marginLeft: '0.5rem' }}>{b.leave_type_id}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#34d399', fontFamily: 'var(--font-heading)' }}>
                      {b.available} Days
                    </span>
                    <div className="text-muted" style={{ fontSize: '0.75rem' }}>Available to Request</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.75rem' }}>
                  <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Opening:</span> <strong>{b.opening_balance}</strong></div>
                  <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Accrued:</span> <strong className="text-success">+{b.accrued}</strong></div>
                  <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Used:</span> <strong style={{ color: '#ef4444' }}>-{b.used}</strong></div>
                  <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Pending Reserved:</span> <strong style={{ color: '#fbbf24' }}>{b.pending > 0 ? `-${b.pending}` : '0'}</strong></div>
                  {b.adjusted !== 0 && (
                    <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Adjusted:</span> <strong>{b.adjusted > 0 ? `+${b.adjusted}` : b.adjusted}</strong></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Admin View: Full Employee Management
  return (
    <div className="animate-fade-in">
      <div className="flex-between mb-4" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Employee Directory & Balance Governance</h2>
          <p className="text-muted">Manage company employees, inspect individual leave ledger balances, and perform manual balance adjustments.</p>
        </div>

        <button className="btn btn-primary" onClick={() => setAddModalOpen(true)}>
          <Plus size={16} />
          Add Employee
        </button>
      </div>

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

      {/* Search and Filters */}
      <div className="filter-bar">
        <div style={{ position: 'relative', flex: 1, minWidth: '220px', maxWidth: '340px' }}>
          <input
            type="text"
            className="form-control"
            placeholder="Search by name, ID, or designation..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ paddingLeft: '2.2rem' }}
          />
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span className="text-muted" style={{ fontSize: '0.85rem' }}>Location:</span>
          <select
            className="form-select"
            style={{ width: '130px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
          >
            <option value="ALL">All Locations</option>
            {locations.map((loc) => (
              <option key={loc.location_id} value={loc.location_id}>
                {loc.name} ({loc.location_id})
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span className="text-muted" style={{ fontSize: '0.85rem' }}>Department:</span>
          <select
            className="form-select"
            style={{ width: '140px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
          >
            <option value="ALL">All Departments</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Employees Table */}
      <div className="card">
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Employee Name</th>
                <th>Department & Designation</th>
                <th>Role & Grade</th>
                <th>Location</th>
                <th>Manager</th>
                <th>Joining Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                    No employees matching the current filters.
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((emp) => (
                  <tr key={emp.employee_id}>
                    <td className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 600 }}>{emp.employee_id}</td>
                    <td>
                      <strong>{emp.name}</strong>
                      <div className="text-muted" style={{ fontSize: '0.75rem' }}>{emp.email}</div>
                    </td>
                    <td>
                      <div>{emp.designation}</div>
                      <div className="text-muted" style={{ fontSize: '0.75rem' }}>{emp.department}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', alignItems: 'flex-start' }}>
                        {emp.role === 'HR_ADMIN' ? (
                          <span className="badge badge-postgres">Role: HR Admin</span>
                        ) : emp.role === 'MANAGER' ? (
                          <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                            Role: Manager
                          </span>
                        ) : (
                          <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                            Role: Employee
                          </span>
                        )}
                        <span className="badge badge-grade">Grade: {emp.grade}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-location">{emp.location_id}</span>
                      {emp.country && (
                        <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>{emp.country}</div>
                      )}
                    </td>
                    <td>
                      <div>{emp.manager_name || (emp.role === 'HR_ADMIN' ? '—' : 'None')}</div>
                      {emp.manager_id && (
                        <div className="font-mono text-muted" style={{ fontSize: '0.75rem' }}>{emp.manager_id}</div>
                      )}
                    </td>
                    <td className="font-mono" style={{ fontSize: '0.825rem' }}>{emp.joining_date}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleViewBalances(emp.employee_id)}
                          title="View live leave ledger balances"
                        >
                          <Eye size={13} /> Balances
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => openAdjustModal(emp)}
                          title="Manually adjust leave balance"
                        >
                          <Sliders size={13} /> Adjust
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ color: '#ef4444' }}
                          onClick={() => handleDeleteEmployee(emp.employee_id, emp.name)}
                          title="Delete employee"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* View Balances Modal */}
      {balanceModalOpen && (
        <div className="modal-backdrop" onClick={() => setBalanceModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>Leave Balances Ledger</h3>
                {selectedEmployeeBalances && (
                  <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                    {selectedEmployeeBalances.name} ({selectedEmployeeBalances.employee_id}) &bull; {selectedEmployeeBalances.location_id} Office
                  </p>
                )}
              </div>
              <button className="close-btn" onClick={() => setBalanceModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {balanceLoading ? (
              <p className="text-muted">Loading balances...</p>
            ) : selectedEmployeeBalances?.balances?.length === 0 ? (
              <p className="text-muted">No balances initialized for this employee.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Leave Type</th>
                      <th>Opening</th>
                      <th>Accrued</th>
                      <th>Used</th>
                      <th>Pending Reserved</th>
                      <th>Available</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedEmployeeBalances?.balances?.map((b) => (
                      <tr key={b.leave_type_id}>
                        <td><span className="badge badge-leave">{b.leave_type_name || b.leave_type_id}</span></td>
                        <td>{b.opening_balance}</td>
                        <td className="text-success">+{b.accrued}</td>
                        <td style={{ color: '#ef4444' }}>-{b.used}</td>
                        <td style={{ color: '#fbbf24' }}>{b.pending > 0 ? `-${b.pending}` : '0'}</td>
                        <td><strong style={{ color: '#34d399', fontSize: '1rem' }}>{b.available} Days</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Adjust Balance Modal */}
      {adjustModalOpen && adjustTargetEmp && (
        <div className="modal-backdrop" onClick={() => setAdjustModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>Adjust Leave Balance</h3>
                <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                  {adjustTargetEmp.name} ({adjustTargetEmp.employee_id}) &bull; {adjustTargetEmp.location_id} Office
                </p>
              </div>
              <button className="close-btn" onClick={() => setAdjustModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {adjustError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{adjustError}</span>
              </div>
            )}

            <form onSubmit={handleAdjustBalance}>
              <div className="form-group">
                <label className="form-label">Select Leave Type</label>
                <select
                  className="form-select"
                  value={adjustLeaveTypeId}
                  onChange={(e) => setAdjustLeaveTypeId(e.target.value)}
                  required
                >
                  {selectedEmployeeBalances?.balances?.map((b) => (
                    <option key={b.leave_type_id} value={b.leave_type_id}>
                      {b.leave_type_name || b.leave_type_id} (Currently: {b.available} Days Available)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Days Adjustment (+ to add, - to deduct)</label>
                <input
                  type="number"
                  step="0.5"
                  className="form-control"
                  value={adjustDays}
                  onChange={(e) => setAdjustDays(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Adjustment Reason / Audit Note</label>
                <input
                  type="text"
                  className="form-control"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAdjustModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={adjustLoading}>
                  {adjustLoading ? 'Updating Balance...' : 'Apply Balance Adjustment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Employee Modal */}
      {addModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Employee</h3>
              <button className="close-btn" onClick={() => setAddModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{addError}</span>
              </div>
            )}

            <form onSubmit={handleCreateEmployee}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Employee ID</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. E110"
                    value={newEmployee.employee_id}
                    onChange={(e) => setNewEmployee({ ...newEmployee, employee_id: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Alex Johnson"
                    value={newEmployee.name}
                    onChange={(e) => setNewEmployee({ ...newEmployee, name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Work Email</label>
                <input
                  type="email"
                  className="form-control"
                  placeholder="alex.johnson@example.com"
                  value={newEmployee.email}
                  onChange={(e) => setNewEmployee({ ...newEmployee, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Department</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newEmployee.department}
                    onChange={(e) => setNewEmployee({ ...newEmployee, department: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Designation</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newEmployee.designation}
                    onChange={(e) => setNewEmployee({ ...newEmployee, designation: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Assigned Location</label>
                  <select
                    className="form-select"
                    value={newEmployee.location_id}
                    onChange={(e) => setNewEmployee({ ...newEmployee, location_id: e.target.value })}
                    required
                  >
                    {locations.map((loc) => (
                      <option key={loc.location_id} value={loc.location_id}>
                        {loc.name} ({loc.location_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Grade</label>
                  <select
                    className="form-select"
                    value={newEmployee.grade}
                    onChange={(e) => setNewEmployee({ ...newEmployee, grade: e.target.value })}
                  >
                    <option value="G3">G3</option>
                    <option value="G4">G4</option>
                    <option value="G5">G5</option>
                    <option value="G6">G6</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select
                    className="form-select"
                    value={newEmployee.role}
                    onChange={(e) => setNewEmployee({ ...newEmployee, role: e.target.value })}
                  >
                    <option value="EMPLOYEE">Regular Employee</option>
                    <option value="HR_ADMIN">HR Administrator</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Joining Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={newEmployee.joining_date}
                    onChange={(e) => setNewEmployee({ ...newEmployee, joining_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addLoading}>
                  {addLoading ? 'Saving...' : 'Save Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
