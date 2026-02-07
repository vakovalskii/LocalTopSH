"""Skills management routes"""

import os
import shutil
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..skills import skills_manager, Skill, ANTHROPIC_SKILLS, SHARED_SKILLS_DIR
from ..config import load_config, save_config

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
async def list_skills(user_id: Optional[str] = None):
    """List all loaded skills"""
    skills_manager.scan_all(user_id)
    
    skills_list = []
    for key, skill in skills_manager.skills.items():
        skills_list.append({
            "key": key,
            **skill.dict(),
            "tool_count": len([t for t in skills_manager.skill_tools.values() if t.get("skill") == skill.name])
        })
    
    return {
        "skills": skills_list,
        "last_scan": skills_manager.last_scan.isoformat() if skills_manager.last_scan else None
    }


@router.get("/mentions")
async def get_skill_mentions_endpoint(user_id: Optional[str] = None):
    """Get skill mentions for system prompt (lightweight)
    
    Returns only skill names and descriptions.
    Agent should use list_directory/read_file to load full instructions.
    """
    skills_manager.scan_all(user_id)
    mentions = skills_manager.get_skill_mentions()
    
    return {
        "mentions": mentions,
        "skill_count": len(skills_manager.skills)
    }


@router.get("/prompts/all")
async def get_all_skill_prompts_endpoint(user_id: Optional[str] = None):
    """Get all system prompts from enabled skills (DEPRECATED)
    
    Use /skills/mentions instead for on-demand loading.
    """
    skills_manager.scan_all(user_id)
    prompts = skills_manager.get_system_prompts()
    
    return {
        "prompts": prompts,
        "count": len(prompts)
    }


@router.post("/scan")
async def scan_skills_endpoint(user_id: Optional[str] = None):
    """Force rescan of all skill directories"""
    skills_manager.scan_all(user_id)
    
    return {
        "success": True,
        "skills_found": len(skills_manager.skills),
        "tools_found": len(skills_manager.skill_tools),
        "last_scan": skills_manager.last_scan.isoformat() if skills_manager.last_scan else None
    }


@router.get("/available")
async def list_available_skills_endpoint():
    """List skills available for installation from Anthropic"""
    skills_manager.scan_all()
    installed = {s.name for s in skills_manager.skills.values()}
    
    available = []
    for name, desc in ANTHROPIC_SKILLS.items():
        available.append({
            "name": name,
            "description": desc,
            "installed": name in installed,
            "source": "anthropic"
        })
    
    return {"available": available, "count": len(available)}


@router.get("/{name}")
async def get_skill(name: str, user_id: Optional[str] = None):
    """Get skill details"""
    skills_manager.scan_all(user_id)
    skill = skills_manager.get_skill(name)
    
    if not skill:
        raise HTTPException(404, f"Skill {name} not found")
    
    # Get tools from this skill
    skill_tools = [t for t in skills_manager.skill_tools.values() if t.get("skill") == skill.name]
    
    return {
        "skill": skill.dict(),
        "tools": skill_tools
    }


@router.get("/{name}/prompt")
async def get_skill_prompt(name: str, user_id: Optional[str] = None):
    """Get system prompt for a specific skill"""
    skills_manager.scan_all(user_id)
    skill = skills_manager.get_skill(name)
    
    if not skill:
        raise HTTPException(404, f"Skill {name} not found")
    
    return {
        "name": skill.name,
        "prompt": skill.system_prompt or ""
    }


class SkillToggle(BaseModel):
    enabled: bool


@router.put("/{name}")
async def toggle_skill(name: str, data: SkillToggle, user_id: Optional[str] = None):
    """Enable or disable a skill"""
    skills_manager.scan_all(user_id)
    skill = skills_manager.get_skill(name)
    
    if not skill:
        raise HTTPException(404, f"Skill {name} not found")
    
    skill.enabled = data.enabled
    skills_manager.save_cache()
    
    return {"success": True, "name": name, "enabled": data.enabled}


class SkillInstall(BaseModel):
    name: str
    source: str = "anthropic"


@router.post("/install")
async def install_skill(data: SkillInstall):
    """Install a skill from Anthropic's repository
    
    Downloads skill files from github.com/anthropics/skills
    """
    name = data.name.lower()
    
    if data.source == "anthropic":
        if name not in ANTHROPIC_SKILLS:
            raise HTTPException(400, f"Unknown skill: {name}. Available: {list(ANTHROPIC_SKILLS.keys())}")
        
        skill_path = os.path.join(SHARED_SKILLS_DIR, name)
        
        # Check if already installed
        if os.path.exists(skill_path):
            return {"success": True, "name": name, "message": f"Skill '{name}' already installed", "path": skill_path}
        
        # Clone from Anthropic's repository
        try:
            # Create temp directory for clone
            temp_dir = f"/tmp/anthropic-skills-{name}"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Sparse checkout just the skill we need
            subprocess.run([
                "git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                "https://github.com/anthropics/skills.git",
                temp_dir
            ], check=True, capture_output=True)
            
            subprocess.run([
                "git", "-C", temp_dir, "sparse-checkout", "set", f"skills/{name}"
            ], check=True, capture_output=True)
            
            # Move to skills directory
            os.makedirs(SHARED_SKILLS_DIR, exist_ok=True)
            src_path = os.path.join(temp_dir, "skills", name)
            
            if os.path.exists(src_path):
                shutil.move(src_path, skill_path)
                
                # Create skill.json if it doesn't exist (use SKILL.md as system_prompt_file)
                skill_json_path = os.path.join(skill_path, "skill.json")
                if not os.path.exists(skill_json_path):
                    skill_md_path = os.path.join(skill_path, "SKILL.md")
                    desc = ANTHROPIC_SKILLS.get(name, "")
                    
                    skill_json = {
                        "name": name,
                        "description": desc,
                        "version": "1.0.0",
                        "author": "Anthropic",
                        "system_prompt_file": "SKILL.md" if os.path.exists(skill_md_path) else None,
                        "tools": [],
                        "enabled": True
                    }
                    
                    with open(skill_json_path, 'w') as f:
                        import json
                        json.dump(skill_json, f, indent=2)
                
                # Cleanup
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                # Rescan skills
                skills_manager.scan_all()
                
                return {"success": True, "name": name, "message": f"Installed skill '{name}'", "path": skill_path}
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise HTTPException(500, f"Skill '{name}' not found in Anthropic's repository")
                
        except subprocess.CalledProcessError as e:
            raise HTTPException(500, f"Installation failed: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            raise HTTPException(500, f"Installation failed: {str(e)}")
    
    else:
        raise HTTPException(400, f"Unknown source: {data.source}")


@router.delete("/{name}")
async def uninstall_skill(name: str):
    """Uninstall a skill"""
    skill_path = os.path.join(SHARED_SKILLS_DIR, name)
    
    if not os.path.exists(skill_path):
        raise HTTPException(404, f"Skill {name} not found")
    
    shutil.rmtree(skill_path)
    skills_manager.scan_all()
    
    return {"success": True, "name": name, "message": f"Uninstalled skill '{name}'"}
