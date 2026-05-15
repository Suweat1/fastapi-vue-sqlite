import client from './client.js'

export const listItemsApi = (params) => client.get('/items', { params }).then((r) => r.data)
export const getItemApi = (id) => client.get(`/items/${id}`).then((r) => r.data)
export const createItemApi = (payload) => client.post('/items', payload).then((r) => r.data)
export const updateItemApi = (id, payload) => client.put(`/items/${id}`, payload).then((r) => r.data)
export const deleteItemApi = (id) => client.delete(`/items/${id}`).then((r) => r.data)
export const myItemsApi = (params) => client.get('/items/me/list', { params }).then((r) => r.data)
export const hotItemsApi = () => client.get('/items/recommendations/hot').then((r) => r.data)
