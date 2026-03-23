"""
Utility formatters for safe string operations
"""

from typing import Any, List, Dict


def safe_join(items: Any, separator: str = ", ") -> str:
    """Safely join items into a string, converting to str first"""
    if not items:
        return ""
    
    if isinstance(items, str):
        return items
    
    if isinstance(items, (list, tuple)):
        safe_items = []
        for item in items:
            if isinstance(item, dict):
                safe_items.append(str(item))
            elif isinstance(item, (list, tuple)):
                safe_items.append(str(item))
            else:
                safe_items.append(str(item))
        return separator.join(safe_items)
    
    return str(items)


def safe_format_list(items: Any) -> List[str]:
    """Safely convert items to list of strings"""
    if not items:
        return []
    
    if isinstance(items, str):
        return [items]
    
    if isinstance(items, (list, tuple)):
        return [str(item) for item in items]
    
    return [str(items)]
