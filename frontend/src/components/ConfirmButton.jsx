import { useEffect, useState } from 'react'

// Two-step delete button: first click arms it, second click confirms.
// Disarms itself after a few seconds so a stray click never deletes anything.
export default function ConfirmButton({ onConfirm, label = 'Eliminar', confirmLabel = '¿Seguro?', disabled }) {
  const [armed, setArmed] = useState(false)

  useEffect(() => {
    if (!armed) return undefined
    const timer = setTimeout(() => setArmed(false), 3000)
    return () => clearTimeout(timer)
  }, [armed])

  function handleClick() {
    if (armed) {
      setArmed(false)
      onConfirm()
    } else {
      setArmed(true)
    }
  }

  return (
    <button
      type="button"
      className={`btn btn-danger ${armed ? 'is-armed' : ''}`}
      onClick={handleClick}
      disabled={disabled}
    >
      {armed ? confirmLabel : label}
    </button>
  )
}
