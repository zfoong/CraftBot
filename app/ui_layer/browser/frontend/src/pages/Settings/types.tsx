import React from 'react'
import {
  Settings,
  Brain,
  Database,
  Cpu,
  Plug,
  Package,
  Globe,
} from 'lucide-react'

export type SettingsCategory =
  | 'general'
  | 'proactive'
  | 'memory'
  | 'model'
  | 'mcps'
  | 'skills'
  | 'integrations'

export interface SettingsCategoryItem {
  id: SettingsCategory
  label: string
  icon: React.ReactNode
  description: string
}

export const categories: SettingsCategoryItem[] = [
  {
    id: 'general',
    label: 'General',
    icon: <Settings size={18} />,
    description: 'Agent name, theme, and reset options',
  },
  {
    id: 'proactive',
    label: 'Proactive',
    icon: <Brain size={18} />,
    description: 'Autonomous behavior settings',
  },
  {
    id: 'memory',
    label: 'Memory',
    icon: <Database size={18} />,
    description: 'Agent memory and context settings',
  },
  {
    id: 'model',
    label: 'Model',
    icon: <Cpu size={18} />,
    description: 'AI model selection and API keys',
  },
  {
    id: 'mcps',
    label: 'MCPs',
    icon: <Plug size={18} />,
    description: 'Model Context Protocol servers',
  },
  {
    id: 'skills',
    label: 'Skills',
    icon: <Package size={18} />,
    description: 'Manage agent skills',
  },
  {
    id: 'integrations',
    label: 'Integrations',
    icon: <Globe size={18} />,
    description: 'Discord, Slack, Google Workspace',
  },
]
