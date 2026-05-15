import client from './client.js'

export const registerApi = (payload) => client.post('/auth/register', payload).then((r) => r.data)
export const loginApi = (payload) => client.post('/auth/login', payload).then((r) => r.data)
export const getMeApi = () => client.get('/auth/me').then((r) => r.data)
export const updateMeApi = (payload) => client.put('/auth/me', payload).then((r) => r.data)
