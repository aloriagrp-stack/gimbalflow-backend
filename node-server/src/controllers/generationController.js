const { enqueueTask } = require('../config/redis');
const { enhancePromptWithFastAPI, generateMLJobWithFastAPI } = require('../services/fastApiClient');
const { isMySQLActive, getPool, getMemoryDb } = require('../config/db');

async function enhancePrompt(req, res) {
  try {
    const { prompt } = req.body;
    if (!prompt) return res.status(400).json({ error: 'Prompt is required' });

    const enhanced = await enhancePromptWithFastAPI(prompt);
    res.json(enhanced);
  } catch (err) {
    console.error('enhancePrompt error:', err);
    res.status(500).json({ error: 'Failed to enhance prompt' });
  }
}

async function createGenerationJob(req, res) {
  try {
    const { type, prompt, model, aspectRatio, camera, resolution, numImages, guidance, steps, referenceImg } = req.body;
    if (!prompt) return res.status(400).json({ error: 'Prompt is required' });

    // Enqueue task to Redis real-time task queue
    const queueItem = await enqueueTask('generation_tasks', {
      type,
      prompt,
      model,
      aspectRatio,
      camera
    });

    // Execute via Python FastAPI ML Engine
    const mlResult = await generateMLJobWithFastAPI({
      type,
      prompt,
      model,
      aspectRatio,
      camera,
      resolution,
      numImages,
      guidance,
      steps,
      referenceImg
    });

    const generationRecord = {
      id: mlResult.job_id || `gen-${Date.now()}`,
      user_id: 'usr-demo-01',
      type: type || 'video',
      prompt,
      model: model || 'Seedance v2',
      aspectRatio: aspectRatio || '16:9',
      camera: camera || 'FPV Drone Swoop 360°',
      status: mlResult.status || 'completed',
      mediaUrl: mlResult.media_url,
      cost: mlResult.cost || 20,
      createdAt: new Date().toISOString()
    };

    if (isMySQLActive()) {
      const pool = getPool();
      await pool.query(
        'INSERT INTO generations (id, user_id, type, prompt, model, aspect_ratio, camera, status, media_url, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [generationRecord.id, generationRecord.user_id, generationRecord.type, generationRecord.prompt, generationRecord.model, generationRecord.aspectRatio, generationRecord.camera, generationRecord.status, generationRecord.mediaUrl, generationRecord.cost]
      );
    } else {
      const memoryDb = getMemoryDb();
      memoryDb.generations.unshift(generationRecord);
    }

    res.status(201).json({
      success: true,
      task: queueItem,
      result: generationRecord
    });
  } catch (err) {
    console.error('createGenerationJob error:', err);
    res.status(500).json({ error: 'Failed to process generation job' });
  }
}

module.exports = { enhancePrompt, createGenerationJob };
