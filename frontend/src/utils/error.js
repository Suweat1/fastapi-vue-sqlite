export const getApiErrorMessage = (error, fallback = '操作失败，请稍后重试') => {
  const responseData = error?.response?.data

  if (typeof responseData === 'string' && responseData.trim()) {
    return responseData
  }

  if (responseData && typeof responseData === 'object') {
    const detail = responseData.detail || responseData.message || responseData.error
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (Array.isArray(detail) && detail.length) {
      const messages = detail
        .map((entry) => {
          if (!entry || typeof entry !== 'object') return ''
          const location = Array.isArray(entry.loc) ? entry.loc.filter(Boolean).join('.') : ''
          const message = typeof entry.msg === 'string' ? entry.msg : ''
          if (location && message) return `${location}: ${message}`
          return message || location
        })
        .filter(Boolean)
      if (messages.length) {
        return `参数校验失败：${messages.join('；')}`
      }
    }
  }

  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message
  }

  return fallback
}
