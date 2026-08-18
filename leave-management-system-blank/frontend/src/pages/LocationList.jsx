import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Plus, 
  Calendar, 
  Settings, 
  ShieldCheck, 
  Layers, 
  AlertCircle, 
  CheckCircle2, 
  Trash2, 
  X, 
  RefreshCw, 
  Key, 
  Globe 
} from 'lucide-react';
import { api } from '../api/api';
import { useAuth } from '../context/AuthContext';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function LocationList() {
  const { currentUser, isAdmin } = useAuth();
  const currentYear = new Date().getFullYear();

  const [locations, setLocations] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [accrualPolicies, setAccrualPolicies] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState(currentUser?.location_id || '');
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Add Location modal state
  const [addLocModalOpen, setAddLocModalOpen] = useState(false);
  const [newLocation, setNewLocation] = useState({
    location_id: '',
    name: '',
    city: '',
    state: '',
    country: '',
    weekend_days: [5, 6],
  });
  const [addLocLoading, setAddLocLoading] = useState(false);
  const [addLocError, setAddLocError] = useState(null);

  // Add Leave Type modal state
  const [addLtModalOpen, setAddLtModalOpen] = useState(false);
  const [newLeaveType, setNewLeaveType] = useState({
    leave_type_id: '',
    name: '',
    description: '',
    is_paid: true,
    is_accruable: true,
  });
  const [addLtLoading, setAddLtLoading] = useState(false);
  const [addLtError, setAddLtError] = useState(null);

  // Add Accrual Policy modal state
  const [addPolicyModalOpen, setAddPolicyModalOpen] = useState(false);
  const [newPolicy, setNewPolicy] = useState({
    leave_type_id: '',
    grade: 'G5',
    tenure_from_months: 0,
    monthly_accrual: 1.5,
    max_balance: 30.0,
    carry_forward_limit: 15.0,
  });
  const [addPolicyLoading, setAddPolicyLoading] = useState(false);
  const [addPolicyError, setAddPolicyError] = useState(null);

  // Add Holiday modal state
  const [addHolidayModalOpen, setAddHolidayModalOpen] = useState(false);
  const [newHoliday, setNewHoliday] = useState({
    name: '',
    date: `${currentYear}-01-01`,
    holiday_type: 'PUBLIC',
    description: '',
  });
  const [addHolidayLoading, setAddHolidayLoading] = useState(false);
  const [addHolidayError, setAddHolidayError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [locs, lts, aps, hols] = await Promise.all([
          api.getLocations(),
          api.getLeaveTypes(),
          api.getAccrualPolicies(),
          api.getHolidays(null, selectedYear),
        ]);
        setLocations(locs);
        setLeaveTypes(lts);
        setAccrualPolicies(aps);
        setHolidays(hols);
        if (locs.length > 0 && !selectedLocationId) {
          setSelectedLocationId(locs[0].location_id);
        }
      } else if (currentUser) {
        const targetLocId = currentUser.location_id;
        const [loc, lts, aps, hols] = await Promise.all([
          api.getLocation(targetLocId),
          api.getLeaveTypes(targetLocId),
          api.getAccrualPolicies(targetLocId),
          api.getHolidays(targetLocId, selectedYear),
        ]);
        setLocations(loc ? [loc] : []);
        setLeaveTypes(lts);
        setAccrualPolicies(aps);
        setHolidays(hols);
        setSelectedLocationId(targetLocId);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedYear]);

  // Create Location
  const handleCreateLocation = async (e) => {
    e.preventDefault();
    setAddLocLoading(true);
    setAddLocError(null);
    try {
      await api.createLocation(newLocation);
      setAddLocModalOpen(false);
      setSelectedLocationId(newLocation.location_id.toUpperCase());
      setActionSuccess(`Location ${newLocation.name} (${newLocation.location_id}) created in PostgreSQL!`);
      setTimeout(() => setActionSuccess(null), 4000);
      setNewLocation({
        location_id: '',
        name: '',
        city: '',
        state: '',
        country: '',
        weekend_days: [5, 6],
      });
      await loadData();
    } catch (err) {
      setAddLocError(err.message);
    } finally {
      setAddLocLoading(false);
    }
  };

  // Delete Location
  const handleDeleteLocation = async (locationId, name) => {
    if (!window.confirm(`Delete location ${name} (${locationId}) and all associated policies and leave types?`)) {
      return;
    }
    try {
      await api.deleteLocation(locationId);
      setActionSuccess(`Location ${name} removed.`);
      setTimeout(() => setActionSuccess(null), 4000);
      const remaining = locations.filter(l => l.location_id !== locationId);
      if (remaining.length > 0) {
        setSelectedLocationId(remaining[0].location_id);
      }
      await loadData();
    } catch (err) {
      alert(`Error deleting location: ${err.message}`);
    }
  };

  // Create Leave Type
  const handleCreateLeaveType = async (e) => {
    e.preventDefault();
    setAddLtLoading(true);
    setAddLtError(null);
    try {
      const fullId = `${selectedLocationId}-${newLeaveType.leave_type_id.toUpperCase()}`;
      await api.createLeaveType({
        leave_type_id: fullId,
        location_id: selectedLocationId,
        name: newLeaveType.name.toUpperCase(),
        description: newLeaveType.description,
        is_paid: newLeaveType.is_paid,
        is_accruable: newLeaveType.is_accruable,
      });
      setAddLtModalOpen(false);
      setActionSuccess(`Leave type ${fullId} created successfully!`);
      setTimeout(() => setActionSuccess(null), 4000);
      setNewLeaveType({
        leave_type_id: '',
        name: '',
        description: '',
        is_paid: true,
        is_accruable: true,
      });
      await loadData();
    } catch (err) {
      setAddLtError(err.message);
    } finally {
      setAddLtLoading(false);
    }
  };

  // Delete Leave Type
  const handleDeleteLeaveType = async (leaveTypeId) => {
    if (!window.confirm(`Delete leave type ${leaveTypeId}?`)) return;
    try {
      await api.deleteLeaveType(leaveTypeId);
      setActionSuccess(`Leave type ${leaveTypeId} deleted.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(`Error deleting leave type: ${err.message}`);
    }
  };

  // Create Policy
  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    setAddPolicyLoading(true);
    setAddPolicyError(null);
    try {
      await api.createAccrualPolicy({
        location_id: selectedLocationId,
        leave_type_id: newPolicy.leave_type_id,
        grade: newPolicy.grade === 'ALL' ? null : newPolicy.grade,
        tenure_from_months: parseInt(newPolicy.tenure_from_months, 10),
        monthly_accrual: parseFloat(newPolicy.monthly_accrual),
        max_balance: parseFloat(newPolicy.max_balance),
        carry_forward_limit: parseFloat(newPolicy.carry_forward_limit),
      });
      setAddPolicyModalOpen(false);
      setActionSuccess(`Accrual policy created for ${newPolicy.leave_type_id}!`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      setAddPolicyError(err.message);
    } finally {
      setAddPolicyLoading(false);
    }
  };

  // Delete Policy
  const handleDeletePolicy = async (policyId) => {
    if (!window.confirm(`Delete accrual policy #${policyId}?`)) return;
    try {
      await api.deleteAccrualPolicy(policyId);
      setActionSuccess(`Accrual policy deleted.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(`Error deleting policy: ${err.message}`);
    }
  };

  // Create Holiday
  const handleCreateHoliday = async (e) => {
    e.preventDefault();
    setAddHolidayLoading(true);
    setAddHolidayError(null);
    try {
      await api.createHoliday({
        location_id: selectedLocationId,
        name: newHoliday.name,
        date: newHoliday.date,
        holiday_type: newHoliday.holiday_type,
        description: newHoliday.description,
      });
      setAddHolidayModalOpen(false);
      setActionSuccess(`Holiday "${newHoliday.name}" added to ${selectedLocationId}!`);
      setTimeout(() => setActionSuccess(null), 4000);
      setNewHoliday({
        name: '',
        date: `${selectedYear}-01-01`,
        holiday_type: 'PUBLIC',
        description: '',
      });
      await loadData();
    } catch (err) {
      setAddHolidayError(err.message);
    } finally {
      setAddHolidayLoading(false);
    }
  };

  // Delete Holiday
  const handleDeleteHoliday = async (holidayId, name) => {
    if (!window.confirm(`Delete holiday "${name}"?`)) return;
    try {
      await api.deleteHoliday(holidayId);
      setActionSuccess(`Holiday "${name}" removed.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(`Error deleting holiday: ${err.message}`);
    }
  };

  // Sync Google Calendar Holidays state
  const [syncGoogleModalOpen, setSyncGoogleModalOpen] = useState(false);
  const [googleApiKey, setGoogleApiKey] = useState('');
  const [syncGoogleLoading, setSyncGoogleLoading] = useState(false);
  const [syncGoogleError, setSyncGoogleError] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [syncStatusData, setSyncStatusData] = useState(null);
  const [syncStatusLoading, setSyncStatusLoading] = useState(false);

  const fetchSyncStatus = async (locId, yr) => {
    if (!locId) return;
    setSyncStatusLoading(true);
    try {
      const res = await api.getHolidaySyncStatus(locId, yr);
      setSyncStatusData(res);
    } catch (err) {
      console.warn('Failed to fetch holiday sync status:', err);
    } finally {
      setSyncStatusLoading(false);
    }
  };

  const openSyncModal = () => {
    setSyncGoogleError(null);
    setSyncResult(null);
    fetchSyncStatus(selectedLocationId, selectedYear);
    setSyncGoogleModalOpen(true);
  };

  // Sync Google Calendar Holidays
  const handleSyncGoogle = async (e) => {
    if (e) e.preventDefault();
    setSyncGoogleLoading(true);
    setSyncGoogleError(null);
    setSyncResult(null);
    try {
      const res = await api.syncGoogleHolidays({
        location_id: selectedLocationId,
        year: selectedYear,
        api_key: googleApiKey.trim() || undefined,
      });
      const data = res.data || res;
      setSyncResult(data);
      if (res.status === 'warning' || data.sync_status === 'SYNC_FAILED') {
        setSyncGoogleError(res.message || data.message || 'Google sync returned 0 events. Preserving cached PostgreSQL holidays.');
      } else {
        setActionSuccess(res.message || `Successfully synced ${data.synced_count || 0} holidays from Google Calendar into PostgreSQL!`);
        setTimeout(() => setActionSuccess(null), 5000);
      }
      await fetchSyncStatus(selectedLocationId, selectedYear);
      await loadData();
    } catch (err) {
      setSyncGoogleError(err.message);
    } finally {
      setSyncGoogleLoading(false);
    }
  };

  const selectedLocation = locations.find(l => l.location_id === selectedLocationId) || locations[0];
  const locLeaveTypes = leaveTypes.filter(lt => lt.location_id === selectedLocationId);
  const locPolicies = accrualPolicies.filter(ap => ap.location_id === selectedLocationId);
  const locHolidays = holidays.filter(h => h.location_id === selectedLocationId);

  const formatWeekends = (weekendDays) => {
    if (!weekendDays || weekendDays.length === 0) return 'None';
    return weekendDays.map(d => WEEKDAYS[d]).join(', ');
  };

  return (
    <div className="animate-fade-in">
      <div className="flex-between mb-4" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>{isAdmin ? 'Office Locations & Scoped Policies' : `My Office Location (${selectedLocation?.name || currentUser?.location_id})`}</h2>
          <p className="text-muted">
            {isAdmin 
              ? 'Manage location profiles, configurable weekend rules, leave types, accrual policies, and real-time Google Calendar holidays in PostgreSQL.'
              : `Viewing holiday calendar, weekend schedule, and active leave types for ${selectedLocation?.name || currentUser?.location_id}.`}
          </p>
        </div>

        {isAdmin && (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="btn btn-secondary" onClick={() => setSyncGoogleModalOpen(true)}>
              <Globe size={16} className="text-primary" />
              Sync Google Holidays
            </button>
            <button className="btn btn-primary" onClick={() => setAddLocModalOpen(true)}>
              <Plus size={16} />
              Add Location
            </button>
          </div>
        )}
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

      {/* Location Selector Tabs (Only shown if Admin has multiple, or single badge for employee) */}
      {isAdmin ? (
        <div className="filter-bar mb-4">
          {locations.map((loc) => {
            const isSelected = loc.location_id === selectedLocationId;
            return (
              <button
                key={loc.location_id}
                className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedLocationId(loc.location_id)}
              >
                <MapPin size={16} />
                <span>{loc.name} ({loc.location_id})</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="mb-4">
          <span className="badge badge-location" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
            <MapPin size={14} style={{ display: 'inline', marginRight: '6px' }} />
            Assigned Office: {selectedLocation?.name} ({selectedLocation?.location_id})
          </span>
        </div>
      )}

      {selectedLocation && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
          {/* Location Details & Weekend Rules Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Settings size={20} className="text-primary" />
                <span>Location Profile & Weekend Config</span>
              </div>
              {isAdmin && (
                <button 
                  className="btn btn-secondary btn-sm" 
                  style={{ color: '#ef4444' }}
                  onClick={() => handleDeleteLocation(selectedLocation.location_id, selectedLocation.name)}
                  title="Delete location"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div className="flex-between">
                <span className="text-muted">Location ID:</span>
                <span className="font-mono" style={{ fontWeight: 700 }}>{selectedLocation.location_id}</span>
              </div>
              <div className="flex-between">
                <span className="text-muted">City / Region:</span>
                <span>{selectedLocation.city}, {selectedLocation.state || '—'}</span>
              </div>
              <div className="flex-between">
                <span className="text-muted">Country:</span>
                <span>{selectedLocation.country}</span>
              </div>
              <div className="flex-between">
                <span className="text-muted">Weekend Schedule:</span>
                <span className="badge badge-grade">{formatWeekends(selectedLocation.weekend_days)}</span>
              </div>
            </div>

            <div className="alert alert-info mt-4" style={{ padding: '0.75rem 1rem', fontSize: '0.825rem' }}>
              Working day calculations for employees assigned to this location automatically skip {formatWeekends(selectedLocation.weekend_days)} plus all configured public holidays.
            </div>
          </div>

          {/* Location Leave Types Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Layers size={20} className="text-primary" />
                <span>Available Leave Types</span>
              </div>
              {isAdmin && (
                <button className="btn btn-secondary btn-sm" onClick={() => setAddLtModalOpen(true)}>
                  <Plus size={14} /> Add Type
                </button>
              )}
            </div>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type ID</th>
                    <th>Name</th>
                    <th>Paid</th>
                    <th>Accruable</th>
                    {isAdmin && <th>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {locLeaveTypes.length === 0 ? (
                    <tr>
                      <td colSpan={isAdmin ? "5" : "4"} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                        No leave types yet for this location.
                      </td>
                    </tr>
                  ) : (
                    locLeaveTypes.map((lt) => (
                      <tr key={lt.leave_type_id}>
                        <td className="font-mono" style={{ fontSize: '0.8rem' }}>{lt.leave_type_id}</td>
                        <td><strong>{lt.name}</strong></td>
                        <td>{lt.is_paid ? 'Yes' : 'No'}</td>
                        <td>{lt.is_accruable ? <span className="badge badge-approved">Yes</span> : 'No'}</td>
                        {isAdmin && (
                          <td>
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ color: '#ef4444', padding: '0.2rem 0.4rem' }}
                              onClick={() => handleDeleteLeaveType(lt.leave_type_id)}
                              title="Delete leave type"
                            >
                              <Trash2 size={12} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Location Accrual Policies Card */}
          <div className="card" style={{ gridColumn: 'span 2' }}>
            <div className="card-header">
              <div className="card-title">
                <ShieldCheck size={20} className="text-primary" />
                <span>Deterministic Accrual Policies</span>
              </div>
              {isAdmin && (
                <button 
                  className="btn btn-secondary btn-sm" 
                  onClick={() => {
                    if (locLeaveTypes.length > 0) {
                      setNewPolicy(prev => ({ ...prev, leave_type_id: locLeaveTypes[0].leave_type_id }));
                    }
                    setAddPolicyModalOpen(true);
                  }}
                >
                  <Plus size={14} /> Add Policy
                </button>
              )}
            </div>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Leave Type</th>
                    <th>Applicable Grade</th>
                    <th>Min Tenure</th>
                    <th>Monthly Accrual</th>
                    <th>Max Balance Cap</th>
                    <th>Carry Forward Limit</th>
                    {isAdmin && <th>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {locPolicies.length === 0 ? (
                    <tr>
                      <td colSpan={isAdmin ? "7" : "6"} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                        No accrual policies configured for this location.
                      </td>
                    </tr>
                  ) : (
                    locPolicies.map((p) => (
                      <tr key={p.policy_id}>
                        <td><span className="badge badge-leave">{p.leave_type_id}</span></td>
                        <td>{p.grade ? <span className="badge badge-grade">{p.grade}</span> : <span className="text-muted">All Grades</span>}</td>
                        <td>{p.tenure_from_months} months</td>
                        <td><strong>+{p.monthly_accrual} days / mo</strong></td>
                        <td><span className="badge badge-location">{p.max_balance} days max</span></td>
                        <td>{p.carry_forward_limit} days</td>
                        {isAdmin && (
                          <td>
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ color: '#ef4444', padding: '0.2rem 0.4rem' }}
                              onClick={() => handleDeletePolicy(p.policy_id)}
                              title="Delete policy"
                            >
                              <Trash2 size={12} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Location Holidays Card */}
          <div className="card" style={{ gridColumn: 'span 2' }}>
            <div className="card-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
              <div className="card-title">
                <Calendar size={20} className="text-primary" />
                <span>Location Public Holidays ({selectedYear})</span>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {isAdmin && (
                  <button 
                    className="btn btn-secondary btn-sm"
                    onClick={openSyncModal}
                    style={{ color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.4)' }}
                  >
                    <Globe size={14} /> Google Calendar Status
                  </button>
                )}

                <select
                  className="form-select"
                  style={{ width: '100px', padding: '0.3rem 0.5rem', fontSize: '0.85rem' }}
                  value={selectedYear}
                  onChange={(e) => {
                    const yr = parseInt(e.target.value, 10);
                    setSelectedYear(yr);
                    fetchSyncStatus(selectedLocationId, yr);
                  }}
                >
                  {[currentYear - 1, currentYear, currentYear + 1, currentYear + 2].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>

                {isAdmin && (
                  <button 
                    className="btn btn-secondary btn-sm" 
                    onClick={() => {
                      setNewHoliday({
                        name: '',
                        date: `${selectedYear}-01-01`,
                        holiday_type: 'PUBLIC',
                        description: '',
                      });
                      setAddHolidayModalOpen(true);
                    }}
                  >
                    <Plus size={14} /> Add Manual
                  </button>
                )}
              </div>
            </div>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Holiday Name</th>
                    <th>Calendar Date</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th>Description</th>
                    {isAdmin && <th>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {locHolidays.length === 0 ? (
                    <tr>
                      <td colSpan={isAdmin ? "6" : "5"} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                        No holidays configured for year {selectedYear} at {selectedLocation.name}.
                      </td>
                    </tr>
                  ) : (
                    locHolidays.map((h) => (
                      <tr key={h.holiday_id}>
                        <td><strong>{h.name}</strong></td>
                        <td className="font-mono">{h.date}</td>
                        <td><span className="badge badge-leave">{h.type || 'PUBLIC'}</span></td>
                        <td>
                          {h.source === 'GOOGLE' ? (
                            <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                              <Globe size={11} /> Google
                            </span>
                          ) : (
                            <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)' }}>
                              Manual
                            </span>
                          )}
                        </td>
                        <td className="text-muted">{h.description || '—'}</td>
                        {isAdmin && (
                          <td>
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ color: '#ef4444', padding: '0.2rem 0.4rem' }}
                              onClick={() => handleDeleteHoliday(h.holiday_id, h.name)}
                              title="Delete holiday"
                            >
                              <Trash2 size={12} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Sync Google Calendar Modal */}
      {syncGoogleModalOpen && (
        <div className="modal-backdrop" onClick={() => setSyncGoogleModalOpen(false)}>
          <div className="modal-content" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Globe size={20} className="text-primary" />
                <h3>Google Calendar Holiday Synchronization</h3>
              </div>
              <button className="close-btn" onClick={() => setSyncGoogleModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {syncGoogleError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{syncGoogleError}</span>
              </div>
            )}

            {syncResult && syncResult.sync_status === 'SYNCED' && syncResult.synced_count > 0 && (
              <div className="alert alert-success mb-3" style={{ fontSize: '0.85rem' }}>
                <Check size={16} />
                <div>
                  <strong>Sync Successful!</strong>
                  <div style={{ marginTop: '0.25rem' }}>
                    Google Events Returned: <strong>{syncResult.synced_count}</strong> &bull; Total Holidays in PostgreSQL: <strong>{syncResult.total_holidays}</strong>
                  </div>
                  <div style={{ fontSize: '0.8rem', opacity: 0.85, marginTop: '0.25rem' }}>{syncResult.message}</div>
                </div>
              </div>
            )}

            {syncResult && (syncResult.sync_status === 'SYNC_FAILED' || syncResult.synced_count === 0) && (
              <div className="alert alert-danger mb-3" style={{ fontSize: '0.85rem' }}>
                <AlertCircle size={16} />
                <div>
                  <strong>Sync Notice: 0 Events Imported</strong>
                  <div style={{ marginTop: '0.25rem' }}>
                    {syncResult.message || syncStatusData?.error_message || 'Google Calendar returned no events for this location and year.'}
                  </div>
                  <div style={{ marginTop: '0.4rem', color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <Shield size={13} />
                    <span>Safely using <strong>{syncResult.total_holidays ?? syncStatusData?.holiday_count ?? locHolidays.length}</strong> cached PostgreSQL holidays.</span>
                  </div>
                </div>
              </div>
            )}

            {!syncResult && syncStatusData?.error_message && (
              <div className="alert alert-warning mb-3" style={{ fontSize: '0.825rem' }}>
                <AlertCircle size={14} />
                <span>{syncStatusData.error_message}</span>
              </div>
            )}

            <div className="card mb-3" style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
                <div>
                  <span className="text-muted">Target Location:</span>
                  <div style={{ fontWeight: 600 }}>{selectedLocation?.name} ({selectedLocation?.country})</div>
                </div>
                <div>
                  <span className="text-muted">Calendar Year:</span>
                  <div style={{ fontWeight: 600 }}>{selectedYear}</div>
                </div>
                <div>
                  <span className="text-muted">Calendar Feed:</span>
                  <div style={{ fontWeight: 600, color: '#818cf8' }}>
                    {syncStatusData?.calendar_name || `${selectedLocation?.country} Public Holidays`}
                  </div>
                </div>
                <div>
                  <span className="text-muted">Sync Status:</span>
                  <div>
                    {syncStatusData?.sync_status === 'SYNCED' ? (
                      <span className="badge badge-approved" style={{ fontSize: '0.75rem' }}>
                        <Check size={11} /> Connected & Synced
                      </span>
                    ) : syncStatusData?.sync_status === 'USING_CACHED' ? (
                      <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)', fontSize: '0.75rem' }}>
                        <Shield size={11} /> PostgreSQL Operational Cache
                      </span>
                    ) : syncStatusData?.sync_status === 'SYNC_FAILED' ? (
                      <span className="badge badge-danger" style={{ fontSize: '0.75rem' }}>
                        Sync Notice
                      </span>
                    ) : (
                      <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)', fontSize: '0.75rem' }}>
                        Ready to Sync
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <span className="text-muted">Last Synced:</span>
                  <div style={{ fontSize: '0.8rem' }}>
                    {syncStatusData?.last_synced_at 
                      ? new Date(syncStatusData.last_synced_at).toLocaleString() 
                      : 'Using operational seed cache'}
                  </div>
                </div>
                <div>
                  <span className="text-muted">Holidays in PostgreSQL:</span>
                  <div style={{ fontWeight: 700, color: '#34d399' }}>
                    {syncStatusData?.holiday_count ?? locHolidays.length} Public Holidays
                  </div>
                </div>
              </div>
              
              {syncStatusData?.calendar_id && (
                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <strong>Calendar ID:</strong> <code>{syncStatusData.calendar_id}</code>
                </div>
              )}
            </div>

            <p className="text-muted mb-3" style={{ fontSize: '0.825rem' }}>
              Google Calendar API v3 synchronizes public holiday feeds into PostgreSQL. The local PostgreSQL table acts as the authoritative operational cache, guaranteeing deterministic working-day calculations even when external network connectivity is unavailable.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setSyncGoogleModalOpen(false)}>
                Close
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={handleSyncGoogle}
                disabled={syncGoogleLoading}
              >
                <RefreshCw size={16} className={syncGoogleLoading ? 'animate-spin' : ''} />
                {syncGoogleLoading ? 'Syncing with Google...' : 'Force Refresh from Google'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Location Modal */}
      {addLocModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddLocModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Location</h3>
              <button className="close-btn" onClick={() => setAddLocModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addLocError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{addLocError}</span>
              </div>
            )}

            <form onSubmit={handleCreateLocation}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Location Code / ID</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. LON"
                    value={newLocation.location_id}
                    onChange={(e) => setNewLocation({ ...newLocation, location_id: e.target.value.toUpperCase() })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Location Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. London Office"
                    value={newLocation.name}
                    onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">City</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. London"
                    value={newLocation.city}
                    onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">State / Region</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Greater London"
                    value={newLocation.state}
                    onChange={(e) => setNewLocation({ ...newLocation, state: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Country</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. United Kingdom"
                  value={newLocation.country}
                  onChange={(e) => setNewLocation({ ...newLocation, country: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Weekend Schedule</label>
                <select
                  className="form-select"
                  value={JSON.stringify(newLocation.weekend_days)}
                  onChange={(e) => setNewLocation({ ...newLocation, weekend_days: JSON.parse(e.target.value) })}
                >
                  <option value="[5,6]">Saturday & Sunday (Standard)</option>
                  <option value="[4,5]">Friday & Saturday (Middle East)</option>
                  <option value="[4,6]">Friday & Sunday</option>
                  <option value="[6]">Sunday Only</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddLocModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addLocLoading}>
                  {addLocLoading ? 'Saving...' : 'Save Location'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Leave Type Modal */}
      {addLtModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddLtModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Leave Type for {selectedLocation.name}</h3>
              <button className="close-btn" onClick={() => setAddLtModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addLtError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{addLtError}</span>
              </div>
            )}

            <form onSubmit={handleCreateLeaveType}>
              <div className="form-group">
                <label className="form-label">Leave Type Code / Suffix (e.g. PTO, SICK, MATERNITY)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. PARENTAL"
                  value={newLeaveType.leave_type_id}
                  onChange={(e) => setNewLeaveType({ ...newLeaveType, leave_type_id: e.target.value })}
                  required
                />
                <small className="text-muted">Will be registered with ID: <code>{selectedLocationId}-{newLeaveType.leave_type_id.toUpperCase() || 'CODE'}</code></small>
              </div>

              <div className="form-group">
                <label className="form-label">Display Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Parental Leave"
                  value={newLeaveType.name}
                  onChange={(e) => setNewLeaveType({ ...newLeaveType, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Paid leave for new parents"
                  value={newLeaveType.description}
                  onChange={(e) => setNewLeaveType({ ...newLeaveType, description: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="is_paid"
                    checked={newLeaveType.is_paid}
                    onChange={(e) => setNewLeaveType({ ...newLeaveType, is_paid: e.target.checked })}
                  />
                  <label htmlFor="is_paid" className="form-label" style={{ margin: 0 }}>Is Paid Leave</label>
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="is_accruable"
                    checked={newLeaveType.is_accruable}
                    onChange={(e) => setNewLeaveType({ ...newLeaveType, is_accruable: e.target.checked })}
                  />
                  <label htmlFor="is_accruable" className="form-label" style={{ margin: 0 }}>Is Accruable Monthly</label>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddLtModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addLtLoading}>
                  {addLtLoading ? 'Saving...' : 'Save Leave Type'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Accrual Policy Modal */}
      {addPolicyModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddPolicyModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Accrual Policy for {selectedLocation.name}</h3>
              <button className="close-btn" onClick={() => setAddPolicyModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addPolicyError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{addPolicyError}</span>
              </div>
            )}

            <form onSubmit={handleCreatePolicy}>
              <div className="form-group">
                <label className="form-label">Leave Type</label>
                <select
                  className="form-select"
                  value={newPolicy.leave_type_id}
                  onChange={(e) => setNewPolicy({ ...newPolicy, leave_type_id: e.target.value })}
                  required
                >
                  {locLeaveTypes.map(lt => (
                    <option key={lt.leave_type_id} value={lt.leave_type_id}>
                      {lt.name} ({lt.leave_type_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Applicable Grade</label>
                  <select
                    className="form-select"
                    value={newPolicy.grade}
                    onChange={(e) => setNewPolicy({ ...newPolicy, grade: e.target.value })}
                  >
                    <option value="ALL">All Grades (Default)</option>
                    <option value="G3">G3</option>
                    <option value="G4">G4</option>
                    <option value="G5">G5</option>
                    <option value="G6">G6</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Min Tenure (Months)</label>
                  <input
                    type="number"
                    min="0"
                    className="form-control"
                    value={newPolicy.tenure_from_months}
                    onChange={(e) => setNewPolicy({ ...newPolicy, tenure_from_months: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Monthly Accrual (Days)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    className="form-control"
                    value={newPolicy.monthly_accrual}
                    onChange={(e) => setNewPolicy({ ...newPolicy, monthly_accrual: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Max Balance Cap (Days)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    className="form-control"
                    value={newPolicy.max_balance}
                    onChange={(e) => setNewPolicy({ ...newPolicy, max_balance: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Carry Forward Limit (Days)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  className="form-control"
                  value={newPolicy.carry_forward_limit}
                  onChange={(e) => setNewPolicy({ ...newPolicy, carry_forward_limit: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddPolicyModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addPolicyLoading || locLeaveTypes.length === 0}>
                  {addPolicyLoading ? 'Saving...' : 'Save Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Holiday Modal */}
      {addHolidayModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddHolidayModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Holiday for {selectedLocation.name}</h3>
              <button className="close-btn" onClick={() => setAddHolidayModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {addHolidayError && (
              <div className="alert alert-danger mb-3">
                <AlertCircle size={16} />
                <span>{addHolidayError}</span>
              </div>
            )}

            <form onSubmit={handleCreateHoliday}>
              <div className="form-group">
                <label className="form-label">Holiday Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Summer Bank Holiday"
                  value={newHoliday.name}
                  onChange={(e) => setNewHoliday({ ...newHoliday, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={newHoliday.date}
                    onChange={(e) => setNewHoliday({ ...newHoliday, date: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Holiday Type</label>
                  <select
                    className="form-select"
                    value={newHoliday.holiday_type}
                    onChange={(e) => setNewHoliday({ ...newHoliday, holiday_type: e.target.value })}
                  >
                    <option value="PUBLIC">Public Holiday</option>
                    <option value="REGIONAL">Regional Holiday</option>
                    <option value="COMPANY">Company Holiday</option>
                    <option value="OPTIONAL">Optional / Floating</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. National holiday"
                  value={newHoliday.description}
                  onChange={(e) => setNewHoliday({ ...newHoliday, description: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddHolidayModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addHolidayLoading}>
                  {addHolidayLoading ? 'Saving...' : 'Save Holiday'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
