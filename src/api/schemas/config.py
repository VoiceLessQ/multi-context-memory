"""
Pydantic schemas for configuration operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ConfigBase(BaseModel):
    """Base schema for configuration operations."""
    key: str = Field(..., min_length=1, max_length=255)
    value: Any
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field("general", min_length=1, max_length=50)
    is_sensitive: bool = Field(False)
    is_system: bool = Field(False)
    version: int = Field(1)

    @validator('key')
    def validate_key(cls, v):
        """Validate configuration key."""
        if not v or not isinstance(v, str):
            raise ValueError("Configuration key must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Configuration key cannot be empty")
        return v

    @validator('category')
    def validate_category(cls, v):
        """Validate configuration category."""
        if not v or not isinstance(v, str):
            raise ValueError("Configuration category must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Configuration category cannot be empty")
        return v

class ConfigCreate(ConfigBase):
    """Schema for creating a new configuration."""
    pass

class ConfigUpdate(BaseModel):
    """Schema for updating a configuration."""
    value: Any
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    is_sensitive: Optional[bool] = Field(None)
    is_system: Optional[bool] = Field(None)

    @validator('category')
    def validate_category(cls, v):
        """Validate configuration category."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Configuration category must be a string")
            v = v.strip()
            if not v:
                raise ValueError("Configuration category cannot be empty")
        return v

class ConfigResponse(ConfigBase):
    """Schema for configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class ConfigStats(BaseModel):
    """Schema for configuration statistics."""
    total_configs: int
    configs_by_category: Dict[str, int]
    sensitive_configs: int
    system_configs: int
    last_updated: Optional[datetime]
    most_updated_category: Optional[str]
    average_version: float

class ConfigImport(BaseModel):
    """Schema for configuration import."""
    configs: List[Dict[str, Any]]
    merge_strategy: str = Field("overwrite", regex="^(overwrite|skip|merge)$")
    validate_only: bool = Field(False)
    dry_run: bool = Field(False)

class ConfigExport(BaseModel):
    """Schema for configuration export."""
    format: str = Field("json", regex="^(json|yaml|csv|xml)$")
    category: Optional[str] = Field(None)
    include_sensitive: bool = Field(False)
    include_system: bool = Field(False)
    include_metadata: bool = Field(True)

class ConfigExportResponse(BaseModel):
    """Schema for configuration export response."""
    total_items: int
    format: str
    exported_at: datetime
    file_path: Optional[str] = None
    checksum: Optional[str] = None

class ConfigImportResponse(BaseModel):
    """Schema for configuration import response."""
    total_items: int
    imported_items: int
    skipped_items: int
    updated_items: int
    errors: List[str] = Field(default_factory=list)
    imported_at: datetime

class ConfigSearch(BaseModel):
    """Schema for configuration search."""
    query: str = Field(..., min_length=1)
    category: Optional[str] = Field(None)
    is_sensitive: Optional[bool] = Field(None)
    is_system: Optional[bool] = Field(None)
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class ConfigHistory(BaseModel):
    """Schema for configuration history."""
    config_id: int
    key: str
    version: int
    value: Any
    description: Optional[str] = None
    category: str
    is_sensitive: bool
    is_system: bool
    created_at: datetime
    updated_by: Optional[int] = None
    change_reason: Optional[str] = None

class ConfigHistoryResponse(BaseModel):
    """Schema for configuration history response."""
    history: List[ConfigHistory]
    total_items: int
    config_key: str

class ConfigDiff(BaseModel):
    """Schema for configuration diff."""
    old_version: Optional[ConfigHistory] = None
    new_version: ConfigHistory
    differences: Dict[str, Any] = Field(default_factory=dict)
    diff_type: str = Field("created", regex="^(created|updated|deleted)$")

class ConfigDiffResponse(BaseModel):
    """Schema for configuration diff response."""
    config_id: int
    key: str
    diffs: List[ConfigDiff]
    total_diffs: int

class ConfigTemplate(BaseModel):
    """Schema for configuration template."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field("template", min_length=1, max_length=50)
    configs: List[ConfigCreate] = Field(..., min_items=1)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = Field(False)
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('name')
    def validate_name(cls, v):
        """Validate template name."""
        if not v or not isinstance(v, str):
            raise ValueError("Template name must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Template name cannot be empty")
        return v

    @validator('category')
    def validate_category(cls, v):
        """Validate template category."""
        if not v or not isinstance(v, str):
            raise ValueError("Template category must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Template category cannot be empty")
        return v

class ConfigTemplateResponse(ConfigTemplate):
    """Schema for configuration template response."""
    id: int
    usage_count: int = 0

    class Config:
        from_attributes = True

class ConfigTemplateStats(BaseModel):
    """Schema for configuration template statistics."""
    total_templates: int
    public_templates: int
    private_templates: int
    templates_by_category: Dict[str, int]
    most_used_template: Optional[str]
    total_usages: int
    average_configs_per_template: float

class ConfigApplyTemplate(BaseModel):
    """Schema for applying configuration template."""
    template_id: int
    merge_strategy: str = Field("overwrite", regex="^(overwrite|skip|merge)$")
    validate_only: bool = Field(False)
    dry_run: bool = Field(False)
    target_category: Optional[str] = Field(None)
    prefix: Optional[str] = Field(None)

class ConfigApplyTemplateResponse(BaseModel):
    """Schema for applying configuration template response."""
    template_id: int
    template_name: str
    total_items: int
    applied_items: int
    skipped_items: int
    updated_items: int
    errors: List[str] = Field(default_factory=list)
    applied_at: datetime

class ConfigValidate(BaseModel):
    """Schema for configuration validation."""
    configs: List[Dict[str, Any]]
    strict: bool = Field(True)
    check_dependencies: bool = Field(True)
    check_conflicts: bool = Field(True)

class ConfigValidateResponse(BaseModel):
    """Schema for configuration validation response."""
    total_items: int
    valid_items: int
    invalid_items: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_at: datetime

class ConfigBackup(BaseModel):
    """Schema for configuration backup."""
    include_sensitive: bool = Field(False)
    include_system: bool = Field(False)
    include_metadata: bool = Field(True)
    compression: bool = Field(True)
    format: str = Field("json", regex="^(json|yaml|csv|xml)$")

class ConfigBackupResponse(BaseModel):
    """Schema for configuration backup response."""
    backup_id: str
    backup_path: str
    backup_size_mb: float
    format: str
    created_at: datetime
    includes_sensitive: bool
    includes_system: bool
    includes_metadata: bool
    compressed: bool
    expires_at: datetime

class ConfigRestore(BaseModel):
    """Schema for configuration restore."""
    backup_path: str = Field(..., min_length=1)
    merge_strategy: str = Field("overwrite", regex="^(overwrite|skip|merge)$")
    validate_only: bool = Field(False)
    dry_run: bool = Field(False)
    restore_metadata: bool = Field(True)
    restore_sensitive: bool = Field(True)
    restore_system: bool = Field(True)

class ConfigRestoreResponse(BaseModel):
    """Schema for configuration restore response."""
    restore_id: str
    backup_path: str
    status: str = Field(..., regex="^(pending|in_progress|completed|failed)$")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    restored_items: Optional[Dict[str, int]] = None
    errors: Optional[List[str]] = None

class ConfigHealth(BaseModel):
    """Schema for configuration health check."""
    status: str = Field(..., regex="^(healthy|degraded|unhealthy)$")
    total_configs: int
    sensitive_configs: int
    system_configs: int
    last_updated: Optional[datetime]
    outdated_configs: int
    orphaned_configs: int
    validation_errors: int
    warnings: int

class ConfigAuditLog(BaseModel):
    """Schema for configuration audit log."""
    id: int
    config_id: int
    action: str = Field(..., regex="^(created|updated|deleted|restored|exported|imported)$")
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changed_by: int
    changed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    change_reason: Optional[str] = None

class ConfigAuditLogResponse(BaseModel):
    """Schema for configuration audit log response."""
    logs: List[ConfigAuditLog]
    total_items: int
    config_key: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ConfigAuditLogFilter(BaseModel):
    """Schema for configuration audit log filtering."""
    config_id: Optional[int] = Field(None)
    action: Optional[str] = Field(None, regex="^(created|updated|deleted|restored|exported|imported)$")
    changed_by: Optional[int] = Field(None)
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)