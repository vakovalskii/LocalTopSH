"""Skills management - Anthropic-style skill system"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

# Config paths
SKILLS_CACHE = "/data/skills_cache.json"
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")
SHARED_SKILLS_DIR = "/data/skills"

# Available skills from Anthropic's repository
ANTHROPIC_SKILLS = {
    "pptx": "Create PowerPoint presentations",
    "docx": "Create and edit Word documents",
    "xlsx": "Work with Excel spreadsheets",
    "pdf": "Work with PDF files",
    "canvas-design": "Create visual designs",
    "frontend-design": "Frontend UI/UX design",
    "webapp-testing": "Test web applications",
    "mcp-builder": "Build MCP servers",
    "skill-creator": "Create new skills",
    "algorithmic-art": "Generate algorithmic art",
    "brand-guidelines": "Create brand guidelines",
    "doc-coauthoring": "Collaborative document editing",
    "internal-comms": "Internal communications",
    "slack-gif-creator": "Create Slack GIFs",
    "theme-factory": "Create themes",
    "web-artifacts-builder": "Build web artifacts"
}


class Skill(BaseModel):
    """Skill definition - like Anthropic's Skills"""
    name: str
    description: str
    version: str = "1.0"
    author: Optional[str] = None
    
    # Skill can provide:
    tools: List[dict] = []           # Custom tools
    system_prompt: Optional[str] = None  # Additional system prompt
    resources: List[str] = []        # Files/URLs to include in context
    commands: Dict[str, str] = {}    # Slash commands
    
    # Metadata
    enabled: bool = True
    source: str = "user"  # user, shared, marketplace
    path: Optional[str] = None


class SkillsManager:
    """Manages skills loaded from user workspaces and shared directory"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.skill_tools: Dict[str, dict] = {}  # Flattened tools from all skills
        self.last_scan: Optional[datetime] = None
    
    def load_cache(self):
        """Load skills cache from file"""
        if os.path.exists(SKILLS_CACHE):
            try:
                with open(SKILLS_CACHE) as f:
                    data = json.load(f)
                    for name, skill_data in data.get("skills", {}).items():
                        self.skills[name] = Skill(**skill_data)
                    self.skill_tools = data.get("skill_tools", {})
                    self.last_scan = datetime.fromisoformat(data["last_scan"]) if data.get("last_scan") else None
            except Exception as e:
                print(f"Error loading skills cache: {e}")
    
    def save_cache(self):
        """Save skills cache to file"""
        os.makedirs(os.path.dirname(SKILLS_CACHE), exist_ok=True)
        with open(SKILLS_CACHE, 'w') as f:
            json.dump({
                "skills": {name: skill.dict() for name, skill in self.skills.items()},
                "skill_tools": self.skill_tools,
                "last_scan": self.last_scan.isoformat() if self.last_scan else None
            }, f, indent=2)
    
    def scan_directory(self, directory: str, source: str = "user") -> List[Skill]:
        """Scan directory for skill.json files"""
        found_skills = []
        
        if not os.path.exists(directory):
            return found_skills
        
        # Look for skill.json in immediate subdirectories
        for item in os.listdir(directory):
            skill_dir = os.path.join(directory, item)
            skill_file = os.path.join(skill_dir, "skill.json")
            
            if os.path.isdir(skill_dir) and os.path.exists(skill_file):
                try:
                    with open(skill_file) as f:
                        data = json.load(f)
                        
                        # Load system_prompt from file if specified
                        system_prompt = data.get("system_prompt")
                        if data.get("system_prompt_file"):
                            prompt_file = os.path.join(skill_dir, data["system_prompt_file"])
                            if os.path.exists(prompt_file):
                                with open(prompt_file) as pf:
                                    system_prompt = pf.read()
                        
                        skill = Skill(
                            name=data.get("name", item),
                            description=data.get("description", ""),
                            version=data.get("version", "1.0"),
                            author=data.get("author"),
                            tools=data.get("tools", []),
                            system_prompt=system_prompt,
                            resources=data.get("resources", []),
                            commands=data.get("commands", {}),
                            enabled=data.get("enabled", True),
                            source=source,
                            path=skill_dir
                        )
                        found_skills.append(skill)
                except Exception as e:
                    print(f"Error loading skill from {skill_file}: {e}")
        
        return found_skills
    
    def scan_user_workspace(self, user_id: str) -> List[Skill]:
        """Scan user's workspace for skills"""
        user_skills_dir = os.path.join(WORKSPACE_ROOT, user_id, "skills")
        return self.scan_directory(user_skills_dir, source=f"user:{user_id}")
    
    def scan_shared_skills(self) -> List[Skill]:
        """Scan shared skills directory"""
        return self.scan_directory(SHARED_SKILLS_DIR, source="shared")
    
    def scan_all(self, user_id: Optional[str] = None):
        """Scan all skill sources and update cache"""
        self.skills.clear()
        self.skill_tools.clear()
        
        # 1. Load shared skills
        for skill in self.scan_shared_skills():
            self.skills[f"shared:{skill.name}"] = skill
        
        # 2. Load user skills (if user_id provided)
        if user_id:
            for skill in self.scan_user_workspace(user_id):
                self.skills[f"user:{skill.name}"] = skill
        
        # 3. Flatten tools from all enabled skills
        for skill_key, skill in self.skills.items():
            if skill.enabled:
                for tool in skill.tools:
                    tool_name = f"skill_{skill.name}_{tool['name']}"
                    self.skill_tools[tool_name] = {
                        "name": tool_name,
                        "original_name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                        "source": f"skill:{skill.name}",
                        "skill": skill.name,
                        "enabled": True
                    }
        
        self.last_scan = datetime.now()
        self.save_cache()
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name"""
        # Try exact match first
        if name in self.skills:
            return self.skills[name]
        # Try without prefix
        for key, skill in self.skills.items():
            if skill.name == name:
                return skill
        return None
    
    def get_enabled_tools(self) -> Dict[str, dict]:
        """Get all enabled tools from skills"""
        return {name: tool for name, tool in self.skill_tools.items() if tool.get("enabled", True)}
    
    def get_system_prompts(self) -> List[str]:
        """Get all system prompts from enabled skills - FULL VERSION (deprecated)"""
        prompts = []
        for skill in self.skills.values():
            if skill.enabled and skill.system_prompt:
                prompts.append(f"# Skill: {skill.name}\n{skill.system_prompt}")
        return prompts
    
    def get_skill_mentions(self) -> str:
        """Get skill mentions for system prompt (name + description only)
        
        Agent should use list_directory/read_file to load full instructions when needed.
        Skills are available at /data/skills/{name}/ or user workspace /workspace/{user_id}/skills/
        """
        if not self.skills:
            return ""
        
        lines = ["## Available Skills", ""]
        lines.append("When user requests something that matches a skill, load its instructions:")
        lines.append("1. `list_directory` on `/data/skills/{skill_name}/`")
        lines.append("2. `read_file` the SKILL.md or relevant .md files")
        lines.append("3. Follow the loaded instructions")
        lines.append("")
        lines.append("| Skill | Description |")
        lines.append("|-------|-------------|")
        
        for skill in self.skills.values():
            if skill.enabled:
                # Truncate description to ~80 chars
                desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
                lines.append(f"| `{skill.name}` | {desc} |")
        
        return "\n".join(lines)


# Global skills manager
skills_manager = SkillsManager()
