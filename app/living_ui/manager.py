"""
Living UI Manager

Manages the lifecycle of Living UI projects:
- Project creation from template
- Project launching and stopping
- Port allocation
- State tracking
- Startup auto-launch
- Task creation with trigger firing
"""

import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.task.task_manager import TaskManager
    from app.trigger import TriggerQueue

logger = logging.getLogger(__name__)


@dataclass
class LivingUIProject:
    """Represents a Living UI project."""
    id: str
    name: str
    description: str
    path: str
    status: str = 'created'  # created, creating, ready, running, stopped, error
    port: Optional[int] = None
    backend_port: Optional[int] = None
    url: Optional[str] = None
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    features: List[str] = field(default_factory=list)
    theme: str = 'system'
    error: Optional[str] = None
    task_id: Optional[str] = None
    process: Optional[subprocess.Popen] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'status': self.status,
            'port': self.port,
            'url': self.url,
            'createdAt': int(self.created_at * 1000),  # Convert to JS timestamp
            'features': self.features,
            'theme': self.theme,
            'error': self.error,
        }


class LivingUIManager:
    """Manages Living UI project lifecycle."""

    def __init__(self, workspace_root: Path, template_path: Path):
        """
        Initialize the Living UI Manager.

        Args:
            workspace_root: Root directory for Living UI projects
            template_path: Path to the Living UI template
        """
        self.workspace_root = Path(workspace_root)
        self.template_path = Path(template_path)
        self.projects: Dict[str, LivingUIProject] = {}
        self._next_port = 3100
        self._port_range = (3100, 3199)
        self._used_ports: set = set()
        self._projects_file = self.workspace_root / 'living_ui_projects.json'

        # Task and trigger management (set via bind_task_manager)
        self._task_manager: Optional["TaskManager"] = None
        self._trigger_queue: Optional["TriggerQueue"] = None

        # Ensure workspace directory exists
        self.living_ui_dir = self.workspace_root / 'living_ui'
        self.living_ui_dir.mkdir(parents=True, exist_ok=True)

        # Load existing projects
        self._load_projects()

    def bind_task_manager(
        self,
        task_manager: "TaskManager",
        trigger_queue: "TriggerQueue"
    ) -> None:
        """
        Bind the task manager and trigger queue for creating development tasks.

        Args:
            task_manager: TaskManager instance for creating tasks
            trigger_queue: TriggerQueue instance for firing triggers
        """
        self._task_manager = task_manager
        self._trigger_queue = trigger_queue
        logger.info("[LIVING_UI] Task manager and trigger queue bound")

    def _load_projects(self) -> None:
        """Load projects from persistent storage."""
        if self._projects_file.exists():
            try:
                with open(self._projects_file, 'r') as f:
                    data = json.load(f)
                    for project_data in data.get('projects', []):
                        project = LivingUIProject(
                            id=project_data['id'],
                            name=project_data['name'],
                            description=project_data.get('description', ''),
                            path=project_data['path'],
                            status=project_data.get('status', 'stopped'),
                            port=project_data.get('port'),
                            created_at=project_data.get('createdAt', datetime.now().timestamp()) / 1000,
                            features=project_data.get('features', []),
                            theme=project_data.get('theme', 'system'),
                        )
                        # Reset status to stopped for all loaded projects
                        project.status = 'stopped' if project.status == 'running' else project.status
                        self.projects[project.id] = project
                        if project.port:
                            self._used_ports.add(project.port)
                logger.info(f"[LIVING_UI] Loaded {len(self.projects)} projects")
            except Exception as e:
                logger.error(f"[LIVING_UI] Failed to load projects: {e}")

    def _save_projects(self) -> None:
        """Save projects to persistent storage."""
        try:
            data = {
                'projects': [p.to_dict() for p in self.projects.values()]
            }
            with open(self._projects_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[LIVING_UI] Failed to save projects: {e}")

    def _allocate_port(self) -> int:
        """Allocate a free port for a Living UI project.

        Checks both the internal tracking set AND actual system port usage
        to avoid conflicts with orphan processes.
        """
        for port in range(self._port_range[0], self._port_range[1] + 1):
            # Skip if tracked as used
            if port in self._used_ports:
                continue
            # Skip if actually in use on the system
            if self._is_port_in_use(port):
                logger.warning(f"[LIVING_UI] Port {port} in use by external process, skipping")
                continue
            self._used_ports.add(port)
            return port
        raise RuntimeError("No available ports in the Living UI port range")

    def _release_port(self, port: int) -> None:
        """Release a port back to the pool."""
        self._used_ports.discard(port)

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is actually in use on the system."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('localhost', port)) == 0

    def _get_pids_on_ports(self, ports_to_check: Optional[Set[int]] = None) -> Dict[int, str]:
        """
        Get PIDs of processes listening on ports in the Living UI range.
        Uses a single system call for efficiency.

        Args:
            ports_to_check: Optional set of specific ports to check.
                           If None, checks all ports in the Living UI range.

        Returns:
            Dict mapping port numbers to PIDs
        """
        port_pids = {}

        if os.name == 'nt':
            # Windows: run netstat once and parse all results
            try:
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            addr = parts[1]
                            pid = parts[-1]
                            if ':' in addr:
                                try:
                                    port = int(addr.split(':')[-1])
                                    # Check if port is in range and optionally in the filter set
                                    if self._port_range[0] <= port <= self._port_range[1]:
                                        if ports_to_check is None or port in ports_to_check:
                                            port_pids[port] = pid
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"[LIVING_UI] Failed to get ports via netstat: {e}")
        else:
            # Linux/Mac: use lsof
            try:
                result = subprocess.run(
                    ['lsof', '-i', '-P', '-n'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'LISTEN' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            # PID is typically the second column
                            pid = parts[1]
                            # Find the port in the line
                            for part in parts:
                                if ':' in part:
                                    try:
                                        port = int(part.split(':')[-1])
                                        if self._port_range[0] <= port <= self._port_range[1]:
                                            if ports_to_check is None or port in ports_to_check:
                                                port_pids[port] = pid
                                                break
                                    except ValueError:
                                        pass
            except Exception as e:
                logger.warning(f"[LIVING_UI] Failed to get ports via lsof: {e}")

        return port_pids

    def _kill_process_by_pid(self, pid: str) -> bool:
        """
        Kill a process by its PID.

        Args:
            pid: Process ID to kill

        Returns:
            True if process was killed, False otherwise
        """
        try:
            if os.name == 'nt':
                subprocess.run(
                    ['taskkill', '/F', '/PID', pid],
                    capture_output=True,
                    shell=True
                )
            else:
                subprocess.run(['kill', '-9', pid], capture_output=True)
            return True
        except Exception as e:
            logger.warning(f"[LIVING_UI] Failed to kill process {pid}: {e}")
            return False

    async def _wait_for_server(self, port: int, timeout: int = 10) -> bool:
        """
        Wait for a server to start listening on a port.

        Args:
            port: The port to check
            timeout: Maximum seconds to wait

        Returns:
            True if server is responding, False if timeout
        """
        for _ in range(timeout * 2):
            if self._is_port_in_use(port):
                return True
            await asyncio.sleep(0.5)
        return False

    def _kill_process_on_port(self, port: int) -> bool:
        """
        Kill any process listening on the specified port (Windows-specific).

        Args:
            port: The port to free

        Returns:
            True if a process was killed, False otherwise
        """
        if os.name != 'nt':
            # Linux/Mac: use lsof and kill
            try:
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                    logger.info(f"[LIVING_UI] Killed process(es) on port {port}")
                    return True
            except Exception as e:
                logger.warning(f"[LIVING_UI] Failed to kill process on port {port}: {e}")
            return False
        else:
            # Windows: use netstat and taskkill
            try:
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                shell=True
                            )
                            logger.info(f"[LIVING_UI] Killed process {pid} on port {port}")
                            return True
            except Exception as e:
                logger.warning(f"[LIVING_UI] Failed to kill process on port {port}: {e}")
            return False

    def cleanup_on_startup(self) -> None:
        """
        Clean up orphan processes and folders on startup.

        This should be called after loading projects to:
        1. Kill any orphan Living UI server processes on tracked ports
        2. Delete project folders not tracked in the registry
        3. Reset all project statuses to 'stopped'

        Optimized to:
        - Only check ports that are tracked in projects (not all 100 ports)
        - Use a single netstat call to get all port info at once
        """
        logger.info("[LIVING_UI] Running startup cleanup...")

        # 1. Kill orphan processes - only on ports tracked by projects
        killed_count = 0
        tracked_ports = {p.port for p in self.projects.values() if p.port}

        if tracked_ports:
            # Get all port -> PID mappings with a single system call
            port_pids = self._get_pids_on_ports(tracked_ports)

            # Kill processes on tracked ports
            for port, pid in port_pids.items():
                if self._kill_process_by_pid(pid):
                    killed_count += 1
                    logger.info(f"[LIVING_UI] Killed process {pid} on port {port}")

        if killed_count > 0:
            logger.info(f"[LIVING_UI] Killed {killed_count} orphan process(es)")

        # 2. Clean up orphan project folders
        orphan_count = self._cleanup_orphan_folders()
        if orphan_count > 0:
            logger.info(f"[LIVING_UI] Removed {orphan_count} orphan folder(s)")

        # 3. Reset all project statuses to 'stopped'
        for project in self.projects.values():
            if project.status == 'running':
                project.status = 'stopped'
                project.process = None
        self._save_projects()

        logger.info("[LIVING_UI] Startup cleanup complete")

    def _cleanup_orphan_folders(self) -> int:
        """
        Delete project folders that are not tracked in the registry.

        Returns:
            Number of orphan folders deleted
        """
        if not self.living_ui_dir.exists():
            return 0

        tracked_paths = {Path(p.path) for p in self.projects.values()}
        orphan_count = 0

        for folder in self.living_ui_dir.iterdir():
            if folder.is_dir() and folder not in tracked_paths:
                try:
                    shutil.rmtree(folder)
                    logger.info(f"[LIVING_UI] Deleted orphan folder: {folder.name}")
                    orphan_count += 1
                except Exception as e:
                    logger.warning(f"[LIVING_UI] Failed to delete orphan folder {folder}: {e}")

        return orphan_count

    def _generate_id(self) -> str:
        """Generate a unique project ID."""
        return str(uuid.uuid4())[:8]

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for use in file paths."""
        # Replace spaces and special characters
        sanitized = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        return sanitized.lower()

    async def create_project(
        self,
        name: str,
        description: str,
        features: List[str] = None,
        data_source: Optional[str] = None,
        theme: str = 'system'
    ) -> LivingUIProject:
        """
        Create a new Living UI project from template.

        Args:
            name: Project name
            description: Project description
            features: List of requested features
            data_source: Optional API URL or data source description
            theme: UI theme (light, dark, system)

        Returns:
            Created LivingUIProject instance
        """
        project_id = self._generate_id()
        sanitized_name = self._sanitize_name(name)
        project_path = self.living_ui_dir / f"{sanitized_name}_{project_id}"

        # Allocate ports
        frontend_port = self._allocate_port()
        backend_port = self._allocate_port()

        # Copy template
        try:
            shutil.copytree(self.template_path, project_path)
            logger.info(f"[LIVING_UI] Copied template to {project_path}")
        except Exception as e:
            self._release_port(frontend_port)
            self._release_port(backend_port)
            raise RuntimeError(f"Failed to copy template: {e}")

        # Replace template placeholders
        self._replace_placeholders(project_path, {
            '{{PROJECT_ID}}': project_id,
            '{{PROJECT_NAME}}': name,
            '{{PROJECT_DESCRIPTION}}': description,
            '{{PORT}}': str(frontend_port),
            '{{BACKEND_PORT}}': str(backend_port),
            '{{THEME}}': theme,
            '{{CREATED_AT}}': datetime.now().isoformat(),
            '{{FEATURES}}': ', '.join(features or []),
        })

        # Create project instance
        project = LivingUIProject(
            id=project_id,
            name=name,
            description=description,
            path=str(project_path),
            status='created',
            port=frontend_port,
            backend_port=backend_port,
            features=features or [],
            theme=theme,
        )

        self.projects[project_id] = project
        self._save_projects()

        logger.info(f"[LIVING_UI] Created project: {name} ({project_id})")
        return project

    def _replace_placeholders(self, directory: Path, replacements: Dict[str, str]) -> None:
        """Replace placeholders in all text files in directory."""
        text_extensions = {'.ts', '.tsx', '.js', '.jsx', '.json', '.html', '.css', '.md', '.py', '.txt', '.env'}

        for filepath in directory.rglob('*'):
            if filepath.is_file() and filepath.suffix in text_extensions:
                try:
                    content = filepath.read_text(encoding='utf-8')
                    modified = False
                    for placeholder, value in replacements.items():
                        if placeholder in content:
                            content = content.replace(placeholder, value)
                            modified = True
                    if modified:
                        filepath.write_text(content, encoding='utf-8')
                except Exception as e:
                    logger.warning(f"[LIVING_UI] Failed to process {filepath}: {e}")

    def update_project_status(self, project_id: str, status: str, error: Optional[str] = None) -> None:
        """Update project status."""
        if project_id in self.projects:
            self.projects[project_id].status = status
            if error:
                self.projects[project_id].error = error
            self._save_projects()

    def set_project_task(self, project_id: str, task_id: str) -> None:
        """Associate a task ID with a project."""
        if project_id in self.projects:
            self.projects[project_id].task_id = task_id

    async def create_development_task(self, project_id: str) -> Optional[str]:
        """
        Create a task for the agent to develop a Living UI and fire the trigger.

        This creates the task and immediately fires a trigger to start execution.
        The pattern follows how memory processing and scheduled tasks work.

        Args:
            project_id: The Living UI project ID to develop

        Returns:
            The task ID if successful, None otherwise
        """
        from app.trigger import Trigger

        project = self.projects.get(project_id)
        if not project:
            logger.error(f"[LIVING_UI] Project not found: {project_id}")
            return None

        if not self._task_manager:
            logger.error("[LIVING_UI] Task manager not bound")
            return None

        if not self._trigger_queue:
            logger.error("[LIVING_UI] Trigger queue not bound")
            return None

        # Build the task instruction
        features_str = ', '.join(project.features) if project.features else 'None specified'
        task_instruction = f"""Create a Living UI application.

Project ID: {project.id}
Project Name: {project.name}
Description: {project.description}
Features: {features_str}
Theme: {project.theme}
Project Path: {project.path}

Follow the living-ui-creator skill instructions to scaffold, develop, test, and launch this UI.
When complete, use the living_ui_notify_ready action to notify the browser."""

        try:
            # Create the task (synchronous method)
            # Include living_ui action set so agent can call living_ui_notify_ready
            task_id = self._task_manager.create_task(
                task_name=f"Create Living UI: {project.name}",
                task_instruction=task_instruction,
                mode="complex",
                action_sets=["file_operations", "code_execution", "living_ui"],
                selected_skills=["living-ui-creator"],
            )

            # Associate task with project
            self.set_project_task(project_id, task_id)

            # Update project status
            self.update_project_status(project_id, "creating")

            # Create and fire the trigger to start execution
            trigger = Trigger(
                fire_at=time.time(),
                priority=50,
                next_action_description=f"[Living UI] Create: {project.name}",
                session_id=task_id,
                payload={
                    "type": "living_ui_development",
                    "project_id": project_id,
                },
            )
            await self._trigger_queue.put(trigger)

            logger.info(f"[LIVING_UI] Created task {task_id} and fired trigger for project {project_id}")
            return task_id

        except Exception as e:
            logger.error(f"[LIVING_UI] Failed to create development task: {e}")
            self.update_project_status(project_id, "error", str(e))
            return None

    async def launch_project(self, project_id: str) -> bool:
        """
        Launch a Living UI project.

        Args:
            project_id: Project ID to launch

        Returns:
            True if launch was successful
        """
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"[LIVING_UI] Project not found: {project_id}")
            return False

        if project.status == 'running':
            logger.info(f"[LIVING_UI] Project already running: {project_id}")
            return True

        project_path = Path(project.path)
        if not project_path.exists():
            logger.error(f"[LIVING_UI] Project path not found: {project.path}")
            project.status = 'error'
            project.error = 'Project directory not found'
            return False

        try:
            # Check if npm dependencies are installed
            node_modules = project_path / 'node_modules'
            if not node_modules.exists():
                logger.info(f"[LIVING_UI] Installing dependencies for {project_id}")
                install_process = await asyncio.create_subprocess_exec(
                    'npm', 'install',
                    cwd=str(project_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await install_process.wait()

            # Get the port (use assigned port or allocate new one)
            port = project.port or self._allocate_port()

            # Check if port is already in use and try to free it
            if self._is_port_in_use(port):
                logger.warning(f"[LIVING_UI] Port {port} already in use, attempting to free it")
                self._kill_process_on_port(port)
                await asyncio.sleep(1)  # Wait for port to be released

                # Double check it's free now
                if self._is_port_in_use(port):
                    logger.error(f"[LIVING_UI] Could not free port {port}")
                    project.status = 'error'
                    project.error = f'Port {port} is occupied by another process'
                    self._save_projects()
                    return False

            # Start the preview server
            logger.info(f"[LIVING_UI] Starting server for {project_id} on port {port}")
            process = subprocess.Popen(
                ['npm', 'run', 'preview', '--', '--port', str(port)],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True if os.name == 'nt' else False,
            )

            project.process = process
            project.port = port

            # Wait for server to actually start and verify it's responding
            logger.info(f"[LIVING_UI] Waiting for server to start on port {port}...")
            server_ready = await self._wait_for_server(port, timeout=15)

            if not server_ready:
                # Server didn't start - check if process died
                if process.poll() is not None:
                    # Process exited
                    stderr = process.stderr.read().decode() if process.stderr else ''
                    logger.error(f"[LIVING_UI] Server process exited: {stderr[:500]}")
                    project.status = 'error'
                    project.error = f'Server failed to start: {stderr[:200]}'
                else:
                    # Process running but not responding
                    logger.error(f"[LIVING_UI] Server not responding on port {port}")
                    process.terminate()
                    project.status = 'error'
                    project.error = f'Server started but not responding on port {port}'
                project.process = None
                self._save_projects()
                return False

            # Server is up and running
            project.url = f"http://localhost:{port}"
            project.status = 'running'
            project.error = None

            self._save_projects()
            logger.info(f"[LIVING_UI] Successfully launched project {project_id} on port {port}")
            return True

        except Exception as e:
            logger.error(f"[LIVING_UI] Failed to launch project {project_id}: {e}")
            project.status = 'error'
            project.error = str(e)
            self._save_projects()
            return False

    async def stop_project(self, project_id: str) -> bool:
        """
        Stop a running Living UI project.

        Args:
            project_id: Project ID to stop

        Returns:
            True if stop was successful
        """
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"[LIVING_UI] Project not found: {project_id}")
            return False

        if project.process:
            try:
                project.process.terminate()
                project.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                project.process.kill()
            project.process = None

        project.status = 'stopped'
        project.url = None
        self._save_projects()

        logger.info(f"[LIVING_UI] Stopped project: {project_id}")
        return True

    async def delete_project(self, project_id: str) -> bool:
        """
        Delete a Living UI project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if deletion was successful
        """
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"[LIVING_UI] Project not found: {project_id}")
            return False

        # Stop if running
        if project.status == 'running':
            await self.stop_project(project_id)

        # Release ports
        if project.port:
            self._release_port(project.port)
        if project.backend_port:
            self._release_port(project.backend_port)

        # Delete project directory
        project_path = Path(project.path)
        if project_path.exists():
            try:
                shutil.rmtree(project_path)
            except Exception as e:
                logger.error(f"[LIVING_UI] Failed to delete project directory: {e}")

        # Remove from registry
        del self.projects[project_id]
        self._save_projects()

        logger.info(f"[LIVING_UI] Deleted project: {project_id}")
        return True

    def get_project(self, project_id: str) -> Optional[LivingUIProject]:
        """Get a project by ID."""
        return self.projects.get(project_id)

    def list_projects(self) -> List[LivingUIProject]:
        """List all projects."""
        return list(self.projects.values())

    def get_project_url(self, project_id: str) -> Optional[str]:
        """Get the URL for a running project."""
        project = self.projects.get(project_id)
        if project and project.status == 'running':
            return project.url
        return None

    async def auto_launch_projects(self, project_ids: List[str]) -> None:
        """Auto-launch specified projects on startup."""
        for project_id in project_ids:
            project = self.projects.get(project_id)
            if project and project.status != 'error':
                logger.info(f"[LIVING_UI] Auto-launching: {project_id}")
                await self.launch_project(project_id)
