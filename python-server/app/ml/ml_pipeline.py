import time
import math
import random
from typing import Dict, Any, List

class GimbalFlowMLEngine:
    """
    Python ML Engine for GimbalFlow
    Handles machine learning model integrations, prompt engineering, 
    cinematic trajectory rendering, and generation jobs.
    """
    
    MODELS = {
        "Seedance v2": {
            "type": "video/cinema",
            "fps": 60,
            "max_res": "4K",
            "description": "High frame-rate 60FPS fluid video generation model with cinematic lighting."
        },
        "Higgsfield Cinema Pro": {
            "type": "image/cinema",
            "fps": 24,
            "max_res": "8K",
            "description": "State-of-the-art photorealistic keyframe and texture generation model."
        },
        "ActionDiff v3": {
            "type": "video",
            "fps": 60,
            "max_res": "4K",
            "description": "Action motion diffusion model tailored for high-speed dynamic camera movements."
        }
    }

    STOCK_MEDIA = [
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1000&auto=format&fit=crop"
    ]

    def _clean_noise_prefixes(self, prompt: str) -> str:
        """Strips command noise like 'make a', 'generate an', 'create a photo of'"""
        import re
        p = prompt.strip()
        noise_patterns = [
            r'^(please\s+)?(can\s+you\s+)?(make|create|generate|draw|render|produce|show|give\s+me)\s+(an?|the|some)?\s+',
            r'^(a\s+)?(picture|photo|photograph|image|illustration|painting|render)\s+(of\s+(an?|the)?)?\s*',
            r'^(wallpaper\s+of\s+(an?|the)?)?\s*',
            r'^(ultra\s+)?(realistic\s+)?(hd\s+)?(4k\s+)?(8k\s+)?'
        ]
        for pat in noise_patterns:
            p = re.sub(pat, '', p, flags=re.IGNORECASE).strip()
        return p if p else prompt.strip()

    def _classify_category(self, prompt: str) -> str:
        """Classifies prompt into visual cinematography domain"""
        p = prompt.lower()
        food_kw = ["apple", "fruit", "burger", "pizza", "coffee", "cake", "bread", "steak", "dish", "food", "cocktail", "pasta", "dessert", "drink", "chocolate", "berry", "orange", "lemon", "sushi", "soup", "salad", "sandwich", "mango", "banana", "strawberry"]
        wildlife_kw = ["dog", "cat", "puppy", "kitten", "lion", "tiger", "bird", "eagle", "wolf", "fox", "bear", "horse", "animal", "pet", "wildlife", "leopard", "elephant", "deer", "owl", "rabbit"]
        char_kw = ["girl", "woman", "man", "boy", "person", "human", "face", "portrait", "model", "warrior", "samurai", "astronaut", "cybernetic", "cyborg", "queen", "king", "knight", "soldier", "detective", "eyes", "smile", "lady", "guy", "child", "character", "monk", "dancer"]
        land_kw = ["mountain", "forest", "river", "ocean", "sea", "beach", "lake", "valley", "waterfall", "desert", "nature", "tree", "trees", "cliff", "clouds", "sky", "sunset", "sunrise", "snow", "aurora", "jungle", "meadow", "island", "landscape", "canyon"]
        urban_kw = ["city", "street", "cyberpunk", "futuristic", "building", "room", "interior", "skyscraper", "neon", "alley", "architecture", "spaceship", "sci-fi", "scifi", "downtown", "metropolis", "cyber", "station", "bridge", "penthouse"]
        veh_kw = ["car", "sports car", "supercar", "motorcycle", "bike", "vehicle", "jet", "airplane", "plane", "boat", "ship", "yacht", "race car", "porsche", "ferrari", "lamborghini", "bmw"]
        fantasy_kw = ["dragon", "wizard", "magic", "crystal", "fairy", "alien", "portal", "celestial", "galaxy", "nebula", "ethereal", "mystical", "spells", "cosmic"]

        for kw in food_kw:
            if kw in p:
                return "FOOD_ORGANIC"
        for kw in wildlife_kw:
            if kw in p:
                return "ANIMAL_WILDLIFE"
        for kw in veh_kw:
            if kw in p:
                return "VEHICLE_ACTION"
        for kw in char_kw:
            if kw in p:
                return "CHARACTER_PORTRAIT"
        for kw in urban_kw:
            if kw in p:
                return "URBAN_SCIFI_ARCHITECTURE"
        for kw in land_kw:
            if kw in p:
                return "LANDSCAPE_NATURE"
        for kw in fantasy_kw:
            if kw in p:
                return "FANTASY_MYTHICAL"
        return "GENERAL"

    def enhance_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Director-Grade Autonomous AI Prompt Engineering Engine.
        Transforms simple raw user prompts into Hollywood-director grade, 
        optics-specific, lighting-balanced, photorealistic masterpieces.
        """
        raw_prompt = prompt.strip()
        clean_subject = self._clean_noise_prefixes(raw_prompt)
        category = self._classify_category(clean_subject)

        # Enhance short raw single words (e.g. 'apple' -> 'crisp ripe red Honeycrisp apple')
        subject_display = clean_subject
        if clean_subject.lower() == "apple":
            subject_display = "fresh crisp ripe red Honeycrisp apple"

        # 1. Attempt genuine Google Gemini Flash prompt engineering (if key configured)
        from app.config.settings import settings
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10:
            try:
                import urllib.request
                import json
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                system_instruction = (
                    "You are an elite Hollywood cinematographer and Octane 3D prompt engineer. "
                    "Expand this user's simple prompt into a single ultra-detailed, photorealistic, director-grade visual prompt. "
                    "Specify camera body (e.g. Hasselblad/ARRI), prime lens, volumetric lighting, micro-textures, and depth of field. "
                    "Keep it under 65 words. Output ONLY the raw expanded prompt without any preamble or quotes."
                )
                payload = {
                    "contents": [{"parts": [{"text": f"{system_instruction}\nPrompt: {clean_subject}"}]}]
                }
                req = urllib.request.Request(
                    gemini_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        text_val = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if len(text_val) > 20:
                            return {
                                "original_prompt": raw_prompt,
                                "enhanced_prompt": text_val,
                                "category": category,
                                "applied_tags": ["Google Gemini Director", "8K Cinema Optics", "Volumetric Light", "Macro Textures"]
                            }
            except Exception as e:
                pass  # Fall through to high-precision category engine

        category_presets = {
            "FOOD_ORGANIC": {
                "prefix": f"Extreme macro commercial studio photography of {subject_display}",
                "optics": "shot on Hasselblad H6D-100c with HC 100mm f/2.2 Macro lens",
                "textures": "glistening morning condensation dew droplets on waxy skin, ultra-fine organic pores, crisp natural cuticle micro-reflections",
                "lighting": "commercial edge rim lighting, soft diffused directional studio bounce, deep chiaroscuro contrast",
                "backdrop": "resting on a dark textured slate background with subtle water reflections",
                "finish": "award-winning culinary magazine cover, shallow depth of field, creamy smooth bokeh, Octane render 8K UHD",
                "tags": ["Macro Optics", "Dew Droplets", "Hasselblad 100c", "Chiaroscuro", "8K Octane"]
            },
            "ANIMAL_WILDLIFE": {
                "prefix": f"Intimate wildlife portrait of {subject_display}",
                "optics": "shot on Sony Alpha 1 with FE 400mm f/2.8 GM OSS telephoto lens",
                "textures": "individual fur strand definition, glistening wet nose texture, razor-sharp lifelike eye reflections, delicate whiskers",
                "lighting": "soft natural golden hour backlight, delicate rim glow separating subject from background, warm atmospheric fill",
                "backdrop": "lush softly blurred natural habitat with dappled sunbeams",
                "finish": "National Geographic award winner, tack sharp focus on eyes, ultra shallow depth of field, 8K ultra realistic",
                "tags": ["Sony Alpha 1", "Fur Definition", "Golden Backlight", "400mm Prime", "National Geographic"]
            },
            "CHARACTER_PORTRAIT": {
                "prefix": f"Cinematic close-up portrait of {subject_display}",
                "optics": "shot on ARRI Alexa Mini LF with Cooke Anamorphic /i Full Frame Plus 85mm T2.3 lens",
                "textures": "realistic human skin pores, micro-peach fuzz, subsurface scattering, razor-sharp eye catchlights, strand-level hair definition",
                "lighting": "Rembrandt lighting, soft warm key light, gentle cyan-teal edge backlight, deep cinematic shadows",
                "backdrop": "atmospheric background with soft volumetric blur",
                "finish": "IMAX cinematic aesthetic, Kodak Vision3 500T film grain, DaVinci Resolve color grade, 8K photorealistic",
                "tags": ["ARRI Alexa LF", "Cooke Anamorphic", "Rembrandt Lighting", "Subsurface Scattering", "8K Film Grain"]
            },
            "LANDSCAPE_NATURE": {
                "prefix": f"Epic sweeping panoramic vista of {subject_display}",
                "optics": "shot on RED V-Raptor 8K VV with Canon Cine 24mm T1.5 prime lens",
                "textures": "crisp atmospheric mist swirling through terrain, airborne particulate motes, wet rock reflections, sharp foliage detail",
                "lighting": "golden hour sunlight cresting the horizon, dramatic volumetric god rays breaking through clouds, HDR dynamic range",
                "backdrop": "majestic endless horizon with layered mountain silhouettes",
                "finish": "National Geographic award-winning photography, deep focus infinity clarity, hyper-detailed 8K vista",
                "tags": ["RED V-Raptor 8K", "Golden Hour", "God Rays", "Infinite Depth", "National Geographic"]
            },
            "URBAN_SCIFI_ARCHITECTURE": {
                "prefix": f"Atmospheric cinematic architectural view of {subject_display}",
                "optics": "shot on Sony Venice 2 with Panavision Primo 35mm T1.9 lens",
                "textures": "wet asphalt with vivid neon puddle reflections, brushed metal panelling, volumetric steam rising from vents, intricate structural symmetry",
                "lighting": "moody dual-tone neon luminescence (cyan and amber), deep volumetric atmospheric haze, rim edge highlights",
                "backdrop": "towering monolithic architecture fading into low-hanging clouds",
                "finish": "Unreal Engine 5.4 Lumen render, raytraced reflections, 8K hyper-detailed, blade runner cyberpunk aesthetic",
                "tags": ["Sony Venice 2", "Neon Reflections", "Lumen Raytracing", "Volumetric Steam", "8K Architecture"]
            },
            "VEHICLE_ACTION": {
                "prefix": f"Dynamic low-angle high-speed tracking shot of {subject_display}",
                "optics": "shot on Phantom Flex4K with Leica Summilux-C 50mm lens",
                "textures": "glossy automotive multi-coat clearcoat reflections, carbon fiber weave texture, specular highlights on aerodynamic curves, motion-blurred road surface",
                "lighting": "dramatic automotive studio rim lighting, crisp headlight illumination beams, dark glossy tarmac reflections",
                "backdrop": "motion-blurred winding coastal highway at twilight",
                "finish": "Speedhunters commercial automotive grade, 8K ultra photorealistic, raytraced reflections, cinematic color grade",
                "tags": ["Phantom Flex4K", "Automotive Clearcoat", "Motion Blur", "Specular Highlights", "8K Commercial"]
            },
            "FANTASY_MYTHICAL": {
                "prefix": f"Breathtaking dark fantasy illustration of {subject_display}",
                "optics": "cinematic wide composition, anamorphic 2.39:1 aspect ratio",
                "textures": "intricate crystalline fractures, ethereal glowing runes, drifting stardust particles, hyper-detailed organic scales and metals",
                "lighting": "magical bioluminescent rim glow, celestial moonlight rays piercing twilight haze, volumetric fog",
                "backdrop": "ancient enchanted landscape under a cosmic aurora nebula sky",
                "finish": "ArtStation Trending, masterwork concept art, Octane 8K render, Greg Rutkowski and Craig Mullins aesthetic",
                "tags": ["Dark Fantasy", "Bioluminescence", "Cosmic Aurora", "Octane 8K", "ArtStation Masterpiece"]
            },
            "GENERAL": {
                "prefix": f"Masterpiece cinematic capture of {subject_display}",
                "optics": "shot on 70mm Panavision IMAX camera with prime cinema optics",
                "textures": "tactile micro-surface details, crisp physical textures, lifelike depth, natural material properties",
                "lighting": "three-point studio lighting, soft diffused fill, crisp dramatic rim highlights",
                "backdrop": "clean atmospheric depth with subtle cinematic blur",
                "finish": "8K UHD, Octane 3D hyper-photorealistic render, Hasselblad natural color science, award-winning composition, shallow depth of field",
                "tags": ["Panavision 70mm", "Octane Render", "Three-Point Light", "8K Masterpiece", "Shallow DOF"]
            }
        }

        preset = category_presets.get(category, category_presets["GENERAL"])
        enhanced_prompt = (
            f"{preset['prefix']}, {preset['optics']}, {preset['textures']}, "
            f"{preset['lighting']}, {preset['backdrop']}, {preset['finish']}"
        )

        return {
            "original_prompt": raw_prompt,
            "enhanced_prompt": enhanced_prompt,
            "category": category,
            "applied_tags": preset["tags"]
        }

    def generate_camera_trajectory(self, camera_type: str, fov: int = 85, roll: float = 0.0, pitch: float = 0.0, speed: float = 1.0) -> Dict[str, Any]:
        """
        Computes 3D trajectory matrix transformations for GimbalFlow Camera Visualizer.
        """
        steps = 10
        paths = []
        for i in range(steps):
            t = (i / float(steps - 1)) * speed
            x = math.sin(t * math.pi * 2) * 5.0
            y = math.cos(t * math.pi * 2) * 3.0 + pitch
            z = t * 10.0 + roll
            paths.append({"time": round(t, 2), "x": round(x, 3), "y": round(y, 3), "z": round(z, 3)})

        matrix_3d = [
            [1.0, 0.0, 0.0, pitch],
            [0.0, 1.0, 0.0, roll],
            [0.0, 0.0, 1.0, float(fov)],
            [0.0, 0.0, 0.0, 1.0]
        ]

        return {
            "camera_type": camera_type,
            "matrix_3d": matrix_3d,
            "keyframe_paths": paths
        }

    def execute_generation_pipeline(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates ML model inference pipeline (diffusion steps, latent space sampling).
        """
        start_time = time.time()
        job_id = f"gen-py-{int(time.time() * 1000)}"
        
        gen_type = request_data.get("type", "video")
        prompt = request_data.get("prompt", "")
        model = request_data.get("model", "Seedance v2")
        aspect_ratio = request_data.get("aspectRatio") or request_data.get("aspect_ratio", "16:9")
        camera = request_data.get("camera", "FPV Drone Swoop 360°")
        ref_img = request_data.get("referenceImg") or request_data.get("reference_img")

        media_url = ref_img if ref_img else random.choice(self.STOCK_MEDIA)
        cost_map = {"image": 10, "video": 25, "cinema": 30}
        cost = cost_map.get(gen_type, 20)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "job_id": job_id,
            "status": "completed",
            "type": gen_type,
            "media_url": media_url,
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "camera": camera,
            "cost": cost,
            "execution_time_ms": elapsed_ms
        }

ml_engine = GimbalFlowMLEngine()
