"""
提示词模板管理服务

负责加载、管理和应用提示词模板
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

from backend.core.config import PROJECT_ROOT
from backend.core.logging import logger


class PromptTemplate:
    """提示词模板"""

    def __init__(
        self,
        name: str,
        category: str,
        prompt: str,
        negative_prompt: str = "",
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        description: str = "",
    ):
        self.name = name
        self.category = category
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.params = params or {}
        self.tags = tags or []
        self.description = description

    def render(self, **kwargs) -> Dict[str, Any]:
        """
        渲染模板，替换占位符

        Args:
            **kwargs: 用于替换模板中的占位符

        Returns:
            {
                "prompt": str,
                "negative_prompt": str,
                "params": dict
            }
        """
        # 替换prompt中的占位符
        prompt = self._replace_placeholders(self.prompt, **kwargs)
        negative_prompt = self._replace_placeholders(self.negative_prompt, **kwargs)

        return {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "params": self.params.copy(),
        }

    def _replace_placeholders(self, text: str, **kwargs) -> str:
        """替换文本中的{key}占位符"""
        pattern = r"\{(\w+)\}"

        def replace_func(match):
            key = match.group(1)
            return str(kwargs.get(key, ""))

        return re.sub(pattern, replace_func, text)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "category": self.category,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "params": self.params,
            "tags": self.tags,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """从字典创建模板"""
        return cls(
            name=data["name"],
            category=data.get("category", "general"),
            prompt=data["prompt"],
            negative_prompt=data.get("negative_prompt", ""),
            params=data.get("params", {}),
            tags=data.get("tags", []),
            description=data.get("description", ""),
        )


class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        初始化模板管理器

        Args:
            templates_dir: 模板目录路径
        """
        self.templates_dir = templates_dir or (PROJECT_ROOT / "templates" / "prompts")
        self.templates: Dict[str, PromptTemplate] = {}
        self.categories: Dict[str, List[str]] = {}  # category -> [template_names]

        # 加载所有模板
        self.load_templates()

    def load_templates(self):
        """从YAML文件加载所有模板"""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return

        yaml_files = list(self.templates_dir.glob("*.yaml"))
        logger.info(f"Loading templates from {len(yaml_files)} files")

        for yaml_file in yaml_files:
            try:
                self._load_yaml_file(yaml_file)
            except Exception as e:
                logger.error(f"Failed to load template file {yaml_file}: {e}")

        logger.info(f"Loaded {len(self.templates)} templates in {len(self.categories)} categories")

    def _load_yaml_file(self, yaml_file: Path):
        """加载单个YAML文件"""
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "templates" not in data:
            logger.warning(f"Invalid template file format: {yaml_file}")
            return

        for template_data in data["templates"]:
            template = PromptTemplate.from_dict(template_data)

            # 存储模板
            self.templates[template.name] = template

            # 分类索引
            if template.category not in self.categories:
                self.categories[template.category] = []
            self.categories[template.category].append(template.name)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        获取指定名称的模板

        Args:
            name: 模板名称

        Returns:
            PromptTemplate或None
        """
        return self.templates.get(name)

    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """
        获取指定分类的所有模板

        Args:
            category: 分类名称

        Returns:
            模板列表
        """
        template_names = self.categories.get(category, [])
        return [self.templates[name] for name in template_names]

    def search_templates(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[PromptTemplate]:
        """
        搜索模板

        Args:
            keyword: 关键词（搜索名称和描述）
            category: 分类筛选
            tags: 标签筛选

        Returns:
            匹配的模板列表
        """
        results = []

        for template in self.templates.values():
            # 分类筛选
            if category and template.category != category:
                continue

            # 标签筛选
            if tags and not any(tag in template.tags for tag in tags):
                continue

            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if (
                    keyword_lower not in template.name.lower()
                    and keyword_lower not in template.description.lower()
                ):
                    continue

            results.append(template)

        return results

    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return list(self.categories.keys())

    def list_all_templates(self) -> List[PromptTemplate]:
        """列出所有模板"""
        return list(self.templates.values())

    def add_custom_template(
        self,
        name: str,
        prompt: str,
        category: str = "custom",
        negative_prompt: str = "",
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> PromptTemplate:
        """
        添加自定义模板

        Args:
            name: 模板名称
            prompt: 提示词
            category: 分类
            negative_prompt: 负向提示词
            params: 参数
            tags: 标签
            description: 描述

        Returns:
            创建的模板
        """
        if name in self.templates:
            raise ValueError(f"Template with name '{name}' already exists")

        template = PromptTemplate(
            name=name,
            category=category,
            prompt=prompt,
            negative_prompt=negative_prompt,
            params=params,
            tags=tags or [],
            description=description,
        )

        self.templates[name] = template

        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)

        logger.info(f"Added custom template: {name}")
        return template

    def remove_template(self, name: str) -> bool:
        """
        删除模板

        Args:
            name: 模板名称

        Returns:
            是否成功删除
        """
        if name not in self.templates:
            return False

        template = self.templates[name]
        del self.templates[name]

        # 从分类索引中移除
        if template.category in self.categories:
            self.categories[template.category].remove(name)
            if not self.categories[template.category]:
                del self.categories[template.category]

        logger.info(f"Removed template: {name}")
        return True

    def save_custom_templates(self, output_file: Optional[Path] = None):
        """
        保存自定义模板到YAML文件

        Args:
            output_file: 输出文件路径
        """
        if output_file is None:
            output_file = self.templates_dir / "custom.yaml"

        # 只保存custom分类的模板
        custom_templates = self.get_templates_by_category("custom")

        if not custom_templates:
            logger.info("No custom templates to save")
            return

        data = {
            "templates": [template.to_dict() for template in custom_templates]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Saved {len(custom_templates)} custom templates to {output_file}")

    def render_template(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        渲染指定模板

        Args:
            name: 模板名称
            **kwargs: 渲染参数

        Returns:
            渲染后的prompt和params

        Raises:
            ValueError: 模板不存在
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        return template.render(**kwargs)


# 创建全局模板管理器实例
template_manager = PromptTemplateManager()


if __name__ == "__main__":
    # 测试模板管理器
    print("=" * 60)
    print("提示词模板管理器测试")
    print("=" * 60)

    # 列出所有分类
    print(f"\n分类: {template_manager.list_categories()}")

    # 列出所有模板
    print(f"\n总共 {len(template_manager.list_all_templates())} 个模板")

    # 获取指定模板
    template = template_manager.get_template("高质量照片")
    if template:
        print(f"\n模板: {template.name}")
        print(f"描述: {template.description}")
        print(f"标签: {template.tags}")

        # 渲染模板
        rendered = template.render(description="a beautiful sunset over the ocean")
        print(f"\n渲染后的prompt: {rendered['prompt']}")
        print(f"负向prompt: {rendered['negative_prompt']}")
        print(f"参数: {rendered['params']}")

    # 搜索模板
    results = template_manager.search_templates(keyword="车辆")
    print(f"\n搜索 '车辆': 找到 {len(results)} 个模板")
    for t in results:
        print(f"  - {t.name} ({t.category})")

    print("=" * 60)
