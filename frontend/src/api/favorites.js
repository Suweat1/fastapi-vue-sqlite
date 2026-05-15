import client from './client.js'

export const listFavoritesApi = (params) => client.get('/favorites', { params }).then((r) => r.data)
export const toggleFavoriteApi = (id) => client.post(`/favorites/${id}/toggle`).then((r) => r.data)
