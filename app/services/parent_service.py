from sqlalchemy import desc, asc, or_, func, distinct
from sqlalchemy.orm import Session, joinedload, aliased
from typing import Optional
from uuid import UUID

from app.models.parents import ParentChildren
from app.models.user import User
from app.models.rbac import Role
from app.schemas.parent import (
    LinkStatus,
    ParentChildCreate,
    ParentChildFilters,
    ParentChildUpdate,
    RelationshipType,
)

# def get_links_query1(
#     db: Session,
#     filters: Optional[ParentChildFilters] = None,
# ):
#     parent = aliased(User)
#     student = aliased(User)

#     query = (
#         db.query(ParentChildren)
#         .join(parent, ParentChildren.parent_id == parent.id)
#         .join(student, ParentChildren.child_id == student.id)
#         .options(
#             joinedload(ParentChildren.parent),
#             joinedload(ParentChildren.child),
#         )
#     )

#     if not filters:
#         return query.order_by(desc(ParentChildren.created_at))

#     if filters.search:
#         search = f"%{filters.search.lower()}%"
#         query = query.filter(
#             or_(
#                 parent.names.ilike(search),
#                 parent.email.ilike(search),
#                 student.names.ilike(search),
#                 student.email.ilike(search),
#             )
#         )

#     if filters.status:
#         query = query.filter(
#             ParentChildren.status == LinkStatus(filters.status)
#         )

#     if filters.parent_id:
#         query = query.filter(ParentChildren.parent_id == filters.parent_id)

#     if filters.child_id:
#         query = query.filter(ParentChildren.child_id == filters.child_id)

#     if filters.relationship_type:
#         query = query.filter(
#             ParentChildren.relationship_type
#             == RelationshipType(filters.relationship_type)
#         )

#     sort_column = getattr(
#         ParentChildren, filters.sort_by, ParentChildren.created_at
#     )

#     query = (
#         query.order_by(desc(sort_column))
#         if filters.order == "desc"
#         else query.order_by(asc(sort_column))
#     )

#     return query


def get_links_query(
    db: Session,
    filters: Optional[ParentChildFilters] = None,
):
    """Build filtered and sorted ParentChildren query"""

    Parent = aliased(User)
    Child = aliased(User)

    query = (
        db.query(ParentChildren)
        .join(Parent, ParentChildren.parent)
        .join(Child, ParentChildren.child)
        .options(
            joinedload(ParentChildren.parent),
            joinedload(ParentChildren.child),
        )
    )

    if not filters:
        return query.order_by(desc(ParentChildren.created_at))

    # Search (parent OR child / student)
    if filters.search:
        term = f"%{filters.search}%"
        query = query.filter(
            or_(
                Parent.names.ilike(term),
                Parent.email.ilike(term),
                Child.names.ilike(term),
                Child.email.ilike(term),
            )
        )

    if filters.status:
        query = query.filter(ParentChildren.status == filters.status)

    if filters.parent_id:
        query = query.filter(ParentChildren.parent_id == filters.parent_id)

    if filters.child_id:
        query = query.filter(ParentChildren.child_id == filters.child_id)

    if filters.relationship_type:
        query = query.filter(
            ParentChildren.relationship_type == filters.relationship_type
        )

    sort_column = getattr(
        ParentChildren,
        filters.sort_by,
        ParentChildren.created_at,
    )

    order_fn = desc if filters.order == "desc" else asc
    return query.order_by(order_fn(sort_column))


def list_links(
    db: Session,
    filters: Optional[ParentChildFilters] = None,
):
    return get_links_query(db, filters).all()


def create_link(
    db: Session,
    link_data: ParentChildCreate,
    linked_by_id: Optional[UUID] = None,
) -> ParentChildren:

    exists = (
        db.query(ParentChildren)
        .filter(
            ParentChildren.parent_id == link_data.parent_id,
            ParentChildren.child_id == link_data.child_id,
        )
        .first()
    )

    if exists:
        raise ValueError("Parent-child link already exists")

    parent = (
        db.query(User)
        .filter(
            User.id == link_data.parent_id,
            User.roles.any(Role.name == "parent"),
        )
        .first()
    )

    student = (
        db.query(User)
        .filter(
            User.id == link_data.child_id,
            User.roles.any(Role.name == "student"),
        )
        .first()
    )

    if not parent or not student:
        raise ValueError("Invalid parent or student user")

    link = ParentChildren(
        parent_id=link_data.parent_id,
        child_id=link_data.child_id,
        relationship_type=RelationshipType(link_data.relationship_type),
        is_primary=link_data.is_primary,
        notes=link_data.notes,
        linked_by=linked_by_id,
        status=LinkStatus.ACTIVE,
    )

    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def update_link(
    db: Session,
    link_id: UUID,
    update_data: ParentChildUpdate,
) -> ParentChildren:

    link = db.query(ParentChildren).filter_by(id=link_id).first()

    if not link:
        raise ValueError("Link not found")

    if update_data.relationship_type:
        link.relationship_type = RelationshipType(update_data.relationship_type)

    if update_data.is_primary is not None:
        link.is_primary = update_data.is_primary

    if update_data.notes is not None:
        link.notes = update_data.notes

    if update_data.status:
        link.status = LinkStatus(update_data.status)

    db.commit()
    db.refresh(link)
    return link

def delete_link(db: Session, link_id: UUID) -> None:
    link = db.get(ParentChildren, link_id)
    if not link:
        raise ValueError("Link not found")

    db.delete(link)
    db.commit()

def get_stats(db: Session) -> dict:
    total_links = db.query(func.count(ParentChildren.id)).scalar() or 0

    active_links = (
        db.query(func.count(ParentChildren.id))
        .filter(ParentChildren.status == LinkStatus.ACTIVE)
        .scalar()
        or 0
    )

    parents_linked = (
        db.query(func.count(distinct(ParentChildren.parent_id)))
        .filter(ParentChildren.status == LinkStatus.ACTIVE)
        .scalar()
        or 0
    )

    total_parents = (
        db.query(User)
        .filter(
            User.roles.any(Role.name == "parent"),
            User.is_active.is_(True),
        )
        .count()
    )

    children_linked = (
        db.query(func.count(distinct(ParentChildren.child_id)))
        .filter(ParentChildren.status == LinkStatus.ACTIVE)
        .scalar()
        or 0
    )

    total_students = (
        db.query(User)
        .filter(User.roles.any(Role.name == "student"))
        .count()
    )

    return {
        "total_links": total_links,
        "active_links": active_links,
        "inactive_links": total_links - active_links,
        "parents_linked": parents_linked,
        "total_parents": total_parents,
        "parents_unlinked": total_parents - parents_linked,
        "children_linked": children_linked,
        "total_students": total_students,
        "children_unlinked": total_students - children_linked,
    }

