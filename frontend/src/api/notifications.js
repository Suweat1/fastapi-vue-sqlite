import client from './client.js'

export const listNotificationsApi = (params) => client.get('/notifications', { params }).then((r) => r.data)
export const getUnreadNotificationCountApi = () => client.get('/notifications/unread-count').then((r) => r.data)
export const markNotificationReadApi = (notificationId) => client.put(`/notifications/${notificationId}/read`).then((r) => r.data)
export const markAllNotificationsReadApi = () => client.put('/notifications/read-all').then((r) => r.data)
