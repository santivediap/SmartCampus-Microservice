import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api/client.js'
import BookingForm from './components/BookingForm.jsx'
import BookingSearch from './components/BookingSearch.jsx'
import BookingTable from './components/BookingTable.jsx'
import HealthBadge from './components/HealthBadge.jsx'
import RoomForm from './components/RoomForm.jsx'
import RoomList from './components/RoomList.jsx'
import './App.css'

export default function App() {
  const [rooms, setRooms] = useState([])
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [selectedRoom, setSelectedRoom] = useState('')
  const [showRoomForm, setShowRoomForm] = useState(false)
  const formRef = useRef(null)

  const reload = useCallback(async () => {
    try {
      const [roomData, bookingData] = await Promise.all([api.listRooms(), api.listBookings()])
      setRooms(roomData)
      setBookings(bookingData)
      setLoadError(null)
    } catch (err) {
      setLoadError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Initial fetch from the API; setState runs after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    reload()
  }, [reload])

  // Auto-hide the success/error toast
  useEffect(() => {
    if (!notice) return undefined
    const timer = setTimeout(() => setNotice(null), 4000)
    return () => clearTimeout(timer)
  }, [notice])

  const roomsById = useMemo(() => new Map(rooms.map((r) => [r.id, r])), [rooms])
  const bookingCountByRoom = useMemo(() => {
    const counts = new Map()
    for (const b of bookings) counts.set(b.aula_id, (counts.get(b.aula_id) ?? 0) + 1)
    return counts
  }, [bookings])

  // Fall back to the first room when nothing is selected or the room was deleted
  const roomId = roomsById.has(Number(selectedRoom)) ? selectedRoom : String(rooms[0]?.id ?? '')

  function handleBook(id) {
    setSelectedRoom(String(id))
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    formRef.current?.querySelector('input[type="text"]')?.focus({ preventScroll: true })
  }

  async function handleDeleteRoom(room) {
    try {
      await api.deleteRoom(room.id)
      setNotice({ type: 'ok', text: `Aula "${room.nombre}" eliminada.` })
    } catch (err) {
      setNotice({ type: 'error', text: err.message })
    }
    // Bookings of the room are deleted in cascade, so refresh both lists
    await reload()
  }

  async function handleDeleteBooking(booking) {
    try {
      await api.deleteBooking(booking.id)
      setNotice({ type: 'ok', text: `Reserva #${booking.id} eliminada.` })
    } catch (err) {
      setNotice({ type: 'error', text: err.message })
    }
    await reload()
  }

  async function handleRoomCreated(room) {
    setShowRoomForm(false)
    setNotice({ type: 'ok', text: `Aula "${room.nombre}" creada.` })
    await reload()
  }

  async function handleCreated(booking) {
    setNotice({ type: 'ok', text: `Reserva #${booking.id} creada.` })
    await reload()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>SmartCampus</h1>
          <p className="muted">Gestión de aulas y reservas</p>
        </div>
        <HealthBadge />
      </header>

      {loadError && (
        <div className="alert alert-error banner" role="alert">
          <span>No se pudieron cargar los datos: {loadError}</span>
          <button type="button" className="btn" onClick={reload}>
            Reintentar
          </button>
        </div>
      )}

      <main className="layout">
        <section className="panel panel-rooms" aria-labelledby="rooms-title">
          <div className="panel-head">
            <h2 id="rooms-title">
              Aulas <span className="muted count">{rooms.length}</span>
            </h2>
            {!showRoomForm && (
              <button type="button" className="btn btn-primary" onClick={() => setShowRoomForm(true)}>
                Nueva aula
              </button>
            )}
          </div>
          {showRoomForm && (
            <RoomForm onCreated={handleRoomCreated} onCancel={() => setShowRoomForm(false)} />
          )}
          <RoomList
            rooms={rooms}
            bookingCountByRoom={bookingCountByRoom}
            onBook={handleBook}
            onDelete={handleDeleteRoom}
            loading={loading}
          />
        </section>

        <div className="side">
          <section className="panel" aria-labelledby="form-title" ref={formRef}>
            <div className="panel-head">
              <h2 id="form-title">Nueva reserva</h2>
            </div>
            {!loading && (
              <BookingForm
                rooms={rooms}
                roomId={roomId}
                onRoomChange={setSelectedRoom}
                onCreated={handleCreated}
              />
            )}
          </section>

          <section className="panel" aria-labelledby="search-title">
            <div className="panel-head">
              <h2 id="search-title">Buscar reserva por id</h2>
            </div>
            <BookingSearch bookings={bookings} roomsById={roomsById} onDelete={handleDeleteBooking} />
          </section>
        </div>

        <section className="panel panel-bookings" aria-labelledby="bookings-title">
          <div className="panel-head">
            <h2 id="bookings-title">Reservas</h2>
          </div>
          <BookingTable
            bookings={bookings}
            rooms={rooms}
            roomsById={roomsById}
            onDelete={handleDeleteBooking}
            loading={loading}
          />
        </section>
      </main>

      {notice && (
        <div className={`toast toast-${notice.type}`} role="status">
          {notice.text}
        </div>
      )}
    </div>
  )
}
