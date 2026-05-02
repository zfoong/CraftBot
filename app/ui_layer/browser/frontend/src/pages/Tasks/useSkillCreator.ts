import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSettingsWebSocket } from '../Settings/useSettingsWebSocket'
import type { ActionItem } from '../../types'
import type { SkillCreatorSubmit, SkillCreatorSuccessInfo } from '../../components/ui/SkillCreatorModal'

export type SkillCreatorStatus = 'idle' | 'submitting' | 'success' | 'error'

interface SkillCreatorResponse {
  success: boolean
  taskId?: string
  skillName?: string
  mode?: 'create' | 'improve'
  error?: string
}

const ERROR_MESSAGES: Record<string, string> = {
  invalid_mode: 'Invalid request mode.',
  missing_task_id: 'No source task selected.',
  missing_skill_name: 'Enter a skill name.',
  invalid_skill_name: 'Skill name format is invalid.',
  reserved_skill_name: 'That name is reserved.',
  source_task_not_found: 'Source task no longer exists.',
  source_task_not_completed: 'Source task is not completed.',
  source_task_is_internal_workflow: 'This task cannot be turned into a skill.',
  skill_already_exists: 'A skill with this name already exists.',
  skill_not_found: 'The target skill no longer exists.',
  workflow_busy: 'Another skill workflow is in progress. Try again in a moment.',
  task_manager_unavailable: 'Agent is not ready.',
  workflow_lock_unavailable: 'Agent is not ready.',
}

function humanize(error: string | undefined): string {
  if (!error) return 'Unknown error.'
  return ERROR_MESSAGES[error] ?? error
}

export function useSkillCreator() {
  const { send, onMessage } = useSettingsWebSocket()
  const [isOpen, setIsOpen] = useState(false)
  const [sourceTask, setSourceTask] = useState<ActionItem | null>(null)
  const [status, setStatus] = useState<SkillCreatorStatus>('idle')
  const [serverError, setServerError] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<SkillCreatorResponse | null>(null)

  // Subscribe to backend responses. The modal stays OPEN on success so the
  // user sees the "submitted, agent is working" confirmation inside the
  // dialog they were just interacting with — they dismiss it manually with
  // the Close button. (Previously the modal auto-closed and a tiny chip in
  // the top bar showed status, which was confusing.)
  useEffect(() => {
    const unsubscribe = onMessage('create_skill_from_task', (data: unknown) => {
      const resp = data as SkillCreatorResponse
      setLastResult(resp)
      if (resp.success) {
        setStatus('success')
        setServerError(null)
      } else {
        setStatus('error')
        setServerError(humanize(resp.error))
      }
    })
    return unsubscribe
  }, [onMessage])

  const open = useCallback((task: ActionItem) => {
    setSourceTask(task)
    setIsOpen(true)
    setServerError(null)
    setStatus('idle')
  }, [])

  const close = useCallback(() => {
    if (status === 'submitting') return // don't allow closing mid-flight
    setIsOpen(false)
    setSourceTask(null)
    setServerError(null)
    // Reset status so the next open shows a fresh form (otherwise a prior
    // success/error would persist and the modal would skip the form view).
    setStatus('idle')
    setLastResult(null)
  }, [status])

  const submit = useCallback((payload: SkillCreatorSubmit) => {
    if (!sourceTask) return
    setStatus('submitting')
    setServerError(null)
    send('create_skill_from_task', {
      taskId: sourceTask.id,
      mode: payload.mode,
      skillName: payload.skillName,
      targetSkill: payload.targetSkill,
    })
  }, [send, sourceTask])

  // Stabilize the array reference — `?? []` would yield a new array each
  // render, which invalidates downstream useMemo/useEffect deps in the modal
  // and causes the form to reset on every parent re-render (e.g. while
  // submitting).
  const sourceSkills = useMemo(
    () => sourceTask?.selectedSkills ?? [],
    [sourceTask],
  )

  // Compact view of the last successful submit, for the modal's success
  // state. Returns null unless we have a valid skill name + mode pair.
  const successInfo = useMemo<SkillCreatorSuccessInfo | null>(() => {
    if (status !== 'success') return null
    if (!lastResult?.skillName || !lastResult?.mode) return null
    return { skillName: lastResult.skillName, mode: lastResult.mode }
  }, [status, lastResult])

  return {
    isOpen,
    sourceTask,
    sourceSkills,
    status,
    serverError,
    lastResult,
    successInfo,
    open,
    close,
    submit,
  }
}
