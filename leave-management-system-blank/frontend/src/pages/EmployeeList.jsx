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
  Award 
} from 'lucide-react';
import { api } from '../api/api';

export default function EmployeeList() {
  const [employees, setEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Balance modal state
  const [selectedEmployeeBalances, setSelectedEmployeeBalances] = useState(null);
  const [balanceModalOpen, setBalanceModalOpen] = useState(false);
  const [balanceLoading, setBalanceLoading] = useState(false);

  // Add Employee Modal state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    employee_id: '',
    name: '',
    email: '',
    department: 'Engineering',
    designation: 'Software Engineer',
    grade: 'G5',
    location_id: 'BLR',
    joining_date: '2025-01-01',
    status: 'ACTIVE',
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState(null);

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const [emps, locs] = await Promise.all([
        api.getEmployees(),
        api.getLocations(),
      ]);
      setEmployees(emps);
      setLocations(locs);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, []);

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

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    setAddLoading(true);
    setAddError(null);
    try {
      await api.createEmployee(newEmployee);
      setAddModalOpen(false);
      setNewEmployee({
        employee_id: '',
        name: '',
        email: '',
        department: 'Engineering',
        designation: 'Software Engineer',
        grade: 'G5',
        location_id: 'BLR',
        joining_date: '2025-01-01',
        status: 'ACTIVE',
      });
      await loadEmployees();
    } catch (err) {
      setAddError(err.message);
    } finally {
      setAddLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex-between mb-4">
        <div>
          <h2>Employee Directory & Balances</h2>
          <p className="text-muted">Manage global employees and view location-scoped leave balance allocations.</p>
        </div>

        <button className="btn btn-primary" onClick={() => setAddModalOpen(true)}>
          <Plus size={16} />
          Add Employee
        </button>
      </div>

      {error && (
        <div className="alert alert-danger">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Employees Table */}
      <div className="card">
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Name & Email</th>
                <th>Department</th>
                <th>Designation</th>
                <th>Grade</th>
                <th>Location</th>
                <th>Joining Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.employee_id}>
                  <td className="font-mono" style={{ fontWeight: 600 }}>{emp.employee_id}</td>
                  <td>
                    <div><strong>{emp.name}</strong></div>
                    <div className="text-muted" style={{ fontSize: '0.8rem' }}>{emp.email}</div>
                  </td>
                  <td>{emp.department}</td>
                  <td>{emp.designation}</td>
                  <td><span className="badge badge-grade">{emp.grade}</span></td>
                  <td><span className="badge badge-location">{emp.location_id}</span></td>
                  <td>{emp.joining_date}</td>
                  <td><span className="badge badge-approved">{emp.status}</span></td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleViewBalances(emp.employee_id)}
                      title="View detailed leave balance breakdowns"
                    >
                      <Eye size={14} />
                      Balances
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Balance Breakdown Modal */}
      {balanceModalOpen && (
        <div className="modal-backdrop" onClick={() => setBalanceModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                Leave Balances for {selectedEmployeeBalances?.employee_name || 'Employee'}
                <span className="text-muted" style={{ fontSize: '0.9rem', marginLeft: '0.5rem' }}>
                  ({selectedEmployeeBalances?.employee_id})
                </span>
              </h3>
              <button className="close-btn" onClick={() => setBalanceModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {balanceLoading ? (
              <p className="text-muted" style={{ padding: '1.5rem', textAlign: 'center' }}>Loading balance details...</p>
            ) : (
              <div>
                <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
                  <span className="badge badge-location">Location: {selectedEmployeeBalances?.location_id}</span>
                  <span className="badge badge-grade">Deterministic Engine</span>
                </div>

                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Leave Type</th>
                        <th>Opening</th>
                        <th>Accrued</th>
                        <th>Used</th>
                        <th>Pending (Reserved)</th>
                        <th>Available</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedEmployeeBalances?.balances?.map((bal) => (
                        <tr key={bal.leave_type_id}>
                          <td><strong>{bal.leave_type_name}</strong></td>
                          <td>{bal.opening_balance.toFixed(1)}</td>
                          <td>+{bal.accrued.toFixed(1)}</td>
                          <td className="text-danger">-{bal.used.toFixed(1)}</td>
                          <td>
                            {bal.pending > 0 ? (
                              <span className="badge badge-pending">{bal.pending.toFixed(1)} reserved</span>
                            ) : (
                              '0.0'
                            )}
                          </td>
                          <td>
                            <strong className="text-success" style={{ fontSize: '1.1rem' }}>
                              {bal.available.toFixed(1)}
                            </strong>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => setBalanceModalOpen(false)}>
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Employee Modal */}
      {addModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Employee</h3>
              <button className="close-btn" onClick={() => setAddModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addError && (
              <div className="alert alert-danger">
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
                    placeholder="e.g. E105"
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
                    placeholder="e.g. David Brown"
                    value={newEmployee.name}
                    onChange={(e) => setNewEmployee({ ...newEmployee, name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="form-control"
                  placeholder="e.g. david.brown@example.com"
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
                  <label className="form-label">Grade</label>
                  <select
                    className="form-select"
                    value={newEmployee.grade}
                    onChange={(e) => setNewEmployee({ ...newEmployee, grade: e.target.value })}
                    required
                  >
                    <option value="G3">G3</option>
                    <option value="G4">G4</option>
                    <option value="G5">G5</option>
                    <option value="G6">G6</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Location</label>
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addLoading}>
                  {addLoading ? 'Creating...' : 'Save Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
