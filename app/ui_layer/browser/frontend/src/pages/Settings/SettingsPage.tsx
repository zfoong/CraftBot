import React, { useState } from 'react'
import {
  Settings,
  User,
  Brain,
  Database,
  Cpu,
  Plug,
  Package,
  Globe,
  ChevronRight
} from 'lucide-react'
import { Button, Badge } from '../../components/ui'
import styles from './SettingsPage.module.css'

type SettingsCategory =
  | 'general'
  | 'proactive'
  | 'memory'
  | 'model'
  | 'mcps'
  | 'skills'
  | 'integrations'

interface SettingsCategoryItem {
  id: SettingsCategory
  label: string
  icon: React.ReactNode
  description: string
}

const categories: SettingsCategoryItem[] = [
  {
    id: 'general',
    label: 'General',
    icon: <Settings size={18} />,
    description: 'Language, agent name, and preferences',
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

export function SettingsPage() {
  const [activeCategory, setActiveCategory] = useState<SettingsCategory>('general')

  const renderSettingsContent = () => {
    switch (activeCategory) {
      case 'general':
        return <GeneralSettings />
      case 'proactive':
        return <ProactiveSettings />
      case 'memory':
        return <MemorySettings />
      case 'model':
        return <ModelSettings />
      case 'mcps':
        return <MCPSettings />
      case 'skills':
        return <SkillsSettings />
      case 'integrations':
        return <IntegrationsSettings />
      default:
        return null
    }
  }

  return (
    <div className={styles.settingsPage}>
      {/* Sidebar */}
      <nav className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h2>Settings</h2>
        </div>
        <div className={styles.categoryList}>
          {categories.map(cat => (
            <button
              key={cat.id}
              className={`${styles.categoryItem} ${activeCategory === cat.id ? styles.active : ''}`}
              onClick={() => setActiveCategory(cat.id)}
            >
              <span className={styles.categoryIcon}>{cat.icon}</span>
              <div className={styles.categoryInfo}>
                <span className={styles.categoryLabel}>{cat.label}</span>
                <span className={styles.categoryDesc}>{cat.description}</span>
              </div>
              <ChevronRight size={14} className={styles.chevron} />
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <div className={styles.content}>
        {renderSettingsContent()}
      </div>
    </div>
  )
}

// Settings Sections

function GeneralSettings() {
  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>General Settings</h3>
        <p>Configure basic agent settings and preferences</p>
      </div>
      <div className={styles.settingsForm}>
        <div className={styles.formGroup}>
          <label>Agent Name</label>
          <input type="text" defaultValue="CraftBot" placeholder="Enter agent name" />
          <span className={styles.hint}>The name displayed in conversations</span>
        </div>
        <div className={styles.formGroup}>
          <label>Language</label>
          <select defaultValue="en">
            <option value="en">English</option>
            <option value="zh">Chinese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
          </select>
        </div>
        <div className={styles.formGroup}>
          <label>Theme</label>
          <select defaultValue="dark">
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>
      <div className={styles.sectionFooter}>
        <Button variant="primary">Save Changes</Button>
      </div>
    </div>
  )
}

function ProactiveSettings() {
  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Proactive Behavior</h3>
        <p>Configure when the agent acts autonomously</p>
      </div>
      <div className={styles.settingsForm}>
        <div className={styles.toggleGroup}>
          <div className={styles.toggleInfo}>
            <span className={styles.toggleLabel}>Enable Proactive Mode</span>
            <span className={styles.toggleDesc}>Allow agent to suggest actions</span>
          </div>
          <input type="checkbox" className={styles.toggle} defaultChecked />
        </div>
        <div className={styles.toggleGroup}>
          <div className={styles.toggleInfo}>
            <span className={styles.toggleLabel}>Auto-fix Errors</span>
            <span className={styles.toggleDesc}>Automatically attempt to fix errors</span>
          </div>
          <input type="checkbox" className={styles.toggle} />
        </div>
        <div className={styles.toggleGroup}>
          <div className={styles.toggleInfo}>
            <span className={styles.toggleLabel}>Continuous Mode</span>
            <span className={styles.toggleDesc}>Keep working until task is complete</span>
          </div>
          <input type="checkbox" className={styles.toggle} />
        </div>
      </div>
    </div>
  )
}

function MemorySettings() {
  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Memory Settings</h3>
        <p>Manage agent memory and context retention</p>
      </div>
      <div className={styles.settingsForm}>
        <div className={styles.formGroup}>
          <label>Context Window</label>
          <select defaultValue="128k">
            <option value="32k">32K tokens</option>
            <option value="64k">64K tokens</option>
            <option value="128k">128K tokens</option>
            <option value="200k">200K tokens</option>
          </select>
        </div>
        <div className={styles.toggleGroup}>
          <div className={styles.toggleInfo}>
            <span className={styles.toggleLabel}>Persistent Memory</span>
            <span className={styles.toggleDesc}>Remember context across sessions</span>
          </div>
          <input type="checkbox" className={styles.toggle} defaultChecked />
        </div>
        <div className={styles.actionGroup}>
          <Button variant="secondary">Export Memory</Button>
          <Button variant="danger">Clear Memory</Button>
        </div>
      </div>
    </div>
  )
}

function ModelSettings() {
  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Model Configuration</h3>
        <p>Select AI model and configure API settings</p>
      </div>
      <div className={styles.settingsForm}>
        <div className={styles.formGroup}>
          <label>Provider</label>
          <select defaultValue="anthropic">
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="local">Local (Ollama)</option>
          </select>
        </div>
        <div className={styles.formGroup}>
          <label>Model</label>
          <select defaultValue="claude-3-5-sonnet">
            <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
            <option value="claude-3-opus">Claude 3 Opus</option>
            <option value="claude-3-haiku">Claude 3 Haiku</option>
          </select>
        </div>
        <div className={styles.formGroup}>
          <label>API Key</label>
          <input type="password" placeholder="sk-ant-..." />
          <span className={styles.hint}>Your API key is stored securely</span>
        </div>
      </div>
      <div className={styles.sectionFooter}>
        <Button variant="secondary">Test Connection</Button>
        <Button variant="primary">Save</Button>
      </div>
    </div>
  )
}

function MCPSettings() {
  const servers = [
    { name: 'filesystem', status: 'connected', tools: 5 },
    { name: 'browser', status: 'connected', tools: 8 },
    { name: 'shell', status: 'connected', tools: 3 },
  ]

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>MCP Servers</h3>
        <p>Manage Model Context Protocol server connections</p>
      </div>
      <div className={styles.serverList}>
        {servers.map(server => (
          <div key={server.name} className={styles.serverCard}>
            <div className={styles.serverInfo}>
              <Plug size={16} />
              <span className={styles.serverName}>{server.name}</span>
              <Badge variant={server.status === 'connected' ? 'success' : 'error'}>
                {server.status}
              </Badge>
            </div>
            <span className={styles.toolCount}>{server.tools} tools</span>
            <Button variant="ghost" size="sm">Configure</Button>
          </div>
        ))}
      </div>
      <Button variant="secondary" icon={<Plug size={14} />}>
        Add MCP Server
      </Button>
    </div>
  )
}

function SkillsSettings() {
  const skills = [
    { name: 'Code Analysis', enabled: true, description: 'Analyze and understand code' },
    { name: 'File Management', enabled: true, description: 'Create, edit, and manage files' },
    { name: 'Web Search', enabled: false, description: 'Search the web for information' },
    { name: 'Image Processing', enabled: true, description: 'Analyze and process images' },
  ]

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Skills</h3>
        <p>Enable or disable agent capabilities</p>
      </div>
      <div className={styles.skillsList}>
        {skills.map(skill => (
          <div key={skill.name} className={styles.skillCard}>
            <div className={styles.skillInfo}>
              <span className={styles.skillName}>{skill.name}</span>
              <span className={styles.skillDesc}>{skill.description}</span>
            </div>
            <input
              type="checkbox"
              className={styles.toggle}
              defaultChecked={skill.enabled}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

function IntegrationsSettings() {
  const integrations = [
    { name: 'Discord', connected: false, icon: '🎮' },
    { name: 'Slack', connected: false, icon: '💬' },
    { name: 'Google Workspace', connected: false, icon: '📧' },
    { name: 'GitHub', connected: true, icon: '🐙' },
  ]

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>External Integrations</h3>
        <p>Connect to external services and tools</p>
      </div>
      <div className={styles.integrationsList}>
        {integrations.map(integration => (
          <div key={integration.name} className={styles.integrationCard}>
            <span className={styles.integrationIcon}>{integration.icon}</span>
            <div className={styles.integrationInfo}>
              <span className={styles.integrationName}>{integration.name}</span>
              <Badge variant={integration.connected ? 'success' : 'default'}>
                {integration.connected ? 'Connected' : 'Not connected'}
              </Badge>
            </div>
            <Button variant="secondary" size="sm">
              {integration.connected ? 'Manage' : 'Connect'}
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
