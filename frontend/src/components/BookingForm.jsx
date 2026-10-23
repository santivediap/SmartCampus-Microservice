import { useState } from 'react'
import { api } from '../api/client.js'
import { todayIso } from '../utils/format.js'

const EMPTY_FORM = { usuario: '', fecha: todayIso(), hora_inicio: '09:00', hora_fin: '10:00' }

export default function BookingForm({ rooms, roomId, onRoomChange, onCreated }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  function update(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)

    // Same rule as the backend, checked early to save a round trip
    if (form.hora_inicio >= form.hora_fin) {
      setError('La hora de inicio debe ser anterior a la de fin.')
      return
    }

    setSubmitting(true)
    try {
      const booking = await api.createBooking({ ...form, aula_id: Number(roomId) })
      // Keep the date and room so several slots can be booked in a row
      setForm((prev) => ({ ...prev, usuario: '' }))
      onCreated(booking)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (rooms.length === 0) {
    return <p className="muted">Crea un aula antes de reservar.</p>
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label className="field field-wide">
        <span>Aula</span>
        <select value={roomId} onChange={(e) => onRoomChange(e.target.value)} required>
          {rooms.map((room) => (
            <option key={room.id} value={room.id}>
              {room.nombre} ({room.edificio})
            </option>
          ))}
        </select>
      </label>

      <label className="field field-wide">
        <span>Usuario</span>
        <input
          type="text"
          value={form.usuario}
          onChange={update('usuario')}
          placeholder="ana.garcia"
          required
        />
      </label>

      <label className="field field-wide">
        <span>Fecha</span>
        <input type="date" value={form.fecha} onChange={update('fecha')} required />
      </label>

      <label className="field">
        <span>Inicio</span>
        <input type="time" value={form.hora_inicio} onChange={update('hora_inicio')} required />
      </label>

      <label className="field">
        <span>Fin</span>
        <input type="time" value={form.hora_fin} onChange={update('hora_fin')} required />
      </label>

      {error && (
        <p className="alert alert-error field-wide" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="btn btn-primary field-wide" disabled={submitting}>
        {submitting ? 'Reservando…' : 'Reservar'}
      </button>
    </form>
  )
}
