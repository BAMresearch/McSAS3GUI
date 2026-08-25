#!/usr/bin/env python3
"""Generate a Mermaid dependency diagram for internal McSAS3GUI modules."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src" / "mcsas3gui"
OUTPUT_PATH = ROOT / "docs" / "generated_module_dependencies.md"

LAYER_ORDER = (
    "Entry points and bootstrap",
    "GUI tabs",
    "GUI bridge, workers, and shared helpers",
    "Other internal modules",
)

LAYER_MEMBERS = {
    "Entry points and bootstrap": {
        "__init__",
        "__main__",
        "_bootstrap",
        "main",
    },
    "GUI tabs": {
        "gui.data_loading_tab",
        "gui.getting_started_tab",
        "gui.hist_run_tab",
        "gui.hist_settings_tab",
        "gui.main_window",
        "gui.optimization_tab",
        "gui.run_settings_tab",
    },
    "GUI bridge, workers, and shared helpers": {
        "gui.file_line_selection_widget",
        "gui.file_selection_helpers",
        "gui.file_selection_widget",
        "gui.mcsas3_bridge",
        "gui.optimization_worker",
        "gui.run_control_helpers",
        "gui.run_settings_helpers",
        "gui.yaml_editor_widget",
        "utils.base_worker",
        "utils.mcsas3_cli",
        "utils.task_runner_mixin",
    },
}


def discover_modules() -> dict[str, Path]:
    """Return the top-level and subpackage Python modules that make up McSAS3GUI."""

    modules: dict[str, Path] = {}
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        modules[path.stem] = path
    for subpackage in ("gui", "utils"):
        subpackage_dir = PACKAGE_DIR / subpackage
        for path in sorted(subpackage_dir.glob("*.py")):
            modules[f"{subpackage}.{path.stem}"] = path
    return modules


def resolve_local_dependency(import_name: str, local_modules: set[str]) -> str | None:
    """Map an import target to a local dotted module when possible."""

    if import_name.startswith("mcsas3gui."):
        candidate = import_name.removeprefix("mcsas3gui.")
    else:
        candidate = import_name
    return candidate if candidate in local_modules else None


def resolve_relative_import(module_name: str, level: int, target: str | None) -> str | None:
    """Resolve a relative import target to a dotted local module name."""

    package_parts = module_name.split(".")[:-1]
    anchor = len(package_parts) - (level - 1)
    if anchor < 0:
        return None
    base_parts = package_parts[:anchor]
    if target:
        return ".".join(base_parts + target.split("."))
    return ".".join(base_parts)


def parse_local_dependencies(module_name: str, module_path: Path, local_modules: set[str]) -> set[str]:
    """Parse a module and collect imports that point to local McSAS3GUI modules."""

    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    dependencies: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependency = resolve_local_dependency(alias.name, local_modules)
                if dependency is not None and dependency != module_name:
                    dependencies.add(dependency)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                if node.module:
                    dependency = resolve_relative_import(module_name, node.level, node.module)
                    if dependency in local_modules and dependency != module_name:
                        dependencies.add(dependency)
                else:
                    for alias in node.names:
                        dependency = resolve_relative_import(module_name, node.level, alias.name)
                        if dependency in local_modules and dependency != module_name:
                            dependencies.add(dependency)
            elif node.module is not None:
                dependency = resolve_local_dependency(node.module, local_modules)
                if dependency is not None and dependency != module_name:
                    dependencies.add(dependency)

    return dependencies


def module_layer(module_name: str) -> str:
    """Return the display layer used for a module in the diagram."""

    for layer_name, members in LAYER_MEMBERS.items():
        if module_name in members:
            return layer_name
    return "Other internal modules"


def mermaid_node_id(module_name: str) -> str:
    """Return a Mermaid-safe node identifier."""

    return f"module_{module_name.replace('-', '_').replace('.', '_')}"


def generate_markdown() -> str:
    """Generate the dependency diagram markdown."""

    modules = discover_modules()
    local_modules = set(modules)
    dependencies = {
        module_name: parse_local_dependencies(module_name, module_path, local_modules)
        for module_name, module_path in modules.items()
    }
    layer_to_modules: dict[str, list[str]] = defaultdict(list)
    for module_name in modules:
        layer_to_modules[module_layer(module_name)].append(module_name)
    for module_names in layer_to_modules.values():
        module_names.sort()

    lines: list[str] = [
        "# McSAS3GUI Module Dependency Diagram",
        "",
        "This file is generated by `python tools/generate_dependency_diagram.py`.",
        "It captures imports between maintained internal modules in `src/mcsas3gui` and is intended",
        "as a structure overview rather than a full call graph.",
        "",
        "```mermaid",
        "flowchart LR",
    ]

    class_members: dict[str, list[str]] = defaultdict(list)
    class_members["entry"] = []
    class_members["tabs"] = []
    class_members["shared"] = []
    class_members["other"] = []
    class_name_for_layer = {
        "Entry points and bootstrap": "entry",
        "GUI tabs": "tabs",
        "GUI bridge, workers, and shared helpers": "shared",
        "Other internal modules": "other",
    }

    for layer_name in LAYER_ORDER:
        modules_in_layer = layer_to_modules.get(layer_name, [])
        if not modules_in_layer:
            continue
        lines.append(f'  subgraph {mermaid_node_id(layer_name)}["{layer_name}"]')
        for module_name in modules_in_layer:
            node_id = mermaid_node_id(module_name)
            lines.append(f'    {node_id}["{module_name}"]')
            class_members[class_name_for_layer[layer_name]].append(node_id)
        lines.append("  end")

    for module_name in sorted(dependencies):
        source_id = mermaid_node_id(module_name)
        for dependency in sorted(dependencies[module_name]):
            target_id = mermaid_node_id(dependency)
            lines.append(f"  {source_id} --> {target_id}")

    lines.extend(
        [
            "  classDef entry fill:#e7f0ff,stroke:#3a66b3,color:#1d2b45;",
            "  classDef tabs fill:#fff2df,stroke:#b06a00,color:#4d3200;",
            "  classDef shared fill:#e8f8ee,stroke:#2a7f45,color:#153523;",
            "  classDef other fill:#f2f2f2,stroke:#777777,color:#333333;",
        ]
    )

    for class_name, node_ids in class_members.items():
        if node_ids:
            lines.append(f"  class {','.join(node_ids)} {class_name};")

    lines.extend(
        [
            "```",
            "",
            "## Regeneration",
            "",
            "Run:",
            "",
            "```bash",
            "./.venv/bin/python tools/generate_dependency_diagram.py",
            "```",
            "",
            "## Notes",
            "",
            (
                "- The diagram is generated from import statements, so it shows module coupling "
                "rather than runtime call flow."
            ),
            "- External dependencies are intentionally omitted.",
            "- The layer grouping is curated for readability; edges within and across layers remain generated.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Write the generated dependency diagram to the tracked markdown file."""

    OUTPUT_PATH.write_text(generate_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
