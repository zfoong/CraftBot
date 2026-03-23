import React, { useState, useEffect } from 'react'
import {
  RotateCcw,
  AlertTriangle,
  X,
  Loader2,
  Plus,
  Edit2,
  Trash2,
} from 'lucide-react'
import { Button, Badge, ConfirmModal } from '../../components/ui'
import { useConfirmModal } from '../../hooks'
import styles from './SettingsPage.module.css'
import { useSettingsWebSocket } from './useSettingsWebSocket'
import { formatCronExpression } from './helpers'

// Types for proactive settings
interface ScheduleConfig {
  id: string
  name: string
  schedule: string
  enabled: boolean
  priority: number
  payload?: { type: string; frequency?: string; scope?: string }
}

interface ProactiveTask {
  id: string
  name: string
  frequency: string
  instruction: string
  enabled: boolean
  priority: number
  permissionTier: number
  time?: string
  day?: string
  runCount: number
  lastRun?: string
  nextRun?: string
  outcomeHistory: Array<{ timestamp: string; result: string; success: boolean }>
}

export function ProactiveSettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()

  // Scheduler state
  const [schedulerEnabled, setSchedulerEnabled] = useState(true)
  const [schedules, setSchedules] = useState<ScheduleConfig[]>([])
  const [isLoadingScheduler, setIsLoadingScheduler] = useState(true)

  // Proactive tasks state
  const [tasks, setTasks] = useState<ProactiveTask[]>([])
  const [isLoadingTasks, setIsLoadingTasks] = useState(true)

  // UI state
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [editingTask, setEditingTask] = useState<ProactiveTask | null>(null)
  const [isResettingTasks, setIsResettingTasks] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')

  // Confirm modal
  const { modalProps: confirmModalProps, confirm } = useConfirmModal()

  // Load data when connected
  useEffect(() => {
    if (!isConnected) return

    const cleanups = [
      // Proactive mode handlers (master toggle uses settings.json)
      onMessage('proactive_mode_get', (data: unknown) => {
        const d = data as { success: boolean; enabled: boolean }
        setIsLoadingScheduler(false)
        if (d.success) {
          setSchedulerEnabled(d.enabled)
        }
      }),
      onMessage('proactive_mode_set', (data: unknown) => {
        const d = data as { success: boolean; enabled: boolean }
        if (d.success) {
          setSchedulerEnabled(d.enabled)
          setSaveStatus('success')
          setTimeout(() => setSaveStatus('idle'), 2000)
        }
      }),
      // Scheduler config handlers (individual schedule toggles)
      onMessage('scheduler_config_get', (data: unknown) => {
        const d = data as { success: boolean; config?: { enabled: boolean; schedules: ScheduleConfig[] } }
        if (d.success && d.config) {
          setSchedules(d.config.schedules || [])
        }
      }),
      onMessage('scheduler_config_update', (data: unknown) => {
        const d = data as { success: boolean; config?: { enabled: boolean; schedules: ScheduleConfig[] } }
        if (d.success && d.config) {
          setSchedules(d.config.schedules || [])
          setSaveStatus('success')
          setTimeout(() => setSaveStatus('idle'), 2000)
        }
      }),
      onMessage('proactive_tasks_get', (data: unknown) => {
        const d = data as { success: boolean; tasks: ProactiveTask[] }
        setIsLoadingTasks(false)
        if (d.success) {
          setTasks(d.tasks || [])
        }
      }),
      onMessage('proactive_task_add', (data: unknown) => {
        const d = data as { success: boolean }
        if (d.success) {
          send('proactive_tasks_get')
          setShowTaskForm(false)
          setEditingTask(null)
        }
      }),
      onMessage('proactive_task_update', (data: unknown) => {
        const d = data as { success: boolean }
        if (d.success) {
          send('proactive_tasks_get')
          setShowTaskForm(false)
          setEditingTask(null)
        }
      }),
      onMessage('proactive_task_remove', (data: unknown) => {
        const d = data as { success: boolean }
        if (d.success) {
          send('proactive_tasks_get')
        }
      }),
      onMessage('proactive_tasks_reset', (data: unknown) => {
        const d = data as { success: boolean }
        setIsResettingTasks(false)
        if (d.success) {
          send('proactive_tasks_get')
        }
      }),
    ]

    // Load initial data
    send('proactive_mode_get')  // Master toggle state from settings.json
    send('scheduler_config_get')  // Individual schedule states
    send('proactive_tasks_get')

    return () => cleanups.forEach(c => c())
  }, [isConnected, send, onMessage])

  // Get schedule by ID
  const getSchedule = (id: string) => schedules.find(s => s.id === id)

  // Toggle proactive mode globally (uses settings.json, not scheduler_config)
  const handleToggleScheduler = (enabled: boolean) => {
    setSchedulerEnabled(enabled)
    send('proactive_mode_set', { enabled })
  }

  // Toggle individual schedule
  const handleToggleSchedule = (scheduleId: string, enabled: boolean) => {
    send('scheduler_config_update', {
      updates: { schedules: [{ id: scheduleId, enabled }] }
    })
  }

  // Handle adding a new task
  const handleAddTask = () => {
    setEditingTask(null)
    setShowTaskForm(true)
  }

  // Handle editing a task
  const handleEditTask = (task: ProactiveTask) => {
    setEditingTask(task)
    setShowTaskForm(true)
  }

  // Handle task toggle
  const handleToggleTask = (taskId: string, enabled: boolean) => {
    send('proactive_task_update', { taskId, updates: { enabled } })
    // Optimistic update
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, enabled } : t))
  }

  // Handle task deletion
  const handleDeleteTask = (taskId: string) => {
    confirm({
      title: 'Delete Task',
      message: 'Are you sure you want to delete this task?',
      confirmText: 'Delete',
      variant: 'danger',
    }, () => {
      send('proactive_task_remove', { taskId })
    })
  }

  // Handle reset all tasks
  const handleResetTasks = () => {
    confirm({
      title: 'Reset Tasks',
      message: 'Are you sure you want to reset all proactive tasks? This will restore the default PROACTIVE.md from template.',
      confirmText: 'Reset',
      variant: 'danger',
    }, () => {
      setIsResettingTasks(true)
      send('proactive_tasks_reset')
    })
  }

  // Group tasks by frequency
  const tasksByFrequency = {
    hourly: tasks.filter(t => t.frequency === 'hourly'),
    daily: tasks.filter(t => t.frequency === 'daily'),
    weekly: tasks.filter(t => t.frequency === 'weekly'),
    monthly: tasks.filter(t => t.frequency === 'monthly'),
  }

  // Heartbeat schedules
  const heartbeatSchedules = [
    { id: 'hourly-heartbeat', label: 'Hourly Heartbeat', desc: 'Runs every hour to check and execute hourly tasks' },
    { id: 'daily-heartbeat', label: 'Daily Heartbeat', desc: 'Runs once daily to execute daily tasks' },
    { id: 'weekly-heartbeat', label: 'Weekly Heartbeat', desc: 'Runs weekly to execute weekly tasks' },
    { id: 'monthly-heartbeat', label: 'Monthly Heartbeat', desc: 'Runs monthly to execute monthly tasks' },
  ]

  // Planner schedules
  const plannerSchedules = [
    { id: 'day-planner', label: 'Daily Planner', desc: 'Plans daily activities and priorities' },
    { id: 'week-planner', label: 'Weekly Planner', desc: 'Plans weekly goals and tasks' },
    { id: 'month-planner', label: 'Monthly Planner', desc: 'Plans monthly objectives and reviews' },
  ]

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Proactive Behavior</h3>
        <p>Configure when the agent acts autonomously and manages scheduled tasks</p>
      </div>

      {/* Master Toggle */}
      <div className={styles.settingsForm}>
        <div className={styles.toggleGroup}>
          <div className={styles.toggleInfo}>
            <span className={styles.toggleLabel}>Enable Proactive Mode</span>
            <span className={styles.toggleDesc}>
              Allow agent to execute scheduled tasks and proactive behaviors automatically
            </span>
          </div>
          <input
            type="checkbox"
            className={styles.toggle}
            checked={schedulerEnabled}
            onChange={(e) => handleToggleScheduler(e.target.checked)}
            disabled={isLoadingScheduler}
          />
        </div>
      </div>

      {/* Toggleable Content - greyed out when proactive mode is disabled */}
      <div className={`${styles.toggleableContent} ${!schedulerEnabled ? styles.disabledContent : ''}`}>
        {/* Heartbeat Schedules */}
        <div className={styles.subsection}>
          <h4 className={styles.subsectionTitle}>Heartbeat Schedules</h4>
          <p className={styles.subsectionDesc}>
            Heartbeats periodically check and execute proactive tasks based on their frequency
          </p>
          <div className={styles.scheduleList}>
            {heartbeatSchedules.map(item => {
              const schedule = getSchedule(item.id)
              return (
                <div key={item.id} className={styles.scheduleCard}>
                  <div className={styles.scheduleInfo}>
                    <span className={styles.scheduleName}>{item.label}</span>
                    <span className={styles.scheduleDesc}>{item.desc}</span>
                    {schedule && (
                      <span className={styles.scheduleTime}>{formatCronExpression(schedule.schedule)}</span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className={styles.toggle}
                    checked={schedule?.enabled ?? false}
                    onChange={(e) => handleToggleSchedule(item.id, e.target.checked)}
                    disabled={isLoadingScheduler || !schedulerEnabled}
                  />
                </div>
              )
            })}
          </div>
        </div>

        {/* Planners */}
        <div className={styles.subsection}>
          <h4 className={styles.subsectionTitle}>Planners</h4>
          <p className={styles.subsectionDesc}>
            Planners review recent interactions and plan proactive activities
          </p>
          <div className={styles.scheduleList}>
            {plannerSchedules.map(item => {
              const schedule = getSchedule(item.id)
              return (
                <div key={item.id} className={styles.scheduleCard}>
                  <div className={styles.scheduleInfo}>
                    <span className={styles.scheduleName}>{item.label}</span>
                    <span className={styles.scheduleDesc}>{item.desc}</span>
                    {schedule && (
                      <span className={styles.scheduleTime}>{formatCronExpression(schedule.schedule)}</span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className={styles.toggle}
                    checked={schedule?.enabled ?? false}
                    onChange={(e) => handleToggleSchedule(item.id, e.target.checked)}
                    disabled={isLoadingScheduler || !schedulerEnabled}
                  />
                </div>
              )
            })}
          </div>
        </div>

        {/* Proactive Tasks */}
        <div className={styles.subsection}>
          <div className={styles.subsectionHeader}>
            <div>
              <h4 className={styles.subsectionTitle}>Proactive Tasks</h4>
              <p className={styles.subsectionDesc}>
                Tasks defined in PROACTIVE.md that the agent executes during heartbeats
              </p>
            </div>
            <Button variant="primary" size="sm" onClick={handleAddTask} icon={<Plus size={14} />} disabled={!schedulerEnabled}>
              Add Task
            </Button>
          </div>

          {isLoadingTasks ? (
            <div className={styles.loadingState}>
              <Loader2 size={20} className={styles.spinning} />
              <span>Loading tasks...</span>
            </div>
          ) : tasks.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No proactive tasks defined yet.</p>
              <Button variant="secondary" size="sm" onClick={handleAddTask} disabled={!schedulerEnabled}>
                Create your first task
              </Button>
            </div>
          ) : (
            <div className={styles.taskGroups}>
              {(['hourly', 'daily', 'weekly', 'monthly'] as const).map(frequency => {
                const freqTasks = tasksByFrequency[frequency]
                if (freqTasks.length === 0) return null

                return (
                  <div key={frequency} className={styles.taskGroup}>
                    <div className={styles.taskGroupHeader}>
                      <Badge variant="default">{frequency}</Badge>
                      <span className={styles.taskCount}>{freqTasks.length} task{freqTasks.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className={styles.taskList}>
                      {freqTasks.map(task => (
                        <div key={task.id} className={`${styles.taskCard} ${!task.enabled ? styles.taskDisabled : ''}`}>
                          <div className={styles.taskMain}>
                            <div className={styles.taskHeader}>
                              <span className={styles.taskName}>{task.name}</span>
                              <div className={styles.taskBadges}>
                                <Badge variant={task.enabled ? 'success' : 'default'}>
                                  {task.enabled ? 'Active' : 'Disabled'}
                                </Badge>
                                <Badge variant="info">{getPriorityLabel(task.priority)}</Badge>
                                <Badge variant={task.permissionTier >= 1 ? 'warning' : 'default'}>
                                  {getNotificationLabel(task.permissionTier)}
                                </Badge>
                              </div>
                            </div>
                            <p className={styles.taskInstruction}>{task.instruction}</p>
                            <div className={styles.taskMeta}>
                              {task.time && <span>Time: {task.time}</span>}
                              {task.day && <span>Day: {task.day}</span>}
                              <span>Runs: {task.runCount}</span>
                              {task.lastRun && (
                                <span>Last: {new Date(task.lastRun).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>
                          <div className={styles.taskActions}>
                            <input
                              type="checkbox"
                              className={styles.toggle}
                              checked={task.enabled}
                              onChange={(e) => handleToggleTask(task.id, e.target.checked)}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditTask(task)}
                              icon={<Edit2 size={14} />}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteTask(task.id)}
                              icon={<Trash2 size={14} />}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Reset Tasks */}
      <div className={styles.dangerZone}>
        <div className={styles.dangerHeader}>
          <AlertTriangle size={18} className={styles.dangerIcon} />
          <h4>Reset Proactive Tasks</h4>
        </div>
        <p className={styles.dangerDescription}>
          This will remove all proactive tasks and restore PROACTIVE.md from the default template.
          This action cannot be undone.
        </p>
        <Button
          variant="danger"
          onClick={handleResetTasks}
          disabled={isResettingTasks}
          icon={isResettingTasks ? <Loader2 size={14} className={styles.spinning} /> : <RotateCcw size={14} />}
        >
          {isResettingTasks ? 'Resetting...' : 'Reset All Tasks'}
        </Button>
      </div>

      {/* Task Form Modal */}
      {showTaskForm && (
        <TaskFormModal
          task={editingTask}
          onClose={() => {
            setShowTaskForm(false)
            setEditingTask(null)
          }}
          onSave={(taskData) => {
            if (editingTask) {
              send('proactive_task_update', { taskId: editingTask.id, updates: taskData })
            } else {
              send('proactive_task_add', { task: taskData })
            }
          }}
        />
      )}

      {/* Confirm Modal */}
      <ConfirmModal {...confirmModalProps} />
    </div>
  )
}

// Helper functions for task display
function getPriorityLabel(value: number): string {
  if (value <= 35) return 'High'
  if (value <= 55) return 'Medium'
  return 'Low'
}

function getNotificationLabel(tier: number): string {
  return tier >= 1 ? 'Notifies' : 'Silent'
}

// Task Form Modal Component
interface TaskFormModalProps {
  task: ProactiveTask | null
  onClose: () => void
  onSave: (taskData: Partial<ProactiveTask>) => void
}

// Priority level mappings (lower number = higher priority)
type PriorityLevel = 'high' | 'medium' | 'low'
const PRIORITY_VALUES: Record<PriorityLevel, number> = {
  high: 30,
  medium: 50,
  low: 70,
}

function getPriorityLevel(value: number): PriorityLevel {
  if (value <= 35) return 'high'
  if (value <= 55) return 'medium'
  return 'low'
}

function TaskFormModal({ task, onClose, onSave }: TaskFormModalProps) {
  const [name, setName] = useState(task?.name || '')
  const [frequency, setFrequency] = useState(task?.frequency || 'daily')
  const [instruction, setInstruction] = useState(task?.instruction || '')
  const [enabled, setEnabled] = useState(task?.enabled ?? true)
  const [priorityLevel, setPriorityLevel] = useState<PriorityLevel>(
    task ? getPriorityLevel(task.priority) : 'medium'
  )
  // Checkbox: true = notify before running (tier 1), false = silent (tier 0)
  const [notifyBeforeRunning, setNotifyBeforeRunning] = useState(
    task ? task.permissionTier >= 1 : true
  )
  const [time, setTime] = useState(task?.time || '')
  const [day, setDay] = useState(task?.day || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      name,
      frequency,
      instruction,
      enabled,
      priority: PRIORITY_VALUES[priorityLevel],
      permissionTier: notifyBeforeRunning ? 1 : 0,
      time: time || undefined,
      day: day || undefined,
    })
  }

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3>{task ? 'Edit Task' : 'Add Proactive Task'}</h3>
          <button className={styles.modalClose} onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            <div className={styles.formGroup}>
              <label>Task Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g., Check emails"
                required
              />
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Frequency</label>
                <select value={frequency} onChange={e => setFrequency(e.target.value)}>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Priority <span className={styles.labelHint}>(higher runs first)</span></label>
                <select value={priorityLevel} onChange={e => setPriorityLevel(e.target.value as PriorityLevel)}>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div className={styles.formRow}>
              {frequency !== 'hourly' && (
                <div className={styles.formGroup}>
                  <label>Time (HH:MM)</label>
                  <input
                    type="time"
                    value={time}
                    onChange={e => setTime(e.target.value)}
                  />
                </div>
              )}

              {frequency === 'weekly' && (
                <div className={styles.formGroup}>
                  <label>Day of Week</label>
                  <select value={day} onChange={e => setDay(e.target.value)}>
                    <option value="">Select day</option>
                    <option value="monday">Monday</option>
                    <option value="tuesday">Tuesday</option>
                    <option value="wednesday">Wednesday</option>
                    <option value="thursday">Thursday</option>
                    <option value="friday">Friday</option>
                    <option value="saturday">Saturday</option>
                    <option value="sunday">Sunday</option>
                  </select>
                </div>
              )}
            </div>

            <div className={styles.toggleGroup}>
              <div className={styles.toggleInfo}>
                <span className={styles.toggleLabel}>Notify me before running</span>
                <span className={styles.toggleDesc}>
                  When enabled, the agent will inform you before executing this task.
                  When disabled, the task runs silently.
                </span>
              </div>
              <input
                type="checkbox"
                className={styles.toggle}
                checked={notifyBeforeRunning}
                onChange={e => setNotifyBeforeRunning(e.target.checked)}
              />
            </div>

            <div className={styles.formGroup}>
              <label>Instruction</label>
              <textarea
                value={instruction}
                onChange={e => setInstruction(e.target.value)}
                placeholder="Describe what the agent should do..."
                rows={4}
                required
              />
              <span className={styles.hint}>
                Be specific and actionable. The agent will follow these instructions during execution.
              </span>
            </div>

            <div className={styles.toggleGroup}>
              <div className={styles.toggleInfo}>
                <span className={styles.toggleLabel}>Enabled</span>
                <span className={styles.toggleDesc}>Task will be executed during heartbeats</span>
              </div>
              <input
                type="checkbox"
                className={styles.toggle}
                checked={enabled}
                onChange={e => setEnabled(e.target.checked)}
              />
            </div>
          </div>

          <div className={styles.modalFooter}>
            <Button variant="secondary" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {task ? 'Save Changes' : 'Add Task'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
