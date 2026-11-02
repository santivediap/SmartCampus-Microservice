import { useState } from 'react'
import { api } from '../api/client.js'

const EMPTY_FORM = { nombre: '', edificio: '', capacidad: '', equipamiento: '' }

// Turn "proyector, pizarra digital" into ["proyector", "pizarra digital"]
function parseEquipment(text) {
  const items = text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
  return [...new Set(items)]
}

export default function RoomForm({ onCreated, onCancel }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const equipment = parseEquipment(form.equipamiento)

  function update(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)

    // Same rule as the backend, checked early to save a round trip
    const capacidad = Number(form.capacidad)
    if (!Number.isInteger(capacidad) || capacidad <= 0) {
      setError('La capacidad debe ser un número entero mayor que 0.')
      return
    }

    setSubmitting(true)
    try {
      const room = await api.createRoom({
        nombre: form.nombre,
        edificio: form.edificio,
        capacidad,
        equipamiento: equipment,
      })
      setForm(EMPTY_FORM)
      onCreated(room)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="form room-form" onSubmit={handleSubmit}>
      <label className="field field-wide">
        <span>Nombre</span>
        <input
          type="text"
          value={form.nombre}
          onChange={update('nombre')}
          placeholder="Laboratorio de Redes"
          required
          autoFocus
        />
      </label>

      <label className="field">
        <span>Edificio</span>
        <input
          type="text"
          value={form.edificio}
          onChange={update('edificio')}
          placeholder="Edificio C"
          required
        />
      </label>

      <label className="field">
        <span>Capacidad</span>
        <input
          type="number"
          min="1"
          step="1"
          inputMode="numeric"
          value={form.capacidad}
          onChange={update('capacidad')}
          placeholder="25"
          required
        />
      </label>

      <label className="field field-wide">
        <span>Equipamiento (separado por comas, opcional)</span>
        <input
          type="text"
          value={form.equipamiento}
          onChange={update('equipamiento')}
          placeholder="proyector, ordenadores, pizarra digital"
        />
      </label>

      {equipment.length > 0 && (
        <ul className="chips field-wide" aria-label="Vista previa del equipamiento">
          {equipment.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}

      {error && (
        <p className="alert alert-error field-wide" role="alert">
          {error}
        </p>
      )}

      <div className="form-actions field-wide">
        <button type="button" className="btn" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Creando…' : 'Crear aula'}
        </button>
      </div>
    </form>
  )
}
