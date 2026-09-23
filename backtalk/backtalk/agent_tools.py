# backtalk: local PC agent tools module.
# 100% On-Device execution: coding, email drafting, app/game launching, system automation, and vault memory.
import os
import re
import sys
import time
import json
import subprocess
import datetime
import psutil
from pathlib import Path

VAULT_DIR = Path("C:/Users/saisi/jarvis-vault")
WORKSPACE_DIR = Path("C:/Users/saisi/my-agent/workspace")

# Ensure required directories exist
VAULT_DIR.mkdir(parents=True, exist_ok=True)
(VAULT_DIR / "Drafts").mkdir(parents=True, exist_ok=True)
(VAULT_DIR / "Screenshots").mkdir(parents=True, exist_ok=True)
(VAULT_DIR / "Code").mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def execute_shell_or_script(command: str, cwd: str | None = None) -> str:
    """Executes a local command or script and returns the result."""
    work_dir = cwd or str(WORKSPACE_DIR)
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        out = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        if res.returncode == 0:
            return out if out else "Command executed successfully with no output."
        return f"Execution error (code {res.returncode}): {err or out}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Failed to execute command: {e}"


def write_code_file(filename: str, content: str, folder: str | None = None) -> str:
    """Writes a code file to the local workspace or vault."""
    target_dir = Path(folder) if folder else (VAULT_DIR / "Code")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / filename
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Code saved to {target_file.name} in your local vault."
    except Exception as e:
        return f"Failed to save code file: {e}"


def run_python_code(code: str) -> str:
    """Executes Python code in a safe local sub-process."""
    temp_script = WORKSPACE_DIR / "temp_exec.py"
    try:
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(code)
        
        py_exe = sys.executable
        res = subprocess.run(
            [py_exe, str(temp_script)],
            cwd=str(WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=25
        )
        out = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        if res.returncode == 0:
            return f"Output:\n{out}" if out else "Script executed cleanly with no standard output."
        return f"Error (code {res.returncode}):\n{err or out}"
    except Exception as e:
        return f"Python execution failed: {e}"


def draft_email(to_recipient: str, subject: str, body: str) -> str:
    """Drafts an email, saves it to the Obsidian Drafts vault, and creates a mailto link."""
    drafts_dir = VAULT_DIR / "Drafts"
    safe_sub = re.sub(r'[\\/*?:"<>|]', "", subject).replace(" ", "_")[:40] or "Draft"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_file = drafts_dir / f"Email_{safe_sub}_{timestamp}.md"
    
    content = f"""---
to: "{to_recipient}"
subject: "{subject}"
created: "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
status: "draft"
---

# Email Draft

**To:** `{to_recipient}`  
**Subject:** {subject}  
**Date:** {datetime.datetime.now().strftime('%B %d, %Y %I:%M %p')}  

---

{body}

---
*Drafted by Jarvis AI Agent for Sai.*
"""
    try:
        with open(draft_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Email draft for {to_recipient} with subject '{subject}' has been saved to your Obsidian Drafts vault."
    except Exception as e:
        return f"Failed saving email draft: {e}"


def take_screenshot() -> str:
    """Captures a screenshot of the primary display and saves it to the vault."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_path = VAULT_DIR / "Screenshots" / f"Screenshot_{timestamp}.png"
    try:
        from PIL import ImageGrab
        im = ImageGrab.grab()
        im.save(str(shot_path))
        return f"Screenshot captured and saved to your vault at Screenshots/Screenshot_{timestamp}.png"
    except Exception:
        # Fallback using PowerShell
        ps_cmd = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphic = [System.Drawing.Graphics]::FromImage($bitmap)
$graphic.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{str(shot_path).replace('\\', '/')}', [System.Drawing.Imaging.ImageFormat]::Png)
"""
        execute_shell_or_script(ps_cmd)
        if shot_path.exists():
            return f"Screenshot saved to vault at Screenshots/{shot_path.name}"
        return "Could not capture screenshot on current display."


def launch_application_or_game(app_name: str) -> str:
    """Launches local desktop applications, games, or launchers."""
    name_low = app_name.lower().strip()
    
    app_map = {
        "spotify": "spotify",
        "discord": "discord",
        "steam": "steam",
        "chrome": "chrome",
        "brave": "brave",
        "edge": "msedge",
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "code": "code",
        "vs code": "code",
        "vscode": "code",
        "explorer": "explorer",
        "terminal": "wt",
        "powershell": "powershell",
        "obsidian": "obsidian",
        "task manager": "taskmgr",
        "taskmgr": "taskmgr",
    }
    
    target = app_map.get(name_low, name_low)
    try:
        subprocess.Popen(["cmd", "/c", "start", "", target], shell=True)
        return f"Launching {app_name}, sir."
    except Exception as e:
        return f"Could not launch {app_name}: {e}"


def get_system_diagnostics() -> str:
    """Returns detailed hardware, process, and battery metrics."""
    cpu_pct = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    battery = psutil.sensors_battery()
    bat_str = f", battery is at {int(battery.percent)} percent" if battery else ""
    
    return (
        f"All core systems operational, Sai. CPU is at {cpu_pct} percent, "
        f"RAM utilization is at {mem.percent} percent with {mem.available // (1024*1024*1024)} gigabytes free, "
        f"and C drive has {disk.free // (1024*1024*1024)} gigabytes remaining{bat_str}."
    )


def list_running_apps() -> list[str]:
    """Lists notable running application processes."""
    notable = []
    for proc in psutil.process_iter(['name']):
        try:
            n = proc.info['name']
            if n and n.endswith('.exe') and not n.startswith(('svchost', 'System', 'Registry', 'smss', 'csrss')):
                base = n[:-4]
                if base.lower() not in [x.lower() for x in notable] and len(base) > 2:
                    notable.append(base)
        except Exception:
            pass
    return sorted(notable[:20])


def organize_folder(target_folder: str = "downloads") -> str:
    """Organizes files in Downloads, Desktop, or Documents into categorized subfolders."""
    import shutil
    user_home = Path.home()
    folder_map = {
        "downloads": user_home / "Downloads",
        "download": user_home / "Downloads",
        "desktop": user_home / "Desktop",
        "documents": user_home / "Documents",
        "workspace": WORKSPACE_DIR,
    }
    tf_low = target_folder.lower().strip()
    target_path = folder_map.get(tf_low, Path(target_folder))
    if not target_path.exists() or not target_path.is_dir():
        return f"Folder '{target_folder}' does not exist on your system."
    
    categories = {
        "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"},
        "Documents": {".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv", ".md"},
        "Code_Projects": {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".bat", ".ps1", ".c", ".cpp", ".rs"},
        "Installers_Archives": {".exe", ".msi", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso"},
        "Audio_Video": {".mp3", ".wav", ".mp4", ".mkv", ".mov", ".flac", ".avi"},
    }
    
    moved_counts = {}
    total_moved = 0
    
    for item in list(target_path.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            ext = item.suffix.lower()
            dest_category = None
            for cat_name, extensions in categories.items():
                if ext in extensions:
                    dest_category = cat_name
                    break
            if dest_category:
                cat_dir = target_path / dest_category
                cat_dir.mkdir(exist_ok=True)
                dest_file = cat_dir / item.name
                if dest_file.exists():
                    dest_file = cat_dir / f"{item.stem}_{int(time.time())}{item.suffix}"
                try:
                    shutil.move(str(item), str(dest_file))
                    moved_counts[dest_category] = moved_counts.get(dest_category, 0) + 1
                    total_moved += 1
                except Exception:
                    pass
    if total_moved == 0:
        return f"Your {target_path.name} folder is already clean and organized."
    
    summary_parts = [f"{count} in {cat}" for cat, count in moved_counts.items()]
    return f"Organized {total_moved} files in {target_path.name}: {', '.join(summary_parts)}."


def send_agent_input(task_text: str, target: str = "tasks") -> str:
    """Logs inputs, instructions, or tasks to the workspace and system clipboard."""
    tasks_file = WORKSPACE_DIR / "agent_inputs.md"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] {task_text}\n"
    try:
        with open(tasks_file, "a", encoding="utf-8") as f:
            f.write(entry)
        try:
            ps_cmd = f"Set-Clipboard -Value '{task_text.replace('\'', '\'\'')}'"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        except Exception:
            pass
        return f"Logged task: '{task_text}', and copied it to your clipboard."
    except Exception as e:
        return f"Failed saving task: {e}"
