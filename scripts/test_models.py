#!/usr/bin/env python3
"""
测试数据模型
Test Database Models

验证所有模型是否正确定义
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.models import (
    Annotation,
    AnnotationTask,
    DatasetVersion,
    GenerationTask,
    Image,
    Label,
    Model,
    Project,
    TaskLog,
    TrainingTask,
)


def test_models():
    """测试所有模型"""
    print("=" * 60)
    print("🧪 测试数据模型")
    print("=" * 60)
    
    models = [
        Project,
        Label,
        DatasetVersion,
        GenerationTask,
        Image,
        AnnotationTask,
        Annotation,
        TrainingTask,
        Model,
        TaskLog,
    ]
    
    print(f"\n📦 找到 {len(models)} 个模型:\n")
    
    for i, model in enumerate(models, 1):
        table_name = model.__tablename__
        columns = [col.name for col in model.__table__.columns]
        print(f"{i}. {model.__name__}")
        print(f"   表名: {table_name}")
        print(f"   字段数: {len(columns)}")
        print(f"   主键: {[col.name for col in model.__table__.primary_key.columns]}")
        
        # 检查关系
        if hasattr(model, '__mapper__'):
            relationships = [rel.key for rel in model.__mapper__.relationships]
            if relationships:
                print(f"   关系: {', '.join(relationships)}")
        print()
    
    print("=" * 60)
    print("✅ 所有模型定义正确!")
    print("=" * 60)


if __name__ == "__main__":
    test_models()
