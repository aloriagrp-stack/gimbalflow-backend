from fastapi import APIRouter, HTTPException
from app.ml.ml_pipeline import ml_engine
from app.ml.schemas import (
    GenerationRequest,
    GenerationResponse,
    PromptEnhanceRequest,
    PromptEnhanceResponse,
    CameraTrajectoryRequest,
    CameraTrajectoryResponse
)

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

@router.get("/models")
def list_models():
    return {"models": ml_engine.MODELS}

@router.post("/enhance-prompt", response_model=PromptEnhanceResponse)
def enhance_prompt_ml(req: PromptEnhanceRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    return ml_engine.enhance_prompt(req.prompt)

@router.post("/camera-trajectory", response_model=CameraTrajectoryResponse)
def compute_camera_trajectory(req: CameraTrajectoryRequest):
    return ml_engine.generate_camera_trajectory(
        camera_type=req.camera_type,
        fov=req.fov or 85,
        roll=req.roll or 0.0,
        pitch=req.pitch or 0.0,
        speed=req.speed or 1.0
    )

@router.post("/generate", response_model=GenerationResponse)
def execute_generation(req: GenerationRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required for generation")
    return ml_engine.execute_generation_pipeline(req.dict())
