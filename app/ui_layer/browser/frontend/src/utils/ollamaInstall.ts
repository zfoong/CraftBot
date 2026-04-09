/**
 * Maps Ollama install log messages to a 0-100 progress percentage.
 *
 * The backend streams discrete text lines via `local_llm_install_progress`.
 * We derive a deterministic percentage from known step keywords so both
 * the onboarding and settings UIs can show a progress bar without any
 * backend changes.
 */
export function getOllamaInstallPercent(log: string[]): number {
  if (log.length === 0) return 5

  const last = log[log.length - 1].toLowerCase()

  // ── Completion ──────────────────────────────────────────────────────────────
  if (last.includes('successfully installed') || last.includes('installed successfully')) return 100

  // ── Windows / winget path ───────────────────────────────────────────────────
  if (last.includes('running installer silently') || last.includes('starting package install')) return 82
  if (last.includes('successfully verified') || last.includes('verifying')) return 75
  if (last.includes('downloading') && last.includes('ollama') && !last.includes('script')) return 55
  if (last.includes('found ollama') || last.includes('this application is licensed')) return 42
  if (last.includes('winget install failed') || last.includes('switching to direct download')) return 28
  if (last.includes('winget not found') || last.includes('downloading installer directly')) return 22
  if (last.includes('installing ollama via winget')) return 35
  if (last.includes('checking for winget')) return 15

  // ── Windows / direct download path ─────────────────────────────────────────
  if (last.includes('running installer')) return 82
  if (last.includes('downloading ollama installer')) return 45

  // ── Mac / Linux — install script streams many lines ────────────────────────
  if (last.includes('downloading ollama install script')) return 15
  const streamed = Math.min(log.length, 24)
  return Math.min(20 + Math.round(streamed * 2.8), 88)
}
