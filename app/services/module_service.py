
# v3
# app/services/module_service.py
"""
Module service with automatic reordering support.
Uses temporary negative orders to avoid unique constraint violations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List

from app.schemas.module import ModuleCreate, ModuleUpdate
from app.models.course import Course
from app.models.modules import Module
from fastapi import HTTPException, status


def create_module(db: Session, data: ModuleCreate) -> Module:
    """
    Create a module for a course with automatic reordering.
    
    If the desired order is already taken, shifts existing modules to make room.
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Handle automatic reordering
    _reorder_modules_on_insert(db, data.course_id, data.order)
    
    # Create the module
    module = Module(**data.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module


def update_module(db: Session, module_id: UUID, data: ModuleUpdate) -> Module:
    """
    Update module with automatic reordering.
    
    If order is changed, automatically shifts other modules.
    """
    module = get_module(db, module_id)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle order change with automatic reordering
    if 'order' in update_data and update_data['order'] != module.order:
        old_order = module.order
        new_order = update_data['order']
        
        _reorder_modules_on_update(
            db, 
            module.course_id, 
            module_id, 
            old_order, 
            new_order
        )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(module, field, value)
    
    db.commit()
    db.refresh(module)
    
    return module


def delete_module(db: Session, module_id: UUID) -> None:
    """
    Delete module and reorder remaining modules.
    
    Fills the gap left by the deleted module.
    """
    module = get_module(db, module_id)
    
    course_id = module.course_id
    deleted_order = module.order
    
    # Delete the module
    db.delete(module)
    db.flush()  # Flush to apply deletion
    
    # Shift modules after the deleted one
    _reorder_modules_on_delete(db, course_id, deleted_order)
    
    db.commit()


def list_course_modules(db: Session, course_id: UUID) -> List[Module]:
    """List all modules for a course ordered by order field."""
    return db.query(Module).filter(
        Module.course_id == course_id
    ).order_by(Module.order).all()


def get_module(db: Session, module_id: UUID) -> Module:
    """Get module by ID."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    return module


def list_course_with_modules(db: Session, course_id: UUID):
    """Get course with all its modules."""
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        return None, []
    
    modules = list_course_modules(db, course_id)
    
    return course, modules


# ============================================================================
# PRIVATE HELPER FUNCTIONS FOR REORDERING
# Uses temporary negative orders to avoid unique constraint violations
# ============================================================================

def _reorder_modules_on_insert(db: Session, course_id: UUID, new_order: int) -> None:
    """
    Shift modules to make room for a new module at the specified order.
    
    Uses temporary negative orders to avoid constraint violations.
    
    Example:
        Existing: [1, 2, 3, 4]
        Insert at order 2
        Step 1: Move 2,3,4 to temp [-2, -3, -4]
        Step 2: Reassign to [3, 4, 5]
        Result: [1, (new=2), 3, 4, 5]
    """
    # Get all modules that need to shift (order >= new_order)
    modules_to_shift = db.query(Module).filter(
        and_(
            Module.course_id == course_id,
            Module.order >= new_order
        )
    ).order_by(Module.order).all()
    
    if not modules_to_shift:
        return
    
    # Step 1: Move to temporary negative orders
    for idx, module in enumerate(modules_to_shift):
        module.order = -(new_order + idx)  # Negative temp value
    
    db.flush()
    
    # Step 2: Move to final positive orders
    for idx, module in enumerate(modules_to_shift):
        module.order = new_order + idx + 1  # Final position (shifted by 1)
    
    db.flush()


def _reorder_modules_on_update(
    db: Session, 
    course_id: UUID, 
    module_id: UUID,
    old_order: int, 
    new_order: int
) -> None:
    """
    Reorder modules when a module's order changes.
    
    Uses temporary negative orders to avoid constraint violations.
    
    Example (moving down):
        Existing: [1, (2*), 3, 4, 5]  (* = module being moved)
        Move order 2 to 4
        Step 1: Move target to temp order -999
        Step 2: Move 3,4 to temp [-3, -4]
        Step 3: Reassign 3,4 to [2, 3]
        Step 4: Move target to final order 4
        Result: [1, 2, 3, (4*), 5]
    """
    if old_order == new_order:
        return
    
    # Get the module being moved
    target_module = db.query(Module).filter(Module.id == module_id).first()
    
    # Step 1: Move target module to temporary position (way out of range)
    target_module.order = -9999
    db.flush()
    
    if new_order < old_order:
        # Moving up: need to shift modules down
        # Get modules between new_order and old_order (exclusive)
        modules_to_shift = db.query(Module).filter(
            and_(
                Module.course_id == course_id,
                Module.id != module_id,
                Module.order >= new_order,
                Module.order < old_order
            )
        ).order_by(Module.order).all()
        
        # Step 2: Move to temporary negative orders
        for idx, module in enumerate(modules_to_shift):
            module.order = -(new_order + idx)
        
        db.flush()
        
        # Step 3: Move to final positions (shifted down by 1)
        for idx, module in enumerate(modules_to_shift):
            module.order = new_order + idx + 1
        
        db.flush()
    
    else:  # new_order > old_order
        # Moving down: need to shift modules up
        # Get modules between old_order and new_order (exclusive)
        modules_to_shift = db.query(Module).filter(
            and_(
                Module.course_id == course_id,
                Module.id != module_id,
                Module.order > old_order,
                Module.order <= new_order
            )
        ).order_by(Module.order).all()
        
        # Step 2: Move to temporary negative orders
        for idx, module in enumerate(modules_to_shift):
            module.order = -(old_order + idx)
        
        db.flush()
        
        # Step 3: Move to final positions (shifted up by 1)
        for idx, module in enumerate(modules_to_shift):
            module.order = old_order + idx
        
        db.flush()
    
    # Step 4: Move target module to its final position
    target_module.order = new_order
    db.flush()


def _reorder_modules_on_delete(db: Session, course_id: UUID, deleted_order: int) -> None:
    """
    Fill the gap when a module is deleted.
    
    Uses temporary negative orders to avoid constraint violations.
    
    Example:
        Existing: [1, 2, (3*), 4, 5]  (* = deleted)
        Step 1: Move 4,5 to temp [-4, -5]
        Step 2: Reassign to [3, 4]
        Result: [1, 2, 3, 4]
    """
    # Get all modules after the deleted one
    modules_to_shift = db.query(Module).filter(
        and_(
            Module.course_id == course_id,
            Module.order > deleted_order
        )
    ).order_by(Module.order).all()
    
    if not modules_to_shift:
        return
    
    # Step 1: Move to temporary negative orders
    for idx, module in enumerate(modules_to_shift):
        module.order = -(deleted_order + idx)
    
    db.flush()
    
    # Step 2: Move to final positions (shifted up by 1)
    for idx, module in enumerate(modules_to_shift):
        module.order = deleted_order + idx
    
    db.flush()


def normalize_module_orders(db: Session, course_id: UUID) -> None:
    """
    Normalize module orders to be sequential (1, 2, 3, ...).
    
    Useful for fixing any gaps or inconsistencies in ordering.
    Uses temporary negative orders to avoid constraint violations.
    """
    modules = db.query(Module).filter(
        Module.course_id == course_id
    ).order_by(Module.order).all()
    
    if not modules:
        return
    
    # Step 1: Move all to temporary negative orders
    for idx, module in enumerate(modules):
        module.order = -(idx + 1)
    
    db.flush()
    
    # Step 2: Move to final sequential positions
    for idx, module in enumerate(modules):
        module.order = idx + 1
    
    db.commit()
    

