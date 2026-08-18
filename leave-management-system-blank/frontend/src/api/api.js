const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const token = localStorage.getItem('lms_token');
  const savedUser = localStorage.getItem('lms_user');
  let currentUser = null;
  try {
    currentUser = savedUser ? JSON.parse(savedUser) : null;
  } catch (e) {}

  const authHeaders = {};
  if (token) {
    authHeaders['Authorization'] = `Bearer ${token}`;
  }
  if (currentUser?.employee_id) {
    authHeaders['X-Employee-ID'] = currentUser.employee_id;
  }
  if (currentUser?.email) {
    authHeaders['X-User-Email'] = currentUser.email;
  }

  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...authHeaders,
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
  // Auth
  login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  getPersonas: () => request('/auth/personas'),

  // Health & Admin
  checkHealth: () => request('/health'),
  triggerSeed: () => request('/seed', { method: 'POST' }),

  // Employees
  getEmployees: () => request('/employees'),
  getEmployee: (id) => request(`/employees/${id}`),
  createEmployee: (payload) => request('/employees', { method: 'POST', body: JSON.stringify(payload) }),
  updateEmployee: (id, payload) => request(`/employees/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteEmployee: (id) => request(`/employees/${id}`, { method: 'DELETE' }),
  getEmployeeBalances: (id) => request(`/employees/${id}/balance`),
  adjustEmployeeBalance: (id, payload) => request(`/employees/${id}/adjust-balance`, { method: 'POST', body: JSON.stringify(payload) }),

  // Locations
  getLocations: () => request('/locations'),
  getLocation: (id) => request(`/locations/${id}`),
  createLocation: (payload) => request('/locations', { method: 'POST', body: JSON.stringify(payload) }),
  updateLocation: (id, payload) => request(`/locations/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteLocation: (id) => request(`/locations/${id}`, { method: 'DELETE' }),

  // Leave Types
  getLeaveTypes: (locationId) => request(`/leave-types${locationId ? `?location_id=${locationId}` : ''}`),
  getLeaveType: (id) => request(`/leave-types/${id}`),
  createLeaveType: (payload) => request('/leave-types', { method: 'POST', body: JSON.stringify(payload) }),
  updateLeaveType: (id, payload) => request(`/leave-types/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteLeaveType: (id) => request(`/leave-types/${id}`, { method: 'DELETE' }),

  // Holidays
  getHolidays: (locationId, year) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (year) params.append('year', year);
    const qs = params.toString();
    return request(`/holidays${qs ? `?${qs}` : ''}`);
  },
  getHoliday: (id) => request(`/holidays/${id}`),
  createHoliday: (payload) => request('/holidays', { method: 'POST', body: JSON.stringify(payload) }),
  updateHoliday: (id, payload) => request(`/holidays/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteHoliday: (id) => request(`/holidays/${id}`, { method: 'DELETE' }),
  syncGoogleHolidays: (payload) => request('/holidays/sync-google', { method: 'POST', body: JSON.stringify(payload) }),
  getHolidaySyncStatus: (locationId, year) => request(`/holidays/sync-status?location_id=${encodeURIComponent(locationId)}${year ? `&year=${year}` : ''}`),
  getGoogleStatus: () => request('/holidays/google-status'),

  // Accrual Policies
  getAccrualPolicies: (locationId, leaveTypeId) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (leaveTypeId) params.append('leave_type_id', leaveTypeId);
    const qs = params.toString();
    return request(`/accrual-policies${qs ? `?${qs}` : ''}`);
  },
  getAccrualPolicy: (id) => request(`/accrual-policies/${id}`),
  createAccrualPolicy: (payload) => request('/accrual-policies', { method: 'POST', body: JSON.stringify(payload) }),
  updateAccrualPolicy: (id, payload) => request(`/accrual-policies/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteAccrualPolicy: (id) => request(`/accrual-policies/${id}`, { method: 'DELETE' }),
  runAccrual: (payload = {}) => request('/accrual/run', { method: 'POST', body: JSON.stringify(payload) }),

  // Leave Requests & Multi-Tier Approvals
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
  approveLeaveRequest: (id) => request(`/leave-requests/${id}/approve`, { method: 'PUT' }),
  rejectLeaveRequest: (id) => request(`/leave-requests/${id}/reject`, { method: 'PUT' }),
  deleteLeaveRequest: (id) => request(`/leave-requests/${id}`, { method: 'DELETE' }),

  // Multi-Tier Approvals & Outbox
  getPendingApprovals: (approverId, isAdmin = false) => {
    const params = new URLSearchParams();
    if (approverId) params.append('approver_id', approverId);
    if (isAdmin) params.append('is_admin', 'true');
    const qs = params.toString();
    return request(`/approvals/pending${qs ? `?${qs}` : ''}`);
  },
  getApprovalHistory: (leaveRequestId) => request(`/approvals/history/${leaveRequestId}`),
  approveApprovalStep: (approvalId, approverId, comments = 'Approved') =>
    request(`/approvals/${approvalId}/approve?approver_id=${encodeURIComponent(approverId)}`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    }),
  rejectApprovalStep: (approvalId, approverId, comments) =>
    request(`/approvals/${approvalId}/reject?approver_id=${encodeURIComponent(approverId)}`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    }),
  approveTier: (requestId, approverId, comments = 'Approved') => 
    request(`/leave-requests/${requestId}/approve-tier?approver_id=${encodeURIComponent(approverId)}`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    }),
  rejectTier: (requestId, approverId, comments) => 
    request(`/leave-requests/${requestId}/reject-tier?approver_id=${encodeURIComponent(approverId)}`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    }),
  getNotificationOutbox: (limit = 50, employeeId = null) => {
    const params = new URLSearchParams({ limit });
    if (employeeId) params.append('employee_id', employeeId);
    return request(`/leave-requests/notifications/outbox?${params.toString()}`);
  },
  clearNotificationOutbox: (employeeId = null) => {
    const params = new URLSearchParams();
    if (employeeId) params.append('employee_id', employeeId);
    return request(`/leave-requests/notifications/outbox?${params.toString()}`, {
      method: 'DELETE',
    });
  },
  sendTestEmail: (toEmail) =>
    request('/leave-requests/notifications/test-email', {
      method: 'POST',
      body: JSON.stringify({ to_email: toEmail }),
    }),
  retryNotification: (notificationId) =>
    request(`/leave-requests/notifications/${notificationId}/retry`, {
      method: 'POST',
    }),
  getEmailStatus: () => request('/leave-requests/notifications/email-status'),
};
