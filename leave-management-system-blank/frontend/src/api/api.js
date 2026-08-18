const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || `API Request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Health
  checkHealth: () => request('/health'),
  triggerSeed: () => request('/seed', { method: 'POST' }),

  // Employees
  getEmployees: () => request('/employees'),
  getEmployee: (id) => request(`/employees/${id}`),
  createEmployee: (payload) => request('/employees', { method: 'POST', body: JSON.stringify(payload) }),
  getEmployeeBalances: (id) => request(`/employees/${id}/balance`),

  // Locations
  getLocations: () => request('/locations'),
  getLocation: (id) => request(`/locations/${id}`),
  createLocation: (payload) => request('/locations', { method: 'POST', body: JSON.stringify(payload) }),

  // Leave Types
  getLeaveTypes: (locationId) => request(`/leave-types${locationId ? `?location_id=${locationId}` : ''}`),
  createLeaveType: (payload) => request('/leave-types', { method: 'POST', body: JSON.stringify(payload) }),

  // Holidays
  getHolidays: (locationId, year) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (year) params.append('year', year);
    const qs = params.toString();
    return request(`/holidays${qs ? `?${qs}` : ''}`);
  },
  createHoliday: (payload) => request('/holidays', { method: 'POST', body: JSON.stringify(payload) }),

  // Accrual Policies
  getAccrualPolicies: (locationId, leaveTypeId) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (leaveTypeId) params.append('leave_type_id', leaveTypeId);
    const qs = params.toString();
    return request(`/accrual-policies${qs ? `?${qs}` : ''}`);
  },
  createAccrualPolicy: (payload) => request('/accrual-policies', { method: 'POST', body: JSON.stringify(payload) }),
  runAccrual: (payload = {}) => request('/accrual/run', { method: 'POST', body: JSON.stringify(payload) }),

  // Leave Requests
  previewLeave: (payload) => request('/leave-requests/preview', { method: 'POST', body: JSON.stringify(payload) }),
  createLeaveRequest: (payload) => request('/leave-requests', { method: 'POST', body: JSON.stringify(payload) }),
  getLeaveRequests: (employeeId, status) => {
    const params = new URLSearchParams();
    if (employeeId) params.append('employee_id', employeeId);
    if (status) params.append('status', status);
    const qs = params.toString();
    return request(`/leave-requests${qs ? `?${qs}` : ''}`);
  },
  getLeaveRequest: (id) => request(`/leave-requests/${id}`),
  cancelLeaveRequest: (id) => request(`/leave-requests/${id}/cancel`, { method: 'PUT' }),
};
