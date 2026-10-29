import { useState } from 'react'
import { api } from '../api/client.js'
import { formatDate } from '../utils/format.js'
import ConfirmButton from './ConfirmButton.jsx'

export default function BookingSearch({ bookings, roomsById, onDelete }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [searching, setSearching] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setResult(null)
    setError(null)

    const id = Number(query)
    if (!Number.isInteger(id) || id <= 0) {
      setError('Introduce un id numérico mayor que 0.')
      return
    }

    setSearching(true)
    try {
      setResult(await api.getBooking(id))
    } catch (err) {
      setError(err.status === 404 ? `No existe ninguna reserva con id ${id}.` : err.message)
    } finally {
      setSearching(false)
    }
  }

  // Hide the result if the booking was deleted elsewhere (table or room delete)
  const visibleResult = result && bookings.some((b) => b.id === result.id) ? result : null
  const room = visibleResult ? roomsById.get(visibleResult.aula_id) : null

  return (
    <div className="search">
      <form className="search-bar" onSubmit={handleSubmit}>
        <input
          type="number"
          min="1"
          inputMode="numeric"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Id de la reserva"
          aria-label="Id de la reserva"
          required
        />
        <button type="submit" className="btn btn-primary" disabled={searching}>
          {searching ? 'Buscando…' : 'Buscar'}
        </button>
      </form>

      {error && <p className="alert alert-error">{error}</p>}

      {visibleResult && (
        <div className="result-card">
          <div className="room-head">
            <h3>Reserva #{visibleResult.id}</h3>
            <ConfirmButton onConfirm={() => onDelete(visibleResult)} />
          </div>
          <dl>
            <dt>Aula</dt>
            <dd>{room ? `${room.nombre} (${room.edificio})` : `#${visibleResult.aula_id}`}</dd>
            <dt>Usuario</dt>
            <dd>{visibleResult.usuario}</dd>
            <dt>Fecha</dt>
            <dd>{formatDate(visibleResult.fecha)}</dd>
            <dt>Horario</dt>
            <dd>
              {visibleResult.hora_inicio} – {visibleResult.hora_fin}
            </dd>
          </dl>
        </div>
      )}
    </div>
  )
}
