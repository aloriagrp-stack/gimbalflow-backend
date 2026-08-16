from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GenerationRequest(BaseModel):
    user_id: Optional[str] = "usr-demo-01"
    type: str = Field(..., description="image, video, or cinema")
    prompt: str = Field(..., description="Prompt text")
    model: Optional[str] = "Seedance v2"
    aspect_ratio: Optional[str] = "16:9"
    camera: Optional[str] = "FPV Drone Swoop 360°"
    resolution: Optional[str] = "8K Ultra"
    num_images: Optional[int] = 1
    guidance: Optional[float] = 7.5
    steps: Optional[int] = 30
    reference_img: Optional[str] = None

class GenerationResponse(BaseModel):
    job_id: str
    status: str
    type: str
    media_url: str
    prompt: str
    model: str
    aspect_ratio: str
    camera: str
    cost: int
    execution_time_ms: float

class PromptEnhanceRequest(BaseModel):
    prompt: str

class PromptEnhanceResponse(BaseModel):
    original_prompt: str
    enhanced_prompt: str
    applied_tags: List[str]

class CameraTrajectoryRequest(BaseModel):
    camera_type: str = "FPV Drone Swoop 360°"
    fov: Optional[int] = 85
    roll: Optional[float] = 0.0
    pitch: Optional[float] = 0.0
    speed: Optional[float] = 1.0

class CameraTrajectoryResponse(BaseModel):
    camera_type: str
    matrix_3d: List[List[float]]
    keyframe_paths: List[Dict[str, float]]
