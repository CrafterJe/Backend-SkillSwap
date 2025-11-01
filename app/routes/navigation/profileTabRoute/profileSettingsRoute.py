# routes/navigation/profileTab/profileSettingsRoute.py
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth_guardUtils import auth_required_depends
from app.utils.securityUtils import hash_password, verify_password
from app.database import user_collection
from app.schemas.navigation.profileTabSchema.profileSettingsSchema import *
from app.schemas.authSchema import PREDEFINED_SKILLS
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/navigation/profileTab/profileSettings", tags=["Navigation - Profile"])

@router.get("/predefined-skills", response_model=PredefinedSkillsResponse)
async def get_predefined_skills():
    """Obtener lista de habilidades predefinidas para el frontend"""
    return {
        "skills": PREDEFINED_SKILLS,
        "message": "Lista de habilidades disponibles"
    }

@router.get("", response_model=UserProfile)
async def get_profile(user_id: str = Depends(auth_required_depends)):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": user.get("phone"),
        "birth_date": (
            user["birth_date"].strftime("%Y-%m-%d")
            if isinstance(user["birth_date"], datetime)
            else user["birth_date"]
        ),
        "location": user.get("location"),
        "interests_offered": user.get("interests_offered", []),
        "interests_wanted": user.get("interests_wanted", []),
        "allow_be_added": user.get("allow_be_added", True),
        "about_me": user.get("about_me"),
        "profile_image": user.get("profile_image"),
    }


@router.put("")
async def update_profile(payload: UpdateUserProfile, user_id: str = Depends(auth_required_depends)):
    update_data = payload.dict(exclude_unset=True)

    # Convertir birth_date a datetime si viene en el payload
    if payload.birth_date:
        try:
            update_data["birth_date"] = datetime.combine(payload.birth_date, datetime.min.time())
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido")

    # Validar habilidades ofrecidas (máximo 10)
    if payload.interests_offered is not None:
        if len(payload.interests_offered) > 10:
            raise HTTPException(
                status_code=400, 
                detail="Máximo 10 habilidades que puedes ofrecer"
            )
        
        for skill in payload.interests_offered:
            if len(skill.strip()) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Cada habilidad debe tener al menos 2 caracteres"
                )

    # Validar habilidades deseadas
    if payload.interests_wanted is not None:
        for skill in payload.interests_wanted:
            if len(skill.strip()) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Cada habilidad debe tener al menos 2 caracteres"
                )

    result = await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No se pudo actualizar el perfil")

    return {"message": "Perfil actualizado correctamente"}

@router.patch("/password")
async def change_password(
    payload: PasswordChange,
    user_id: str = Depends(auth_required_depends)
):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_password(payload.current_password, user["password"]):
        raise HTTPException(status_code=403, detail="La contraseña actual no es correcta")

    new_hashed = hash_password(payload.new_password)

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed}}
    )

    return {"message": "Contraseña actualizada correctamente"}