from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.domain_policy import DomainPolicyCreate, DomainPolicyRead, DomainPolicyUpdate
from app.services.domain_policy import domain_policy_service

router = APIRouter()


@router.get("/", response_model=list[DomainPolicyRead])
async def list_domain_policies(db: AsyncSession = Depends(get_db)) -> list[DomainPolicyRead]:
    policies = await domain_policy_service.list(db)
    return [DomainPolicyRead.model_validate(p) for p in policies]


@router.post("/", response_model=DomainPolicyRead, status_code=status.HTTP_201_CREATED)
async def create_domain_policy(payload: DomainPolicyCreate, db: AsyncSession = Depends(get_db)) -> DomainPolicyRead:
    existing = await domain_policy_service.get_by_domain(db, payload.domain)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Policy for this domain already exists")
    policy = await domain_policy_service.create(db, domain=payload.domain, enabled=payload.enabled, config=payload.config)
    return DomainPolicyRead.model_validate(policy)


@router.get("/{policy_id}", response_model=DomainPolicyRead)
async def get_domain_policy(policy_id: str, db: AsyncSession = Depends(get_db)) -> DomainPolicyRead:
    policy = await domain_policy_service.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain policy not found")
    return DomainPolicyRead.model_validate(policy)


@router.patch("/{policy_id}", response_model=DomainPolicyRead)
async def update_domain_policy(
    policy_id: str, payload: DomainPolicyUpdate, db: AsyncSession = Depends(get_db)
) -> DomainPolicyRead:
    policy = await domain_policy_service.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain policy not found")
    updated = await domain_policy_service.update(db, policy, enabled=payload.enabled, config=payload.config)
    return DomainPolicyRead.model_validate(updated)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain_policy(policy_id: str, db: AsyncSession = Depends(get_db)) -> None:
    policy = await domain_policy_service.get(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain policy not found")
    await db.delete(policy)
    await db.commit()
    return None
