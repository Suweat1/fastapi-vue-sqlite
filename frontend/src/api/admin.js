import client from './client.js'

export const listUsersApi = () => client.get('/admin/users').then((r) => r.data)
export const updateUserRoleApi = (id, payload) => client.patch(`/admin/users/${id}/role`, payload).then((r) => r.data)
export const listAdminItemsApi = (params) => client.get('/admin/items', { params }).then((r) => r.data)
export const updateItemStatusApi = (id, payload) => client.patch(`/admin/items/${id}/status`, payload).then((r) => r.data)
export const batchUpdateItemsApi = (payload) => client.post('/admin/items/batch', payload).then((r) => r.data)
export const dashboardStatsApi = () => client.get('/stats/dashboard').then((r) => r.data)
export const priceStatsApi = () => client.get('/stats/prices').then((r) => r.data)
export const downloadDashboardReportApi = () =>
  client.get('/admin/dashboard/export', { responseType: 'blob' }).then((r) => r.data)
