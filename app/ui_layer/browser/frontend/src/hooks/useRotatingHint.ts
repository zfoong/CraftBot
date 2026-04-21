import { useEffect, useState } from 'react'

export interface RotatingHint {
  /** The current hint text to render. */
  text: string
  /** Whether the hint is currently visible. Use for opacity-based crossfade. */
  visible: boolean
}

interface Options {
  /** Interval between rotations in milliseconds. Defaults to 7000. */
  rotationMs?: number
  /** Fade duration in milliseconds. Defaults to 300. */
  fadeMs?: number
}

/**
 * Rotates through a list of hint strings on an interval with a fade-out/fade-in
 * transition. Starts at a random index so repeat views feel fresh.
 *
 * Consumers render `hint.text` and bind `opacity: hint.visible ? 1 : 0` with
 * a matching CSS transition duration to get the crossfade.
 */
export function useRotatingHint(
  hints: readonly string[],
  { rotationMs = 7000, fadeMs = 300 }: Options = {},
): RotatingHint {
  const [index, setIndex] = useState(() =>
    hints.length > 0 ? Math.floor(Math.random() * hints.length) : 0,
  )
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    if (hints.length <= 1) return

    const interval = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setIndex(prev => (prev + 1) % hints.length)
        setVisible(true)
      }, fadeMs)
    }, rotationMs)

    return () => clearInterval(interval)
  }, [hints.length, rotationMs, fadeMs])

  return {
    text: hints[index] ?? '',
    visible,
  }
}
