#!/usr/bin/env python3
"""
Enhanced token management with multi-phase review support.

This module extends the basic token management to support intelligent
multi-phase reviews with smart content extraction and change manifests.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from .token_manager import (
    FileInfo, estimate_tokens, get_token_limit, calculate_file_priority,
    CONTEXT_STRATEGIES
)

logger = logging.getLogger(__name__)


class ContentInclusionMode(Enum):
    """How to include file content in the review."""
    FULL = "full"  # Include complete file content
    DIFF_ONLY = "diff_only"  # Include only the diff/changes
    SMART_DIFF = "smart_diff"  # Include diff with context lines
    STRUCTURE_ONLY = "structure_only"  # Include file structure (classes, functions)
    SUMMARY_ONLY = "summary_only"  # Include only path and change stats


class FileCategory(Enum):
    """Categories for prioritizing files."""
    CORE_SOURCE = "core_source"  # Main application code
    API_CONTRACTS = "api_contracts"  # API definitions, interfaces
    CONFIGURATION = "configuration"  # Config files
    TESTS = "tests"  # Test files
    UTILITIES = "utilities"  # Helper/utility files
    DOCUMENTATION = "documentation"  # Docs, README files
    BUILD_SCRIPTS = "build_scripts"  # Build/deployment scripts
    ASSETS = "assets"  # Images, data files, etc.
    OTHER = "other"  # Everything else


@dataclass
class FileManifestEntry:
    """Entry in the change manifest."""
    path: str
    status: str  # added, modified, deleted
    category: FileCategory
    additions: int
    deletions: int
    size_bytes: int
    priority_score: int
    inclusion_mode: ContentInclusionMode = ContentInclusionMode.FULL
    phase_number: Optional[int] = None
    tokens_if_full: Optional[int] = None


@dataclass
class ChangeManifest:
    """Complete manifest of all changes in the review."""
    total_files: int
    files_added: int
    files_modified: int
    files_deleted: int
    total_additions: int
    total_deletions: int
    entries: List[FileManifestEntry]
    
    def to_markdown(self) -> str:
        """Convert manifest to markdown format."""
        lines = [
            "## 📊 Complete Change Summary",
            f"**Total files changed**: {self.total_files}",
            f"- ➕ Added: {self.files_added} files",
            f"- 📝 Modified: {self.files_modified} files",
            f"- ❌ Deleted: {self.files_deleted} files",
            f"- Lines: +{self.total_additions} -{self.total_deletions}",
            "",
            "### By Category:"
        ]
        
        # Group by category
        by_category = {}
        for entry in self.entries:
            if entry.category not in by_category:
                by_category[entry.category] = []
            by_category[entry.category].append(entry)
        
        # Sort categories by importance
        category_order = [
            FileCategory.CORE_SOURCE,
            FileCategory.API_CONTRACTS,
            FileCategory.CONFIGURATION,
            FileCategory.TESTS,
            FileCategory.UTILITIES,
            FileCategory.DOCUMENTATION,
            FileCategory.BUILD_SCRIPTS,
            FileCategory.ASSETS,
            FileCategory.OTHER
        ]
        
        for category in category_order:
            if category in by_category:
                entries = by_category[category]
                category_name = category.value.replace('_', ' ').title()
                lines.append(f"- **{category_name}**: {len(entries)} files")
        
        return '\n'.join(lines)


@dataclass
class ReviewPhase:
    """Represents a single phase of a multi-phase review."""
    phase_number: int
    total_phases: int
    name: str
    description: str
    included_files: List[FileInfo]
    manifest_entries: List[FileManifestEntry]
    token_count: int
    token_limit: int
    
    def to_metadata_markdown(self) -> str:
        """Generate phase metadata in markdown."""
        lines = [
            f"## 📋 Review Phase Information",
            f"**Phase {self.phase_number} of {self.total_phases}**: {self.name}",
            f"_{self.description}_",
            "",
            f"**Files in this phase**: {len(self.included_files)}/{len(self.manifest_entries)}",
            f"**Token usage**: {self.token_count:,}/{self.token_limit:,} ({self.token_count/self.token_limit*100:.1f}%)",
            "",
            "### Files included in this phase:"
        ]
        
        # Group by inclusion mode
        by_mode = {}
        for entry in self.manifest_entries:
            if entry.phase_number == self.phase_number:
                mode = entry.inclusion_mode
                if mode not in by_mode:
                    by_mode[mode] = []
                by_mode[mode].append(entry)
        
        mode_icons = {
            ContentInclusionMode.FULL: "✅",
            ContentInclusionMode.SMART_DIFF: "📝",
            ContentInclusionMode.DIFF_ONLY: "➖",
            ContentInclusionMode.STRUCTURE_ONLY: "🏗️",
            ContentInclusionMode.SUMMARY_ONLY: "📄"
        }
        
        for mode, entries in by_mode.items():
            icon = mode_icons.get(mode, "📄")
            mode_name = mode.value.replace('_', ' ').title()
            lines.append(f"- {icon} **{mode_name}**: {len(entries)} files")
        
        # Show deferred files if not last phase
        if self.phase_number < self.total_phases:
            deferred_count = len([e for e in self.manifest_entries if e.phase_number is None or e.phase_number > self.phase_number])
            if deferred_count > 0:
                lines.append(f"- ⏭️ **Deferred to later phases**: {deferred_count} files")
        
        return '\n'.join(lines)


@dataclass
class MultiPhaseContext:
    """Result of multi-phase context building."""
    manifest: ChangeManifest
    phases: List[ReviewPhase]
    model_name: str
    strategy: str
    total_tokens_all_phases: int


def categorize_file(file_path: str) -> FileCategory:
    """Categorize a file based on its path and extension."""
    path_lower = file_path.lower()
    _, ext = os.path.splitext(path_lower)
    ext = ext.lstrip('.')
    
    # Check path patterns first
    if '/test' in path_lower or '/spec' in path_lower or path_lower.endswith('_test.py'):
        return FileCategory.TESTS
    elif '/api/' in path_lower or '/routes/' in path_lower or 'schema' in path_lower:
        return FileCategory.API_CONTRACTS
    elif '/docs/' in path_lower or 'readme' in path_lower:
        return FileCategory.DOCUMENTATION
    elif '/utils/' in path_lower or '/helpers/' in path_lower or '/lib/' in path_lower:
        return FileCategory.UTILITIES
    elif any(x in path_lower for x in ['/build/', '/scripts/', 'makefile', 'dockerfile']):
        return FileCategory.BUILD_SCRIPTS
    elif '/src/' in path_lower or '/app/' in path_lower or '/core/' in path_lower:
        return FileCategory.CORE_SOURCE
    
    # Check by extension
    if ext in ['json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'env']:
        return FileCategory.CONFIGURATION
    elif ext in ['py', 'js', 'ts', 'jsx', 'tsx', 'go', 'rs', 'java', 'cpp', 'c']:
        # Could be core source if not categorized above
        if any(x in path_lower for x in ['/bin/', '/cmd/', 'main.', 'app.', 'server.']):
            return FileCategory.CORE_SOURCE
        return FileCategory.UTILITIES
    elif ext in ['md', 'txt', 'rst', 'adoc']:
        return FileCategory.DOCUMENTATION
    elif ext in ['jpg', 'png', 'gif', 'svg', 'ico', 'mp4', 'pdf']:
        return FileCategory.ASSETS
    
    return FileCategory.OTHER


def extract_file_structure(content: str, file_path: str) -> str:
    """Extract file structure (imports, classes, functions) from content."""
    lines = content.split('\n')
    structure_lines = []
    
    _, ext = os.path.splitext(file_path.lower())
    ext = ext.lstrip('.')
    
    if ext in ['py']:
        # Python structure extraction
        import_pattern = re.compile(r'^(from .* import .*|import .*)$')
        class_pattern = re.compile(r'^class\s+(\w+).*:')
        func_pattern = re.compile(r'^def\s+(\w+)\s*\(.*\):')
        
        for i, line in enumerate(lines):
            if import_pattern.match(line.strip()):
                structure_lines.append(line)
            elif class_match := class_pattern.match(line):
                structure_lines.append(line)
                # Include class docstring if present
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    structure_lines.append(lines[i + 1])
            elif func_match := func_pattern.match(line):
                # Only include top-level functions (no indentation)
                if not line.startswith(' ') and not line.startswith('\t'):
                    structure_lines.append(line)
    
    elif ext in ['js', 'ts', 'jsx', 'tsx']:
        # JavaScript/TypeScript structure
        import_pattern = re.compile(r'^(import|export).*$')
        class_pattern = re.compile(r'^(export\s+)?(class|interface|type)\s+(\w+)')
        func_pattern = re.compile(r'^(export\s+)?(function|const)\s+(\w+)\s*[=\(]')
        
        for line in lines:
            stripped = line.strip()
            if import_pattern.match(stripped):
                structure_lines.append(line)
            elif class_pattern.match(stripped):
                structure_lines.append(line)
            elif func_pattern.match(stripped) and not line.startswith(' '):
                structure_lines.append(line)
    
    if structure_lines:
        return '\n'.join(['[File Structure]', ''] + structure_lines[:50])  # Limit to 50 lines
    else:
        return '[File structure extraction not available for this file type]'


def extract_smart_diff(content: str, context_lines: int = 5) -> str:
    """Extract a smart diff focusing on changes with context."""
    # For actual implementation, this would parse git diff output
    # For now, return a placeholder that would be replaced with actual diff logic
    lines = content.split('\n')
    
    if len(lines) > 100:
        # Simulate extracting key parts
        preview_lines = lines[:30] + ['...', f'[{len(lines) - 60} lines omitted]', '...'] + lines[-30:]
        return '\n'.join(preview_lines)
    
    return content


def build_change_manifest(files: List[FileInfo]) -> ChangeManifest:
    """Build a complete manifest of all file changes."""
    entries = []
    total_additions = 0
    total_deletions = 0
    files_added = 0
    files_modified = 0  
    files_deleted = 0
    
    for file_info in files:
        category = categorize_file(file_info.path)
        priority = calculate_file_priority(file_info)
        
        # Estimate tokens for full content
        tokens_if_full = estimate_tokens(file_info.content, file_info.path)
        
        entry = FileManifestEntry(
            path=file_info.path,
            status=file_info.status,
            category=category,
            additions=file_info.additions,
            deletions=file_info.deletions,
            size_bytes=len(file_info.content.encode('utf-8')),
            priority_score=priority,
            tokens_if_full=tokens_if_full
        )
        entries.append(entry)
        
        # Update counters
        total_additions += file_info.additions
        total_deletions += file_info.deletions
        
        if file_info.status == "added":
            files_added += 1
        elif file_info.status == "modified":
            files_modified += 1
        elif file_info.status == "deleted":
            files_deleted += 1
    
    return ChangeManifest(
        total_files=len(files),
        files_added=files_added,
        files_modified=files_modified,
        files_deleted=files_deleted,
        total_additions=total_additions,
        total_deletions=total_deletions,
        entries=entries
    )


def determine_inclusion_mode(
    entry: FileManifestEntry, 
    remaining_tokens: int,
    phase_focus: FileCategory
) -> ContentInclusionMode:
    """Determine how to include a file based on available tokens and priority."""
    
    # Deleted files should always show full content if they're important
    if entry.status == "deleted" and entry.category in [FileCategory.CORE_SOURCE, FileCategory.API_CONTRACTS]:
        return ContentInclusionMode.FULL
    
    # If we have plenty of tokens and it's high priority, include full
    if remaining_tokens > entry.tokens_if_full * 2 and entry.priority_score > 150:
        return ContentInclusionMode.FULL
    
    # Phase-specific rules
    if entry.category == phase_focus:
        if remaining_tokens > entry.tokens_if_full:
            return ContentInclusionMode.FULL
        elif remaining_tokens > entry.tokens_if_full * 0.5:
            return ContentInclusionMode.SMART_DIFF
        else:
            return ContentInclusionMode.STRUCTURE_ONLY
    
    # General rules based on category
    if entry.category == FileCategory.TESTS:
        return ContentInclusionMode.SMART_DIFF if remaining_tokens > 1000 else ContentInclusionMode.SUMMARY_ONLY
    elif entry.category == FileCategory.DOCUMENTATION:
        return ContentInclusionMode.SMART_DIFF if remaining_tokens > 500 else ContentInclusionMode.SUMMARY_ONLY
    elif entry.category in [FileCategory.CONFIGURATION, FileCategory.BUILD_SCRIPTS]:
        return ContentInclusionMode.SMART_DIFF
    elif entry.category == FileCategory.ASSETS:
        return ContentInclusionMode.SUMMARY_ONLY
    
    # Default based on available tokens
    if remaining_tokens > entry.tokens_if_full * 0.3:
        return ContentInclusionMode.SMART_DIFF
    else:
        return ContentInclusionMode.STRUCTURE_ONLY


def apply_inclusion_mode(file_info: FileInfo, mode: ContentInclusionMode) -> FileInfo:
    """Apply the inclusion mode to generate appropriate content."""
    if mode == ContentInclusionMode.FULL:
        return file_info  # Return as-is
    
    elif mode == ContentInclusionMode.SMART_DIFF:
        smart_diff = extract_smart_diff(file_info.content)
        return FileInfo(
            path=file_info.path,
            content=f"[Smart Diff View]\n{smart_diff}",
            status=file_info.status,
            additions=file_info.additions,
            deletions=file_info.deletions
        )
    
    elif mode == ContentInclusionMode.DIFF_ONLY:
        # This would use actual git diff
        return FileInfo(
            path=file_info.path,
            content=f"[Diff Only - +{file_info.additions} -{file_info.deletions} lines]",
            status=file_info.status,
            additions=file_info.additions,
            deletions=file_info.deletions
        )
    
    elif mode == ContentInclusionMode.STRUCTURE_ONLY:
        structure = extract_file_structure(file_info.content, file_info.path)
        return FileInfo(
            path=file_info.path,
            content=structure,
            status=file_info.status,
            additions=file_info.additions,
            deletions=file_info.deletions
        )
    
    else:  # SUMMARY_ONLY
        return FileInfo(
            path=file_info.path,
            content=f"[File Summary: {file_info.status} - +{file_info.additions} -{file_info.deletions} lines]",
            status=file_info.status,
            additions=file_info.additions,
            deletions=file_info.deletions
        )


class MultiPhaseContextBuilder:
    """Enhanced context builder with multi-phase support."""
    
    def __init__(
        self,
        model_name: str,
        strategy: str = "balanced",
        max_tokens_override: Optional[int] = None,
        per_file_limit: int = 10_000,
        enable_multi_phase: bool = True,
        phase_overlap_ratio: float = 0.1  # 10% token budget for manifest/metadata
    ):
        """Initialize multi-phase context builder."""
        self.model_name = model_name
        self.strategy = strategy
        self.token_limit = get_token_limit(model_name, strategy, max_tokens_override)
        self.per_file_limit = per_file_limit
        self.enable_multi_phase = enable_multi_phase
        self.phase_overlap_ratio = phase_overlap_ratio
    
    def build_context(self, files: List[FileInfo]) -> Union[MultiPhaseContext, List[FileInfo]]:
        """
        Build context with automatic multi-phase detection.
        
        Returns MultiPhaseContext if multi-phase is needed and enabled,
        otherwise returns list of FileInfo for backward compatibility.
        """
        # Build manifest first
        manifest = build_change_manifest(files)
        
        # Calculate total tokens needed for all files
        total_tokens_needed = sum(e.tokens_if_full for e in manifest.entries)
        
        # Reserve tokens for manifest and metadata
        manifest_tokens = estimate_tokens(manifest.to_markdown())
        metadata_overhead = int(self.token_limit * self.phase_overlap_ratio)
        effective_limit = self.token_limit - manifest_tokens - metadata_overhead
        
        # Check if multi-phase is needed
        if not self.enable_multi_phase or total_tokens_needed <= effective_limit:
            # Single phase is sufficient
            logger.info(f"Single phase sufficient: {total_tokens_needed:,} tokens needed, {effective_limit:,} available")
            # Return simple list for backward compatibility
            return files
        
        # Multi-phase is needed
        logger.info(f"Multi-phase required: {total_tokens_needed:,} tokens needed, {effective_limit:,} per phase")
        
        # Plan phases
        phases = self._plan_phases(manifest, effective_limit, files)
        
        return MultiPhaseContext(
            manifest=manifest,
            phases=phases,
            model_name=self.model_name,
            strategy=self.strategy,
            total_tokens_all_phases=sum(p.token_count for p in phases)
        )
    
    def _plan_phases(self, manifest: ChangeManifest, tokens_per_phase: int, files: List[FileInfo]) -> List[ReviewPhase]:
        """Plan the review phases based on file categories and priorities."""
        phases = []
        
        # Define phase structure
        phase_definitions = [
            ("Critical Changes", "Core source code, APIs, and critical configurations", [
                FileCategory.CORE_SOURCE,
                FileCategory.API_CONTRACTS,
                FileCategory.CONFIGURATION
            ]),
            ("Supporting Changes", "Tests, utilities, and build scripts", [
                FileCategory.TESTS,
                FileCategory.UTILITIES,
                FileCategory.BUILD_SCRIPTS
            ]),
            ("Documentation & Assets", "Documentation updates and other files", [
                FileCategory.DOCUMENTATION,
                FileCategory.ASSETS,
                FileCategory.OTHER
            ])
        ]
        
        # Track which files have been assigned
        assigned_files = set()
        file_map = {entry.path: entry for entry in manifest.entries}
        
        for phase_num, (phase_name, phase_desc, categories) in enumerate(phase_definitions, 1):
            phase_entries = []
            phase_files = []
            current_tokens = 0
            
            # Sort entries by priority within target categories
            target_entries = [
                e for e in manifest.entries 
                if e.category in categories and e.path not in assigned_files
            ]
            target_entries.sort(key=lambda e: e.priority_score, reverse=True)
            
            for entry in target_entries:
                # Find corresponding FileInfo
                file_info = next((f for f in files if f.path == entry.path), None)
                if not file_info:
                    continue
                
                # Determine inclusion mode based on remaining tokens
                remaining = tokens_per_phase - current_tokens
                mode = determine_inclusion_mode(entry, remaining, categories[0])
                
                # Apply inclusion mode
                processed_file = apply_inclusion_mode(file_info, mode)
                actual_tokens = estimate_tokens(processed_file.content, processed_file.path)
                
                if current_tokens + actual_tokens <= tokens_per_phase:
                    entry.inclusion_mode = mode
                    entry.phase_number = phase_num
                    phase_entries.append(entry)
                    phase_files.append(processed_file)
                    current_tokens += actual_tokens
                    assigned_files.add(entry.path)
            
            # Add any remaining high-priority files that fit
            remaining_entries = [
                e for e in manifest.entries 
                if e.path not in assigned_files
            ]
            remaining_entries.sort(key=lambda e: e.priority_score, reverse=True)
            
            for entry in remaining_entries:
                file_info = next((f for f in files if f.path == entry.path), None)
                if not file_info:
                    continue
                
                remaining = tokens_per_phase - current_tokens
                if remaining < 1000:  # Stop if we're too close to limit
                    break
                
                mode = determine_inclusion_mode(entry, remaining, FileCategory.OTHER)
                processed_file = apply_inclusion_mode(file_info, mode)
                actual_tokens = estimate_tokens(processed_file.content, processed_file.path)
                
                if current_tokens + actual_tokens <= tokens_per_phase:
                    entry.inclusion_mode = mode
                    entry.phase_number = phase_num
                    phase_entries.append(entry)
                    phase_files.append(processed_file)
                    current_tokens += actual_tokens
                    assigned_files.add(entry.path)
            
            if phase_files:  # Only create phase if it has content
                phase = ReviewPhase(
                    phase_number=phase_num,
                    total_phases=len(phase_definitions),
                    name=phase_name,
                    description=phase_desc,
                    included_files=phase_files,
                    manifest_entries=manifest.entries,  # All entries for reference
                    token_count=current_tokens,
                    token_limit=tokens_per_phase
                )
                phases.append(phase)
        
        # Handle any unassigned files
        unassigned = [e for e in manifest.entries if e.path not in assigned_files]
        if unassigned and phases:
            # Try to fit them into existing phases
            for entry in unassigned:
                for phase in phases:
                    if phase.token_count < phase.token_limit * 0.9:  # 90% full
                        entry.phase_number = phase.phase_number
                        entry.inclusion_mode = ContentInclusionMode.SUMMARY_ONLY
                        break
        
        return phases


def generate_multi_phase_summary(context: MultiPhaseContext) -> str:
    """Generate a summary message for multi-phase context generation."""
    lines = [
        "📊 Multi-Phase Review Generated",
        "━" * 50,
        f"Model: {context.model_name}",
        f"Strategy: {context.strategy}",
        f"Total files: {context.manifest.total_files}",
        f"Review phases: {len(context.phases)}",
        f"Total tokens (all phases): {context.total_tokens_all_phases:,}",
        ""
    ]
    
    for phase in context.phases:
        usage_pct = phase.token_count / phase.token_limit * 100
        lines.append(f"**Phase {phase.phase_number}**: {phase.name}")
        lines.append(f"  Files: {len(phase.included_files)} | Tokens: {phase.token_count:,} ({usage_pct:.1f}% of limit)")
    
    lines.extend([
        "",
        "💡 Each phase includes the complete change manifest for context.",
        "Run the review command for each generated phase file."
    ])
    
    return '\n'.join(lines)