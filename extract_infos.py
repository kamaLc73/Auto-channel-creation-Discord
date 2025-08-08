import discord
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

async def extract_categories_to_csv(guild_id: int, filename: str = None):
    """
    Extrait toutes les catégories d'un serveur Discord et les sauvegarde dans un CSV
    
    Args:
        guild_id (int): ID du serveur Discord
        filename (str): Nom du fichier CSV (optionnel)
    """
    try:
        # Récupérer le serveur par son ID
        guild = client.get_guild(guild_id)
        if not guild:
            print(f"❌ Serveur avec l'ID {guild_id} non trouvé!")
            return
        
        print(f"🔍 Extraction des catégories du serveur: {guild.name}")
        
        # Nom du fichier par défaut
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"categories_{guild.name}_{timestamp}.csv"
        
        # Préparer les données
        categories_data = []
        
        for category in guild.categories:
            # Récupérer les informations de la catégorie
            category_info = {
                'id': category.id,
                'name': category.name,
                'position': category.position,
                'created_at': category.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'channels_count': len(category.channels),
                'channels_list': ', '.join([channel.name for channel in category.channels]),
                'is_private': any(overwrite.view_channel is False for target, overwrite in category.overwrites.items() 
                                if target == guild.default_role),
                'roles_with_access': ', '.join([role.name for role, overwrite in category.overwrites.items() 
                                              if isinstance(role, discord.Role) and role != guild.default_role 
                                              and overwrite.view_channel is True]),
                'server_name': guild.name,
                'server_id': guild.id
            }
            categories_data.append(category_info)
        
        # Trier par position
        categories_data.sort(key=lambda x: x['position'])
        
        # Écrire dans le fichier CSV
        if categories_data:
            fieldnames = [
                'id', 'name', 'position', 'created_at', 'channels_count', 
                'channels_list', 'is_private', 'roles_with_access', 'server_name', 'server_id'
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(categories_data)
            
            print(f"✅ {len(categories_data)} catégories extraites et sauvegardées dans '{filename}'")
            
            # Afficher un résumé
            print("\n📊 Résumé:")
            print(f"   • Serveur: {guild.name}")
            print(f"   • Total catégories: {len(categories_data)}")
            print(f"   • Catégories privées: {sum(1 for cat in categories_data if cat['is_private'])}")
            print(f"   • Total canaux: {sum(cat['channels_count'] for cat in categories_data)}")
            
            # Afficher les 5 premières catégories
            print("\n📋 Aperçu des catégories:")
            for i, cat in enumerate(categories_data[:5]):
                privacy = "🔒" if cat['is_private'] else "🌍"
                print(f"   {i+1}. {privacy} {cat['name']} ({cat['channels_count']} canaux)")
            
            if len(categories_data) > 5:
                print(f"   ... et {len(categories_data) - 5} autres")
        
        else:
            print("⚠️ Aucune catégorie trouvée dans ce serveur!")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {str(e)}")

@client.event
async def on_ready():
    print(f'🤖 Bot connecté en tant que {client.user}')
    print("="*50)
    
    # ID du serveur à analyser (remplacez par l'ID de votre serveur)
    GUILD_ID = int(os.getenv("GUILD_ID_3"))  # REMPLACEZ PAR L'ID DE VOTRE SERVEUR
    
    # Vous pouvez aussi spécifier un nom de fichier personnalisé
    # CUSTOM_FILENAME = "mes_categories.csv"
    
    try:
        # Extraire les catégories
        await extract_categories_to_csv(GUILD_ID)
        # Ou avec un nom personnalisé:
        # await extract_categories_to_csv(GUILD_ID, CUSTOM_FILENAME)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    
    finally:
        print("\n🔚 Extraction terminée. Fermeture du bot...")
        await client.close()

# Fonction pour lister tous les serveurs disponibles
async def list_available_servers():
    """Liste tous les serveurs où le bot est présent"""
    print("\n🌍 Serveurs disponibles:")
    print("-" * 60)
    for guild in client.guilds:
        categories_count = len(guild.categories)
        members_count = guild.member_count
        print(f"📁 {guild.name}")
        print(f"   • ID: {guild.id}")
        print(f"   • Catégories: {categories_count}")
        print(f"   • Membres: {members_count}")
        print(f"   • Propriétaire: {guild.owner}")
        print("-" * 60)

# Version interactive pour choisir le serveur
async def interactive_extraction():
    """Version interactive pour choisir le serveur"""
    print("🔍 Mode interactif activé")
    await list_available_servers()
    
    if not client.guilds:
        print("❌ Le bot n'est présent dans aucun serveur!")
        return
    
    try:
        print(f"\n📝 Entrez l'ID du serveur à analyser:")
        print("   (ou tapez 'list' pour voir à nouveau la liste)")
        
        # Dans un vrai script interactif, vous pourriez utiliser input()
        # Pour cet exemple, nous utilisons le premier serveur disponible
        target_guild = client.guilds[0]
        print(f"🎯 Analyse du serveur: {target_guild.name}")
        
        await extract_categories_to_csv(target_guild.id)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

# Fonction principale
async def main():
    """Fonction principale avec différentes options"""
    
    # Option 1: Extraction directe avec ID spécifique
    # await extract_categories_to_csv(123456789012345678)
    
    # Option 2: Mode interactif (liste les serveurs disponibles)
    await interactive_extraction()
    
    # Option 3: Extraire de tous les serveurs
    # for guild in client.guilds:
    #     await extract_categories_to_csv(guild.id, f"categories_{guild.name}.csv")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token du bot non trouvé! Vérifiez votre fichier .env")
    else:
        try:
            # Lancer le bot
            client.run(TOKEN)
        except KeyboardInterrupt:
            print("\n⏹️ Arrêt du script par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur lors du lancement: {str(e)}")