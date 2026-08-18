import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Plus, 
  Calendar, 
  Settings, 
  ShieldCheck, 
  Layers, 
  AlertCircle, 
  X 
} from 'lucide-react';
import { api } from '../api/api';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function LocationList() {
  const [locations, setLocations] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [accrualPolicies, setAccrualPolicies] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState('BLR');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add Location modal state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newLocation, setNewLocation] = useState({
    location_id: '',
    name: '',
    city: '',
    state: '',
    country: '',
    weekend_days: [5, 6],
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [locs, lts, aps, hols] = await Promise.all([
        api.getLocations(),
        api.getLeaveTypes(),
        api.getAccrualPolicies(),
        api.getHolidays(null, 2026),
      ]);
      setLocations(locs);
      setLeaveTypes(lts);
      setAccrualPolicies(aps);
      setHolidays(hols);
      if (locs.length > 0 && !selectedLocationId) {
        setSelectedLocationId(locs[0].location_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateLocation = async (e) => {
    e.preventDefault();
    setAddLoading(true);
    setAddError(null);
    try {
      await api.createLocation(newLocation);
      setAddModalOpen(false);
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
      setAddError(err.message);
    } finally {
      setAddLoading(false);
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
      <div className="flex-between mb-4">
        <div>
          <h2>Office Locations & Scoped Policies</h2>
          <p className="text-muted">Explore location-specific weekend rules, available leave types, accrual rates, and holidays.</p>
        </div>

        <button className="btn btn-primary" onClick={() => setAddModalOpen(true)}>
          <Plus size={16} />
          Add Location
        </button>
      </div>

      {error && (
        <div className="alert alert-danger">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Location Selector Tabs */}
      <div className="filter-bar">
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

      {selectedLocation && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
          {/* Location Details & Weekend Rules Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Settings size={20} className="text-primary" />
                <span>Location Profile & Weekend Config</span>
              </div>
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
                <span className="text-muted">Weekend Configuration:</span>
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
              <span className="badge badge-leave">{locLeaveTypes.length} Types</span>
            </div>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type ID</th>
                    <th>Name</th>
                    <th>Paid</th>
                    <th>Accruable</th>
                  </tr>
                </thead>
                <tbody>
                  {locLeaveTypes.map((lt) => (
                    <tr key={lt.leave_type_id}>
                      <td className="font-mono" style={{ fontSize: '0.8rem' }}>{lt.leave_type_id}</td>
                      <td><strong>{lt.name}</strong></td>
                      <td>{lt.is_paid ? 'Yes' : 'No'}</td>
                      <td>{lt.is_accruable ? <span className="badge badge-approved">Yes</span> : 'No'}</td>
                    </tr>
                  ))}
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
              <span className="badge badge-grade">Deterministic Engine</span>
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
                  </tr>
                </thead>
                <tbody>
                  {locPolicies.map((p) => (
                    <tr key={p.policy_id}>
                      <td><span className="badge badge-leave">{p.leave_type_id}</span></td>
                      <td>{p.grade ? <span className="badge badge-grade">{p.grade}</span> : <span className="text-muted">All Grades</span>}</td>
                      <td>{p.tenure_from_months} months</td>
                      <td><strong>+{p.monthly_accrual} days / month</strong></td>
                      <td><span className="badge badge-location">{p.max_balance} days max</span></td>
                      <td>{p.carry_forward_limit} days</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Add Location Modal */}
      {addModalOpen && (
        <div className="modal-backdrop" onClick={() => setAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Location</h3>
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

            <form onSubmit={handleCreateLocation}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Location Code / ID</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. SYD"
                    value={newLocation.location_id}
                    onChange={(e) => setNewLocation({ ...newLocation, location_id: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Location Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Sydney Office"
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
                    placeholder="e.g. Sydney"
                    value={newLocation.city}
                    onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">State / Province</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. NSW"
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
                  placeholder="e.g. Australia"
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
                  <option value="[4,5]">Friday & Saturday (Middle East / UAE Demo)</option>
                  <option value="[4,6]">Friday & Sunday</option>
                  <option value="[6]">Sunday Only</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setAddModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addLoading}>
                  {addLoading ? 'Creating...' : 'Save Location'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
