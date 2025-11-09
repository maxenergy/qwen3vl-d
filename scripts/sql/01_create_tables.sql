-- 自动标注工具数据库初始化脚本
-- Auto Annotation Tool Database Schema

-- 1. 项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB,
    CONSTRAINT project_name_check CHECK (char_length(name) >= 3)
);

-- 2. 标签定义表
CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- 3. 数据集版本表
CREATE TABLE IF NOT EXISTS dataset_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- 统计信息
    total_images INTEGER DEFAULT 0,
    total_annotations INTEGER DEFAULT 0,
    train_count INTEGER DEFAULT 0,
    val_count INTEGER DEFAULT 0,
    test_count INTEGER DEFAULT 0,
    
    -- 数据集配置
    split_ratio JSONB,
    augmentation_config JSONB,
    export_formats VARCHAR[],
    
    status VARCHAR(50) DEFAULT 'building',
    UNIQUE(project_id, version)
);

-- 4. 图片生成任务表
CREATE TABLE IF NOT EXISTS generation_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dataset_version_id INTEGER REFERENCES dataset_versions(id) ON DELETE SET NULL,
    
    -- 任务配置
    task_name VARCHAR(255),
    num_images INTEGER NOT NULL,
    resolution VARCHAR(20) DEFAULT '640x640',
    
    -- 提示词配置
    prompt_template TEXT,
    prompts JSONB,
    reference_images JSONB,
    
    -- 任务状态
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    generated_count INTEGER DEFAULT 0,
    reviewed_count INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    
    -- Checkpoint数据
    checkpoint JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 错误信息
    error_message TEXT,
    
    -- Celery任务ID
    celery_task_id VARCHAR(255)
);

-- 5. 生成的图片表
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    generation_task_id INTEGER NOT NULL REFERENCES generation_tasks(id) ON DELETE CASCADE,
    dataset_version_id INTEGER REFERENCES dataset_versions(id) ON DELETE CASCADE,
    
    -- 图片信息
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    resolution VARCHAR(20),
    file_size BIGINT,
    
    -- 生成参数
    prompt TEXT,
    reference_image TEXT,
    generation_params JSONB,
    
    -- 人工审核
    review_status VARCHAR(50) DEFAULT 'pending',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    -- 数据集分配
    split_type VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(file_path)
);

-- 6. 标注任务表
CREATE TABLE IF NOT EXISTS annotation_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dataset_version_id INTEGER REFERENCES dataset_versions(id) ON DELETE CASCADE,
    
    task_name VARCHAR(255),
    
    -- 标注配置
    label_ids INTEGER[],
    image_ids INTEGER[],
    confidence_threshold FLOAT DEFAULT 0.3,
    max_detections_per_image INTEGER DEFAULT 100,
    
    -- 任务状态
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    annotated_images INTEGER DEFAULT 0,
    
    -- Qwen3-VL API配置
    api_endpoint VARCHAR(255),
    model_name VARCHAR(100),
    
    -- Checkpoint数据
    checkpoint JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    celery_task_id VARCHAR(255)
);

-- 7. 标注结果表
CREATE TABLE IF NOT EXISTS annotations (
    id SERIAL PRIMARY KEY,
    annotation_task_id INTEGER NOT NULL REFERENCES annotation_tasks(id) ON DELETE CASCADE,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    
    -- 标注数据 (Qwen3-VL原始坐标, 0-1000)
    bbox_x1 FLOAT NOT NULL,
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    confidence FLOAT,
    
    -- 归一化坐标 (YOLO格式: center_x, center_y, width, height, 0-1)
    normalized_x FLOAT,
    normalized_y FLOAT,
    normalized_w FLOAT,
    normalized_h FLOAT,
    
    -- 人工校验
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    is_correct BOOLEAN,
    correction_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT bbox_check CHECK (
        bbox_x1 >= 0 AND bbox_y1 >= 0 AND 
        bbox_x2 <= 1000 AND bbox_y2 <= 1000 AND
        bbox_x1 < bbox_x2 AND bbox_y1 < bbox_y2
    )
);

-- 8. 训练任务表
CREATE TABLE IF NOT EXISTS training_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dataset_version_id INTEGER NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    
    task_name VARCHAR(255),
    
    -- 训练配置
    yolo_version VARCHAR(20) NOT NULL,
    model_size VARCHAR(20) DEFAULT 'n',
    pretrained_model VARCHAR(255),
    
    -- 超参数
    epochs INTEGER DEFAULT 100,
    batch_size INTEGER DEFAULT 16,
    img_size INTEGER DEFAULT 640,
    learning_rate FLOAT DEFAULT 0.01,
    patience INTEGER DEFAULT 50,
    
    -- 高级配置
    use_amp BOOLEAN DEFAULT TRUE,
    multi_scale BOOLEAN DEFAULT FALSE,
    mosaic FLOAT DEFAULT 1.0,
    config_yaml TEXT,
    
    -- K-Fold配置
    use_kfold BOOLEAN DEFAULT FALSE,
    kfold_splits INTEGER DEFAULT 5,
    current_fold INTEGER,
    
    -- 任务状态
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_epoch INTEGER DEFAULT 0,
    
    -- 训练结果
    best_map50 FLOAT,
    best_map50_95 FLOAT,
    final_precision FLOAT,
    final_recall FLOAT,
    training_time_seconds INTEGER,
    
    -- Checkpoint数据
    checkpoint JSONB,
    
    -- 路径
    output_dir TEXT,
    checkpoint_path TEXT,
    best_model_path TEXT,
    tensorboard_dir TEXT,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    celery_task_id VARCHAR(255)
);

-- 9. 训练好的模型表
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    training_task_id INTEGER NOT NULL REFERENCES training_tasks(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50),
    
    -- 模型文件
    model_path TEXT NOT NULL,
    model_size_bytes BIGINT,
    
    -- 性能指标
    map50 FLOAT,
    map50_95 FLOAT,
    precision FLOAT,
    recall FLOAT,
    inference_time_ms FLOAT,
    
    -- 测试集评估
    test_results JSONB,
    
    -- 标记
    is_best BOOLEAN DEFAULT FALSE,
    is_deployed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_path)
);

-- 10. 任务日志表
CREATE TABLE IF NOT EXISTS task_logs (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    task_id INTEGER NOT NULL,
    level VARCHAR(20) DEFAULT 'INFO',
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 触发器：自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE projects IS '项目表';
COMMENT ON TABLE labels IS '标签定义表';
COMMENT ON TABLE dataset_versions IS '数据集版本表';
COMMENT ON TABLE generation_tasks IS '图片生成任务表';
COMMENT ON TABLE images IS '生成的图片表';
COMMENT ON TABLE annotation_tasks IS '标注任务表';
COMMENT ON TABLE annotations IS '标注结果表';
COMMENT ON TABLE training_tasks IS '训练任务表';
COMMENT ON TABLE models IS '训练好的模型表';
COMMENT ON TABLE task_logs IS '任务日志表';
