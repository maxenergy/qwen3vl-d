#!/usr/bin/env python3
"""
数据库初始化脚本
Database Setup Script

用法:
    python scripts/setup_database.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_params():
    """从环境变量获取数据库连接参数"""
    from dotenv import load_dotenv
    
    # 加载.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env文件不存在, 使用默认配置...")
        return {
            "host": "localhost",
            "port": 5432,
            "user": "user",
            "password": "password",
            "database": "auto_annotation"
        }
    
    load_dotenv(env_file)
    
    # 解析DATABASE_URL或使用默认值
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/auto_annotation")
    
    # 简单解析DATABASE_URL
    # postgresql://user:password@localhost:5432/database
    if database_url.startswith("postgresql://"):
        url = database_url.replace("postgresql://", "")
        if "@" in url:
            auth, host_db = url.split("@")
            user, password = auth.split(":")
            host_port, database = host_db.split("/")
            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host, port = host_port, 5432
            
            return {
                "host": host,
                "port": int(port),
                "user": user,
                "password": password,
                "database": database
            }
    
    return {
        "host": "localhost",
        "port": 5432,
        "user": "user",
        "password": "password",
        "database": "auto_annotation"
    }


def create_database(params):
    """创建数据库(如果不存在)"""
    print(f"📦 检查数据库 '{params['database']}'...")
    
    # 连接到postgres数据库
    conn = psycopg2.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # 检查数据库是否存在
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (params['database'],)
    )
    exists = cursor.fetchone()
    
    if not exists:
        print(f"✨ 创建数据库 '{params['database']}'...")
        cursor.execute(f"CREATE DATABASE {params['database']}")
        print(f"✅ 数据库创建成功!")
    else:
        print(f"✅ 数据库已存在")
    
    cursor.close()
    conn.close()


def execute_sql_file(conn, filepath):
    """执行SQL文件"""
    print(f"📄 执行: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"   ✅ 完成")
    except Exception as e:
        conn.rollback()
        print(f"   ❌ 错误: {e}")
        raise
    finally:
        cursor.close()


def run_migrations(params):
    """运行数据库迁移"""
    print(f"\n🔧 运行数据库迁移...")
    
    # 连接到目标数据库
    conn = psycopg2.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        database=params['database']
    )
    
    try:
        # SQL脚本目录
        sql_dir = project_root / "scripts" / "sql"
        
        # 按顺序执行SQL文件
        sql_files = sorted(sql_dir.glob("*.sql"))
        
        if not sql_files:
            print("⚠️  未找到SQL脚本文件")
            return
        
        for sql_file in sql_files:
            execute_sql_file(conn, sql_file)
        
        print(f"\n✅ 所有迁移执行成功!")
        
    finally:
        conn.close()


def verify_tables(params):
    """验证表是否创建成功"""
    print(f"\n🔍 验证数据库表...")
    
    conn = psycopg2.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        database=params['database']
    )
    
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'projects',
        'labels',
        'dataset_versions',
        'generation_tasks',
        'images',
        'annotation_tasks',
        'annotations',
        'training_tasks',
        'models',
        'task_logs'
    ]
    
    print(f"📊 找到 {len(tables)} 个表:")
    for table in tables:
        status = "✅" if table in expected_tables else "❓"
        print(f"   {status} {table}")
    
    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"\n⚠️  缺少表: {', '.join(missing)}")
    else:
        print(f"\n✅ 所有必需的表都已创建!")
    
    cursor.close()
    conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 自动标注工具 - 数据库初始化")
    print("   Auto Annotation Tool - Database Setup")
    print("=" * 60)
    
    try:
        # 获取数据库参数
        params = get_db_params()
        print(f"\n📌 连接信息:")
        print(f"   主机: {params['host']}:{params['port']}")
        print(f"   用户: {params['user']}")
        print(f"   数据库: {params['database']}")
        
        # 创建数据库
        create_database(params)
        
        # 运行迁移
        run_migrations(params)
        
        # 验证表
        verify_tables(params)
        
        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
