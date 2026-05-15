import client from './client.js'

export const purchaseItemApi = (itemId) => client.post(`/orders/purchase/${itemId}`).then((r) => r.data)
export const listMyOrdersApi = (params) => client.get('/orders/me', { params }).then((r) => r.data)
