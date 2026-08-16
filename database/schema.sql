-- ============================================================
-- GimbalFlow Production Relational Database Schema (MySQL 8.0)
-- Strict Table Partitioning & High Concurrency Design
-- ============================================================

CREATE DATABASE IF NOT EXISTS gimbalflow_db
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE gimbalflow_db;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    credits_balance INT NOT NULL DEFAULT 2450,
    plan_tier VARCHAR(50) DEFAULT 'Pro Creator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. PROJECTS TABLE
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'usr-demo-01',
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'video',
    scenes_count INT DEFAULT 1,
    items_count INT DEFAULT 1,
    tag VARCHAR(100) DEFAULT 'General',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_projects_user (user_id),
    INDEX idx_projects_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. ASSETS TABLE
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'usr-demo-01',
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'character',
    tag VARCHAR(100) DEFAULT 'Soul ID Character',
    tag_class VARCHAR(50) DEFAULT 'soul',
    meta VARCHAR(255) DEFAULT 'Used in 1 Project',
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_assets_user (user_id),
    INDEX idx_assets_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. GENERATIONS TABLE
CREATE TABLE IF NOT EXISTS generations (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'usr-demo-01',
    type VARCHAR(50) NOT NULL, -- image, video, cinema
    prompt TEXT NOT NULL,
    model VARCHAR(100) NOT NULL,
    aspect_ratio VARCHAR(20) DEFAULT '16:9',
    camera VARCHAR(100) DEFAULT 'FPV Drone Swoop 360°',
    status VARCHAR(50) NOT NULL DEFAULT 'completed', -- queued, processing, completed, failed
    media_url TEXT,
    cost INT DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_gen_user (user_id),
    INDEX idx_gen_status (status),
    INDEX idx_gen_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. PRESETS TABLE
CREATE TABLE IF NOT EXISTS presets (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    creator VARCHAR(100) DEFAULT 'GimbalFlow Official',
    popularity VARCHAR(50) DEFAULT '10k+ Uses',
    description TEXT,
    camera VARCHAR(100),
    lens VARCHAR(100),
    aspect_ratio VARCHAR(20) DEFAULT '16:9',
    model VARCHAR(100) DEFAULT 'Seedance v2',
    prompt_template TEXT NOT NULL,
    thumbnail TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. EXPLORE ITEMS TABLE
CREATE TABLE IF NOT EXISTS explore_items (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    creator VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'cinema',
    media_url TEXT NOT NULL,
    is_video BOOLEAN DEFAULT TRUE,
    likes INT DEFAULT 0,
    model VARCHAR(100) DEFAULT 'Seedance v2',
    aspect_ratio VARCHAR(20) DEFAULT '16:9',
    duration VARCHAR(20) DEFAULT '0:06',
    prompt TEXT NOT NULL,
    camera VARCHAR(100),
    lens VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_explore_likes (likes DESC),
    INDEX idx_explore_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. REAL-TIME TASK JOBS BUFFER TABLE
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(64) PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payload JSON,
    result JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_jobs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================
-- INITIAL SEED DATA
-- ============================================================

INSERT INTO users (id, email, name, avatar_url, credits_balance, plan_tier) VALUES
('usr-demo-01', 'director@gimbalflow.ai', 'Alex Rivera', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop', 2450, 'Pro Director')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO projects (id, user_id, title, type, scenes_count, items_count, tag) VALUES
('proj-1', 'usr-demo-01', 'TOKYO NIGHT 2099', 'cinema', 12, 48, 'Cinema Film'),
('proj-2', 'usr-demo-01', 'CYBERPUNK CHASE SCENE', 'video', 4, 16, '60FPS Video'),
('proj-3', 'usr-demo-01', 'DUNE HORIZON KEYFRAMES', 'image', 8, 24, '8K Textures')
ON DUPLICATE KEY UPDATE title=VALUES(title);

INSERT INTO assets (id, user_id, name, type, tag, tag_class, meta, url) VALUES
('ast-1', 'usr-demo-01', 'Kira Vance (Protagonist)', 'character', 'Soul ID Character', 'soul', 'Used in 4 Projects', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop'),
('ast-2', 'usr-demo-01', 'Neo-Tokyo Skydeck 2099', 'location', '3D Set', 'location', 'Used in 2 Projects', 'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=500&auto=format&fit=crop'),
('ast-3', 'usr-demo-01', 'Blade Runner Cyber Tone', 'style', 'Color Style', 'style', 'Used in 6 Projects', 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO explore_items (id, title, creator, type, media_url, is_video, likes, model, aspect_ratio, duration, prompt, camera, lens) VALUES
('exp-1', 'Neo-Tokyo Cyberpunk Rain Chase', 'Alex Rivera', 'cinema', 'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1000&auto=format&fit=crop', TRUE, 342, 'Seedance v2', '16:9', '0:06', 'Anamorphic 35mm wide shot of a futuristic cyberpunk director in a neon lit Tokyo alleyway, 60fps fluid motion, hyperrealistic rain reflections.', 'FPV Drone Swoop 360°', '35mm Prime Anamorphic'),
('exp-2', 'Dune Desert Nomad Portrait', 'Elena Rostova', 'image', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1000&auto=format&fit=crop', FALSE, 512, 'Higgsfield Cinema Pro', '1:1', '0:00', 'Cinematic 8K portrait of a sand-covered nomad in golden hour sunlight, volumetric dust particles, extreme detail.', 'Portrait 85mm Bokeh', '85mm Prime'),
('exp-3', 'Sci-Fi Hangar Mech Drop', 'Kenji Sato', 'video', 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1000&auto=format&fit=crop', TRUE, 289, 'ActionDiff v3', '16:9', '0:05', 'Heavy giant mech drops into futuristic steel hangar, dynamic camera shake, sparks flying, cinematic lighting.', 'Dolly Push In', '35mm Prime Anamorphic'),
('exp-4', 'Neon Cyber Samurai Duel', 'Marcus Vance', 'cinema', 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1000&auto=format&fit=crop', TRUE, 418, 'Seedance v2', '21:9', '0:08', 'Two cyborg samurai clashing katana blades under flickering neon signboards, slow motion sparks, rain soaked asphalt.', '360° Character Orbit', '50mm Cinema Anamorphic')
ON DUPLICATE KEY UPDATE title=VALUES(title);

INSERT INTO presets (id, title, category, creator, popularity, description, camera, lens, aspect_ratio, model, prompt_template, thumbnail) VALUES
('pst-1', 'Cinematic 360° FPV Swoop', 'Cinematic', 'GimbalFlow Official', '12.4k Uses', 'High-speed FPV drone swoop around character with volumetric lighting.', 'FPV Drone Swoop 360°', '24mm Wide Anamorphic', '16:9', 'Seedance v2', '[Subject] walking through [Location], dramatic volumetric rim lighting, 60fps high speed camera trajectory.', 'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=500&auto=format&fit=crop'),
('pst-2', 'Soul ID Character Portrait', 'Character', 'GimbalFlow Official', '9.8k Uses', 'Hyper-detailed 8K portrait render locked to persistent character geometry.', 'Portrait 85mm Bokeh', '85mm Prime', '1:1', 'Higgsfield Cinema Pro', 'Studio lighting 8K portrait of @character, shallow depth of field, sharp eyes, cinematic color grading.', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop'),
('pst-3', 'High-Speed Action Explosion', 'Action', 'Studio-H FX', '7.1k Uses', 'Dynamic slow-mo action pass with realistic particle physics and camera shake.', 'Dolly Push In', '35mm Prime Anamorphic', '16:9', 'ActionDiff v3', '[Action scene] with heavy explosions in background, camera shake, slow motion retiming 0.2x.', 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop')
ON DUPLICATE KEY UPDATE title=VALUES(title);
