import streamlit as st
import boto3
import json

# --- CONFIGURATION ---
BUCKET_NAME = 'photos-rbc-2026-irlande'
COLLECTION_ID = 'Mariage_2026_Collection'
MAPPING_FILE = 'face_mapping.json'

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition', region_name='eu-west-1')

# --- DESIGN DU SITE ---
st.title("📸 Retrouvez vos photos du RBC !")

# Lien vers l'album global (optionnel)
st.markdown("---")
st.markdown("📂 **Envie de tout voir ?** [Cliquez ici pour accéder à l'album complet de toutes les photos](VOTRE_LIEN_ALBUM_ICI)")
st.markdown("---")

st.write("Prenez un selfie pour que l'IA recherche les photos où vous apparaissez.")

# --- CHARGEMENT DE LA MÉMOIRE ---
try:
    with open(MAPPING_FILE, 'r') as f:
        face_map = json.load(f)
except Exception:
    st.error("Erreur : Impossible de charger le fichier de correspondance des visages.")
    st.stop()

# --- APPAREIL PHOTO ---
picture = st.camera_input("Prenez un selfie")

if picture is not None:
    image_bytes = picture.getvalue()
    
    with st.spinner("Recherche magique en cours parmi les photos... ⏳"):
        try:
            response = rekognition.search_faces_by_image(
                CollectionId=COLLECTION_ID,
                Image={'Bytes': image_bytes},
                FaceMatchThreshold=80
            )
            
            matches = response.get('FaceMatches', [])
            
            if not matches:
                st.warning("Désolé, aucun visage correspondant n'a été trouvé.")
            else:
                photos_trouvees = []
                for match in matches:
                    face_id = match['Face']['FaceId']
                    if face_id in face_map:
                        photos_trouvees.extend(face_map[face_id])
                        
                photos_trouvees = list(set(photos_trouvees))
                
                st.success(f"🎉 Nous avons trouvé {len(photos_trouvees)} photos de vous !")
                
                for photo in photos_trouvees:
                    try:
                        # Téléchargement direct en mémoire pour garantir l'affichage sans carré noir
                        file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=photo)
                        img_bytes = file_obj['Body'].read()
                        
                        # Affichage propre en grand
                        st.image(img_bytes, use_container_width=True)
                        
                        # Bouton de téléchargement natif
                        st.download_button(
                            label=f"📥 Télécharger {photo}",
                            data=img_bytes,
                            file_name=photo,
                            mime="image/jpeg"
                        )
                        st.markdown("---")
                    except Exception as ex:
                        st.write(f"Impossible d'afficher la photo {photo}")
                    
        except Exception as e:
            st.error(f"Erreur : {e}")
