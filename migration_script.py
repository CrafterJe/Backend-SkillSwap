# migration_script.py
# Script para migrar usuarios de interests string a arrays

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://CrafterJe:Bakugan2y4@computo-nube-5b.mr5lhuh.mongodb.net/SkillSwap?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "SkillSwap")

async def migrate_user_interests():
    """
    Migrar todos los usuarios existentes:
    1. Eliminar campo 'interests' (string)
    2. Agregar 'interests_offered' y 'interests_wanted' como arrays vacíos
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    user_collection = db["users"]
    
    try:
        # Obtener todos los usuarios que tienen el campo 'interests' como string
        users_with_old_interests = await user_collection.find(
            {"interests": {"$exists": True}}
        ).to_list(None)
        
        print(f"📋 Encontrados {len(users_with_old_interests)} usuarios con campo 'interests' string")
        
        if len(users_with_old_interests) == 0:
            print("✅ No hay usuarios que migrar")
            return
        
        # Actualizar todos los usuarios
        result = await user_collection.update_many(
            {"interests": {"$exists": True}},  # Usuarios con campo 'interests'
            {
                "$unset": {"interests": ""},  # Eliminar campo 'interests'
                "$set": {
                    "interests_offered": [],  # Agregar array vacío
                    "interests_wanted": []    # Agregar array vacío
                }
            }
        )
        
        print(f"✅ Migración completada:")
        print(f"   - {result.modified_count} usuarios actualizados")
        print(f"   - Campo 'interests' eliminado")
        print(f"   - Campos 'interests_offered' e 'interests_wanted' agregados como arrays vacíos")
        print(f"   - Los usuarios podrán configurar sus habilidades desde la app")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
    finally:
        client.close()

async def verify_migration():
    """Verificar que la migración se ejecutó correctamente"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    user_collection = db["users"]
    
    try:
        # Contar usuarios con campo 'interests' viejo
        old_count = await user_collection.count_documents({"interests": {"$exists": True}})
        
        # Contar usuarios con nuevos campos
        new_count = await user_collection.count_documents({
            "interests_offered": {"$exists": True},
            "interests_wanted": {"$exists": True}
        })
        
        print(f"📊 Verificación de migración:")
        print(f"   - Usuarios con campo 'interests' viejo: {old_count}")
        print(f"   - Usuarios con nuevos campos de arrays: {new_count}")
        
        if old_count == 0:
            print("✅ Migración exitosa - No quedan campos 'interests' string")
        else:
            print("⚠️  Advertencia - Aún existen campos 'interests' string")
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración de usuarios...")
    
    # Ejecutar migración
    asyncio.run(migrate_user_interests())
    
    print("\n🔍 Verificando migración...")
    
    # Verificar migración
    asyncio.run(verify_migration())
    
    print("\n✅ Proceso completado!")
    print("💡 Los usuarios ahora pueden configurar sus habilidades desde la configuración de la app")