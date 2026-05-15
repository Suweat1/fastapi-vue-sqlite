import client from './client.js'

export const listConversationsApi = () => client.get('/chats/conversations').then((r) => r.data)
export const startConversationFromItemApi = (itemId) => client.post(`/chats/from-item/${itemId}`).then((r) => r.data)
export const startConversationFromOrderApi = (orderId) => client.post(`/chats/from-order/${orderId}`).then((r) => r.data)
export const getConversationMessagesApi = (conversationId) => client.get(`/chats/conversations/${conversationId}`).then((r) => r.data)
export const sendMessageApi = (conversationId, payload) => client.post(`/chats/conversations/${conversationId}/messages`, payload).then((r) => r.data)
export const markConversationReadApi = (conversationId) => client.put(`/chats/conversations/${conversationId}/read`).then((r) => r.data)
