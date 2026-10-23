import ConfirmButton from './ConfirmButton.jsx'

export default function RoomList({ rooms, bookingCountByRoom, onBook, onDelete, loading }) {
  if (loading) return <p className="muted">Cargando aulas…</p>
  if (rooms.length === 0) return <p className="muted">No hay aulas registradas.</p>

  return (
    <ul className="room-list">
      {rooms.map((room) => {
        const count = bookingCountByRoom.get(room.id) ?? 0
        return (
          <li key={room.id} className="room-card">
            <div className="room-head">
              <h3>{room.nombre}</h3>
              <span className="tag">#{room.id}</span>
            </div>
            <p className="room-meta">
              {room.edificio} · {room.capacidad} plazas · {count} {count === 1 ? 'reserva' : 'reservas'}
            </p>
            {room.equipamiento.length > 0 && (
              <ul className="chips">
                {room.equipamiento.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            )}
            <div className="room-actions">
              <button type="button" className="btn" onClick={() => onBook(room.id)}>
                Reservar
              </button>
              <ConfirmButton
                onConfirm={() => onDelete(room)}
                confirmLabel={count > 0 ? `¿Borrar con ${count} reservas?` : '¿Seguro?'}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
