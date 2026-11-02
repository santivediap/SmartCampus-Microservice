import { useState } from 'react'
import { formatDate } from '../utils/format.js'
import ConfirmButton from './ConfirmButton.jsx'

export default function BookingTable({ bookings, rooms, roomsById, onDelete, loading }) {
  const [roomFilter, setRoomFilter] = useState('all')

  // Fall back to "all" if the filtered room no longer exists
  const activeFilter = roomFilter !== 'all' && !roomsById.has(Number(roomFilter)) ? 'all' : roomFilter
  const visible =
    activeFilter === 'all' ? bookings : bookings.filter((b) => b.aula_id === Number(activeFilter))

  return (
    <>
      <div className="table-toolbar">
        <label className="field field-inline">
          <span>Filtrar por aula</span>
          <select value={activeFilter} onChange={(e) => setRoomFilter(e.target.value)}>
            <option value="all">Todas</option>
            {rooms.map((room) => (
              <option key={room.id} value={room.id}>
                {room.nombre}
              </option>
            ))}
          </select>
        </label>
        <span className="muted">
          {visible.length} {visible.length === 1 ? 'reserva' : 'reservas'}
        </span>
      </div>

      {loading ? (
        <p className="muted">Cargando reservas…</p>
      ) : visible.length === 0 ? (
        <p className="muted">No hay reservas.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Id</th>
                <th>Aula</th>
                <th>Usuario</th>
                <th>Fecha</th>
                <th>Horario</th>
                <th aria-label="Acciones" />
              </tr>
            </thead>
            <tbody>
              {visible.map((booking) => (
                <tr key={booking.id}>
                  <td className="num">#{booking.id}</td>
                  <td>{roomsById.get(booking.aula_id)?.nombre ?? `#${booking.aula_id}`}</td>
                  <td>{booking.usuario}</td>
                  <td>{formatDate(booking.fecha)}</td>
                  <td className="num">
                    {booking.hora_inicio} – {booking.hora_fin}
                  </td>
                  <td className="actions">
                    <ConfirmButton onConfirm={() => onDelete(booking)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
