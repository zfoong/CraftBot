import React from 'react'
import {
  Settings,
  Brain,
  Database,
  Cpu,
  Plug,
  Package,
  Globe,
  Box,
} from 'lucide-react'

export type SettingsCategory =
  | 'general'
  | 'proactive'
  | 'memory'
  | 'model'
  | 'mcps'
  | 'skills'
  | 'integrations'
  | 'living_ui'

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
    icon: React.createElement(Settings, { size: 18 }),
    description: 'Agent name, theme, and reset options',
  },
  {
    id: 'proactive',
    label: 'Proactive',
    icon: React.createElement(Brain, { size: 18 }),
    description: 'Autonomous behavior settings',
  },
  {
    id: 'memory',
    label: 'Memory',
    icon: React.createElement(Database, { size: 18 }),
    description: 'Agent memory and context settings',
  },
  {
    id: 'model',
    label: 'Model',
    icon: React.createElement(Cpu, { size: 18 }),
    description: 'AI model selection and API keys',
  },
  {
    id: 'mcps',
    label: 'MCPs',
    icon: React.createElement(Plug, { size: 18 }),
    description: 'Model Context Protocol servers',
  },
  {
    id: 'skills',
    label: 'Skills',
    icon: React.createElement(Package, { size: 18 }),
    description: 'Manage agent skills',
  },
  {
    id: 'integrations',
    label: 'Integrations',
    icon: React.createElement(Globe, { size: 18 }),
    description: 'Discord, Slack, Google Workspace',
  },
  {
    id: 'living_ui',
    label: 'Living UI',
    icon: React.createElement(Box, { size: 18 }),
    description: 'Manage Living UI projects',
  },
]
