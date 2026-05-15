export const NOTIFICATION_CHANGE_EVENT = 'cm-notification-change'
export const REALTIME_MESSAGE_EVENT = 'cm-realtime-message'
export const REALTIME_NOTIFICATION_EVENT = 'cm-realtime-notification'
export const REALTIME_CONVERSATION_EVENT = 'cm-realtime-conversation'

const emitCustomEvent = (name, detail = {}) => {
  if (typeof window === 'undefined' || typeof window.dispatchEvent !== 'function') {
    return
  }
  window.dispatchEvent(new CustomEvent(name, { detail }))
}

export const emitNotificationChange = () => {
  emitCustomEvent(NOTIFICATION_CHANGE_EVENT)
}

export const emitRealtimeMessage = (detail) => {
  emitCustomEvent(REALTIME_MESSAGE_EVENT, detail)
}

export const emitRealtimeNotification = (detail) => {
  emitCustomEvent(REALTIME_NOTIFICATION_EVENT, detail)
}

export const emitRealtimeConversation = (detail) => {
  emitCustomEvent(REALTIME_CONVERSATION_EVENT, detail)
}
