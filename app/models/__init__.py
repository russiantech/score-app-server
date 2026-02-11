# v5
"""
This module provides dynamic auto-discovery and import of all SQLAlchemy model classes
within the 'app/models' directory. It supports both dynamic and explicit imports for
IDE autocompletion, Alembic migrations, and static analysis tools.
Key Features:
- Automatically discovers all model modules and their SQLAlchemy declarative classes.
- Populates the module's __all__ with discovered model class names for clean exports.
- Provides convenience functions to retrieve all model classes or a specific model by name.
- Supports explicit imports for commonly used models to enhance IDE support.
- Handles import errors gracefully, allowing partial model loading if dependencies are missing.
- Skips private, special, or unwanted files and directories during discovery.
- Maintains backward compatibility with explicit imports and supports lazy attribute access.
Note:
The comment '# noqa: F401' is used to tell linters (such as flake8) to ignore warning F401,
which indicates that a module is imported but unused. This is useful when an import is
performed for its side effects (such as registering models) rather than direct usage.
# app/models/__init__.py



Dynamic model auto-loader with explicit exports.

This module automatically discovers and imports all SQLAlchemy models
while maintaining clean exports for IDE support and Alembic compatibility.

"""

import importlib
import os
from typing import List

import logging
logger = logging.getLogger(__name__)

BASE_DIR = "app/models"
BASE_MODULE = "app.models"

# Public API - models available for import
__all__: List[str] = []

# Internal registry of imported model classes
_MODEL_CLASSES = {}


def is_skipped_file(filename: str) -> bool:
    """
    Determine whether the file should be skipped.
    Rules:
      - Skip __init__.py
      - Skip non-.py files
      - Skip any file containing '_0' before the .py extension
      - Skip files starting with underscore (private modules)
    """
    if filename == "__init__.py":
        return True

    if not filename.endswith(".py"):
        return True

    if filename.startswith("_"):
        return True

    name_without_ext = filename[:-3]  # remove .py

    # Skip any file containing '_0' anywhere before `.py`
    if "_0" in name_without_ext:
        return True

    return False


def get_model_classes_from_module(module) -> List[str]:
    """Extract SQLAlchemy model class names from a module."""
    model_classes = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        
        # Check if it's a SQLAlchemy declarative class
        try:
            # This is a common pattern to identify SQLAlchemy models
            if hasattr(attr, '__table__') and hasattr(attr, '__tablename__'):
                model_classes.append(attr_name)
        except Exception:
            continue
    
    return model_classes


def auto_discover_models():
    """
    Automatically discover and import all model modules.
    Returns a dictionary mapping model names to their classes.
    """
    discovered_models = {}
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Filter to valid module files
        module_files = [f for f in files if not is_skipped_file(f)]
        if not module_files:
            continue

        # Compute module path from directory structure
        relative_path = os.path.relpath(root, BASE_DIR)
        
        if relative_path == ".":
            module_base = BASE_MODULE
        else:
            module_base = f"{BASE_MODULE}.{relative_path.replace(os.sep, '.')}"

        # Import each valid module and collect model classes
        for file_name in module_files:
            module_name = file_name[:-3]  # remove ".py"
            full_module_path = f"{module_base}.{module_name}"
            
            try:
                module = importlib.import_module(full_module_path)
                
                # Find model classes in this module
                model_classes = get_model_classes_from_module(module)
                
                for class_name in model_classes:
                    discovered_models[class_name] = getattr(module, class_name)
                    __all__.append(class_name)
                    
            except ImportError as e:
                # Log but don't crash - some models might have dependencies
                # that are resolved after all imports
                logger.warning(f"Warning: Could not import {full_module_path}: {e}")
                continue
    
    return discovered_models


def auto_discover_models():
    """
    Automatically discover and import all model modules.
    Returns a dictionary mapping model names to their classes.
    """
    discovered_models = {}

    for root, dirs, files in os.walk(BASE_DIR):
        #  SKIP directories named "_" or starting with "_"
        dirs[:] = [
            d for d in dirs
            if not d.startswith("_") and d != "_"
        ]

        # Filter valid module files
        module_files = [f for f in files if not is_skipped_file(f)]
        if not module_files:
            continue

        # Compute module path
        relative_path = os.path.relpath(root, BASE_DIR)

        if relative_path == ".":
            module_base = BASE_MODULE
        else:
            module_base = f"{BASE_MODULE}.{relative_path.replace(os.sep, '.')}"

        for file_name in module_files:
            module_name = file_name[:-3]
            full_module_path = f"{module_base}.{module_name}"

            try:
                module = importlib.import_module(full_module_path)

                model_classes = get_model_classes_from_module(module)
                for class_name in model_classes:
                    discovered_models[class_name] = getattr(module, class_name)
                    if class_name not in __all__:
                        __all__.append(class_name)

            except Exception as e:
                print(f"Warning: Could not import {full_module_path}: {e}")

    return discovered_models

# Execute auto-discovery
_MODEL_CLASSES = auto_discover_models()


# Convenience function for Alembic and other tools
def get_all_model_classes():
    """Return all discovered model classes."""
    return list(_MODEL_CLASSES.values())


def get_model_class_by_name(name: str):
    """Get a model class by its name."""
    return _MODEL_CLASSES.get(name)


# Optional: Create a function that can be called explicitly
def import_all_models():
    """Explicitly import all model modules (for Alembic compatibility)."""
    # This function is now idempotent - models are already loaded
    return get_all_model_classes()


# Convenience imports for common models (optional but recommended)
# This provides IDE autocompletion and static analysis
# try:
#     from .user import User
#     from .course import Course
#     from .lesson import Lesson
#     from .enrollment import Enrollment
#     from .score import Score
#     from .attendance import Attendance
#     from .certificate import Certificate
#     from .review import Review
    
#     from .products import (
#         Product, ProductAttribute, ProductVariant
#     )
#     from .payments import (
#         Payment, Subscription, Plan,
#         PaymentModes
#     )

#     # Add other commonly used models here
        
#     from .address import (
#         Address,
#         City,
#         State,
#         Country,
#     )
    
#     from .orders import Order, OrderItem
    

#     # Add other commonly used models here
    
#     # Update __all__ to include these explicit imports
#     # Remove duplicates if any
#     for model in [
#         User, Course, Lesson, 
#         Enrollment, Score, Attendance, Certificate, 
#         Review, Address, City, State, Country,
#         Order, OrderItem,
#         Payment, Subscription, Plan, PaymentModes,
#         Product, ProductAttribute, ProductVariant,
#     ]:
#         if model.__name__ not in __all__:
#             logger.warning(f"Adding {model.__name__} to __all__")
#             __all__.append(model.__name__)
            
# except ImportError:
#     # Models will be loaded dynamically anyway
#     pass


# For backward compatibility with explicit imports
# You can add this if you want explicit imports to work
def __getattr__(name):
    """Support lazy imports via attribute access."""
    if name in _MODEL_CLASSES:
        return _MODEL_CLASSES[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Make the module importable as a callable
# Usage: from app.models import import_all_models
import_all_models = import_all_models

