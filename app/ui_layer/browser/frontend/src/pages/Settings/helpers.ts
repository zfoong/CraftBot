// Theme application helper
export function applyTheme(theme: string) {
  const root = document.documentElement

  if (theme === 'system') {
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
  } else {
    root.setAttribute('data-theme', theme)
  }

  // Persist to localStorage
  localStorage.setItem('craftbot-theme', theme)
}

// Get initial theme from localStorage or default
export function getInitialTheme(): string {
  return localStorage.getItem('craftbot-theme') || 'dark'
}

// Get initial agent name from localStorage or default
export function getInitialAgentName(): string {
  return localStorage.getItem('craftbot-agent-name') || 'CraftBot'
}

// Convert cron expression to human-readable format
export function formatCronExpression(cron: string): string {
  const parts = cron.split(' ')
  if (parts.length !== 5) return cron // Return as-is if invalid

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

  // Helper to format time
  const formatTime = (h: string, m: string): string => {
    const hourNum = parseInt(h, 10)
    const minNum = parseInt(m, 10)
    const period = hourNum >= 12 ? 'PM' : 'AM'
    const displayHour = hourNum === 0 ? 12 : hourNum > 12 ? hourNum - 12 : hourNum
    const displayMin = minNum.toString().padStart(2, '0')
    return `${displayHour}:${displayMin} ${period}`
  }

  // Helper for day suffix
  const getDaySuffix = (day: number): string => {
    if (day >= 11 && day <= 13) return 'th'
    switch (day % 10) {
      case 1: return 'st'
      case 2: return 'nd'
      case 3: return 'rd'
      default: return 'th'
    }
  }

  // Day of week names
  const dayNames: Record<string, string> = {
    '0': 'Sunday', '7': 'Sunday',
    '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday',
    '4': 'Thursday', '5': 'Friday', '6': 'Saturday'
  }

  // Hourly: minute is fixed, everything else is *
  if (hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    const minNum = parseInt(minute, 10)
    if (minNum === 0) return 'Every hour at :00'
    return `Every hour at :${minute.padStart(2, '0')}`
  }

  // Daily: hour and minute fixed, rest is *
  if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    return `Daily at ${formatTime(hour, minute)}`
  }

  // Weekly: day of week is set
  if (dayOfMonth === '*' && month === '*' && dayOfWeek !== '*') {
    const dayName = dayNames[dayOfWeek] || dayOfWeek
    return `Weekly on ${dayName} at ${formatTime(hour, minute)}`
  }

  // Monthly: day of month is set
  if (dayOfMonth !== '*' && month === '*' && dayOfWeek === '*') {
    const dayNum = parseInt(dayOfMonth, 10)
    return `Monthly on the ${dayNum}${getDaySuffix(dayNum)} at ${formatTime(hour, minute)}`
  }

  // Default: return a more readable version
  return `Cron: ${cron}`
}
