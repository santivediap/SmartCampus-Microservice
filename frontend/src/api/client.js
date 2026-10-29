// Every request goes through /api so the same build works behind the Vite
// proxy in development and behind a reverse proxy (nginx) in production.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, { method = 'GET', body } = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('No se puede conectar con la API', 0)
  }

  // 204 No Content (DELETE) has no body to parse
  if (response.status === 204) return null

  // The proxy returns plain text/HTML when Flask is down, so parse defensively
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message = data?.error ?? `Error ${response.status} en la API`
    throw new ApiError(message, response.status)
  }
  return data
}

export const api = {
  health: () => request('/health'),

  listRooms: () => request('/rooms'),
  createRoom: (room) => request('/rooms', { method: 'POST', body: room }),
  deleteRoom: (id) => request(`/rooms/${id}`, { method: 'DELETE' }),

  listBookings: () => request('/bookings'),
  getBooking: (id) => request(`/bookings/${id}`),
  createBooking: (booking) => request('/bookings', { method: 'POST', body: booking }),
  deleteBooking: (id) => request(`/bookings/${id}`, { method: 'DELETE' }),
}
