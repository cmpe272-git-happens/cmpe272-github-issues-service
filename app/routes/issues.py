from fastapi import APIRouter

router = APIRouter(prefix="/issues", tags=["Issues"])

router = APIRouter(prefix="/issues", tags=["Issues"])

@router.get("")
async def list_issues():
    ...

@router.post("")
async def create_issue():
    ...

@router.get("/{issue_number}")
async def get_issue(issue_number: int):
    ...

@router.patch("/{issue_number}")
async def update_issue(issue_number: int):
    ...

@router.delete("/{issue_number}")
async def close_issue(issue_number: int):
    ...
    