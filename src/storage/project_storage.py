"""Project storage for data persistence."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..models.project import Project


class ProjectStorage:
    """Handles saving and loading projects to/from disk."""

    DEFAULT_DATA_DIR = "data/projects"

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize storage with optional custom data directory."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Use default relative to package
            self.data_dir = Path(__file__).parent.parent.parent / self.DEFAULT_DATA_DIR

        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_path(self, project_id: str) -> Path:
        """Get the file path for a project."""
        # Sanitize project_id for filename
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_id)
        return self.data_dir / f"{safe_id}.json"

    def save(self, project: Project) -> Path:
        """Save a project to disk."""
        project.updated_at = datetime.now()
        file_path = self._get_project_path(project.id)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(project.model_dump_for_storage(), f, indent=2, default=str)

        return file_path

    def load(self, project_id: str) -> Optional[Project]:
        """Load a project from disk."""
        file_path = self._get_project_path(project_id)

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Project.from_storage(data)

    def delete(self, project_id: str) -> bool:
        """Delete a project from disk."""
        file_path = self._get_project_path(project_id)

        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_projects(self) -> list[dict]:
        """List all saved projects with basic info."""
        projects = []

        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    projects.append({
                        "id": data.get("id", file_path.stem),
                        "company_name": data.get("company_name", "Unknown"),
                        "project_name": data.get("project_name", ""),
                        "location": data.get("location", ""),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "headcount": sum(
                            sum(s.get("count", 0) for s in d.get("staff", []))
                            for d in data.get("departments", [])
                        ),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by updated_at descending
        projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return projects

    def exists(self, project_id: str) -> bool:
        """Check if a project exists."""
        return self._get_project_path(project_id).exists()

    def search(self, query: str) -> list[dict]:
        """Search projects by company name, project name, or location."""
        query_lower = query.lower()
        all_projects = self.list_projects()

        return [
            p for p in all_projects
            if query_lower in p.get("company_name", "").lower()
            or query_lower in p.get("project_name", "").lower()
            or query_lower in p.get("location", "").lower()
        ]

    def export_all(self, output_path: Path) -> Path:
        """Export all projects to a single JSON file."""
        all_projects = []

        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    all_projects.append(json.load(f))
            except json.JSONDecodeError:
                continue

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"projects": all_projects, "exported_at": datetime.now().isoformat()}, f, indent=2)

        return output_path

    def import_projects(self, input_path: Path) -> int:
        """Import projects from a JSON export file."""
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported_count = 0
        projects = data.get("projects", [])

        for project_data in projects:
            try:
                project = Project.from_storage(project_data)
                self.save(project)
                imported_count += 1
            except Exception:
                continue

        return imported_count


def generate_project_id(company_name: str) -> str:
    """Generate a unique project ID from company name."""
    # Create base ID from company name
    base = "".join(c if c.isalnum() else "-" for c in company_name.lower())
    base = "-".join(filter(None, base.split("-")))[:30]  # Clean up and limit length

    # Add timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base}-{timestamp}"
