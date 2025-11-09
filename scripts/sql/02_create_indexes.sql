-- 索引创建脚本
-- 提升查询性能

-- projects表索引
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);

-- labels表索引
CREATE INDEX IF NOT EXISTS idx_labels_project ON labels(project_id);
CREATE INDEX IF NOT EXISTS idx_labels_active ON labels(is_active);

-- dataset_versions表索引
CREATE INDEX IF NOT EXISTS idx_dataset_versions_project ON dataset_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_dataset_versions_status ON dataset_versions(status);

-- generation_tasks表索引
CREATE INDEX IF NOT EXISTS idx_generation_tasks_project ON generation_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_generation_tasks_status ON generation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_generation_tasks_created ON generation_tasks(created_at DESC);

-- images表索引
CREATE INDEX IF NOT EXISTS idx_images_task ON images(generation_task_id);
CREATE INDEX IF NOT EXISTS idx_images_dataset ON images(dataset_version_id);
CREATE INDEX IF NOT EXISTS idx_images_review ON images(review_status);
CREATE INDEX IF NOT EXISTS idx_images_split ON images(split_type);
CREATE INDEX IF NOT EXISTS idx_images_created ON images(created_at DESC);

-- annotation_tasks表索引
CREATE INDEX IF NOT EXISTS idx_annotation_tasks_project ON annotation_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_annotation_tasks_dataset ON annotation_tasks(dataset_version_id);
CREATE INDEX IF NOT EXISTS idx_annotation_tasks_status ON annotation_tasks(status);

-- annotations表索引
CREATE INDEX IF NOT EXISTS idx_annotations_task ON annotations(annotation_task_id);
CREATE INDEX IF NOT EXISTS idx_annotations_image ON annotations(image_id);
CREATE INDEX IF NOT EXISTS idx_annotations_label ON annotations(label_id);
CREATE INDEX IF NOT EXISTS idx_annotations_verified ON annotations(is_verified);
CREATE INDEX IF NOT EXISTS idx_annotations_correct ON annotations(is_correct);

-- training_tasks表索引
CREATE INDEX IF NOT EXISTS idx_training_tasks_project ON training_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_training_tasks_dataset ON training_tasks(dataset_version_id);
CREATE INDEX IF NOT EXISTS idx_training_tasks_status ON training_tasks(status);
CREATE INDEX IF NOT EXISTS idx_training_tasks_created ON training_tasks(created_at DESC);

-- models表索引
CREATE INDEX IF NOT EXISTS idx_models_project ON models(project_id);
CREATE INDEX IF NOT EXISTS idx_models_training_task ON models(training_task_id);
CREATE INDEX IF NOT EXISTS idx_models_best ON models(is_best);
CREATE INDEX IF NOT EXISTS idx_models_deployed ON models(is_deployed);
CREATE INDEX IF NOT EXISTS idx_models_created ON models(created_at DESC);

-- task_logs表索引
CREATE INDEX IF NOT EXISTS idx_task_logs_task ON task_logs(task_type, task_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_level ON task_logs(level);
CREATE INDEX IF NOT EXISTS idx_task_logs_created ON task_logs(created_at DESC);

-- 联合索引
CREATE INDEX IF NOT EXISTS idx_images_task_status ON images(generation_task_id, review_status);
CREATE INDEX IF NOT EXISTS idx_annotations_image_label ON annotations(image_id, label_id);
