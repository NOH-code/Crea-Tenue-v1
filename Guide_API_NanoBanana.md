# Guide complet : Implémenter l'API Nano Banana de Google pour la génération d'images

## Introduction

Ce guide explique comment intégrer l'API Nano Banana de Google dans votre application pour générer des images à partir de descriptions textuelles.

## Prérequis

- Un compte Google Cloud Platform (GCP)
- Node.js installé (version 14+)
- Connaissances de base en JavaScript/TypeScript
- Un projet configuré sur GCP

## Étape 1 : Configuration de Google Cloud Platform

### 1.1 Créer un projet GCP

1. Accédez à [Google Cloud Console](https://console.cloud.google.com)
2. Cliquez sur "Nouveau projet"
3. Nommez votre projet et créez-le

### 1.2 Activer l'API

1. Dans le menu de navigation, allez dans "APIs & Services" > "Bibliothèque"
2. Recherchez "Vertex AI API"
3. Cliquez sur "Activer"

### 1.3 Créer des identifiants

1. Allez dans "APIs & Services" > "Identifiants"
2. Cliquez sur "Créer des identifiants" > "Clé de compte de service"
3. Créez un compte de service avec le rôle "Vertex AI User"
4. Téléchargez le fichier JSON de la clé

## Étape 2 : Installation des dépendances

```bash
npm install @google-cloud/aiplatform
npm install dotenv
```

## Étape 3 : Configuration de l'environnement

Créez un fichier `.env` à la racine de votre projet :

```
GOOGLE_APPLICATION_CREDENTIALS=./chemin-vers-votre-cle.json
PROJECT_ID=votre-project-id
LOCATION=us-central1
```

## Étape 4 : Implémentation de base

### 4.1 Configuration du client

```javascript
require("dotenv").config();
const aiplatform = require("@google-cloud/aiplatform");
const { PredictionServiceClient } = aiplatform.v1;
const { helpers } = aiplatform;

// Configuration
const clientOptions = {
  apiEndpoint: "us-central1-aiplatform.googleapis.com",
};

const predictionServiceClient = new PredictionServiceClient(clientOptions);
const projectId = process.env.PROJECT_ID;
const location = process.env.LOCATION;
const model = "imagegeneration@006"; // Modelo Imagen
```

### 4.2 Fonction de génération d'images

```javascript
async function generateImage(prompt, numberOfImages = 1) {
  try {
    const endpoint = `projects/${projectId}/locations/${location}/publishers/google/models/${model}`;

    const parameters = helpers.toValue({
      sampleCount: numberOfImages,
      aspectRatio: "1:1", // Options: 1:1, 16:9, 9:16, 4:3, 3:4
      negativePrompt: "blurry, low quality", // Ce qu'on ne veut pas
      safetyFilterLevel: "block_some", // Options: block_few, block_some, block_most
      personGeneration: "allow_adult", // Options: dont_allow, allow_adult, allow_all
    });

    const promptObj = helpers.toValue({
      prompt: prompt,
    });

    const instances = [promptObj];

    const request = {
      endpoint,
      instances,
      parameters,
    };

    const [response] = await predictionServiceClient.predict(request);

    return response.predictions.map((prediction) => {
      const predictionValue = helpers.fromValue(prediction);
      return {
        bytesBase64Encoded: predictionValue.bytesBase64Encoded,
        mimeType: predictionValue.mimeType || "image/png",
      };
    });
  } catch (error) {
    console.error("Erreur lors de la génération:", error);
    throw error;
  }
}
```

### 4.3 Sauvegarder les images

```javascript
const fs = require("fs").promises;
const path = require("path");

async function saveImage(base64Image, outputPath) {
  const buffer = Buffer.from(base64Image, "base64");
  await fs.writeFile(outputPath, buffer);
  console.log(`Image sauvegardée : ${outputPath}`);
}

async function generateAndSave(prompt, outputDirectory = "./generated_images") {
  // Créer le dossier si nécessaire
  await fs.mkdir(outputDirectory, { recursive: true });

  const images = await generateImage(prompt, 2);

  for (let i = 0; i < images.length; i++) {
    const filename = `image_${Date.now()}_${i}.png`;
    const filepath = path.join(outputDirectory, filename);
    await saveImage(images[i].bytesBase64Encoded, filepath);
  }
}
```

## Étape 5 : Utilisation avancée

### 5.1 Paramètres personnalisés

```javascript
const advancedParameters = {
  sampleCount: 4,
  aspectRatio: "16:9",
  negativePrompt: "blurry, distorted, ugly, bad anatomy",
  seed: 12345, // Pour des résultats reproductibles
  guidanceScale: 7.5, // Contrôle l'adhésion au prompt (0-20)
  safetyFilterLevel: "block_some",
  personGeneration: "allow_adult",
  addWatermark: false,
};
```

### 5.2 Gestion des erreurs robuste

```javascript
async function generateImageSafely(prompt, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await generateImage(prompt);
    } catch (error) {
      if (error.code === 8) {
        // RESOURCE_EXHAUSTED
        console.log(`Quota dépassé, attente avant nouvelle tentative...`);
        await new Promise((resolve) => setTimeout(resolve, 2000 * (i + 1)));
      } else if (i === retries - 1) {
        throw error;
      }
    }
  }
}
```

## Étape 6 : Intégration dans une API Express

```javascript
const express = require("express");
const app = express();

app.use(express.json());

app.post("/api/generate-image", async (req, res) => {
  try {
    const { prompt, numberOfImages = 1 } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: "Le prompt est requis" });
    }

    const images = await generateImage(prompt, numberOfImages);

    res.json({
      success: true,
      images: images.map((img) => ({
        data: img.bytesBase64Encoded,
        mimeType: img.mimeType,
      })),
    });
  } catch (error) {
    console.error("Erreur:", error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.listen(3000, () => {
  console.log("Serveur démarré sur le port 3000");
});
```

## Étape 7 : Frontend (exemple React)

```javascript
import React, { useState } from "react";

function ImageGenerator() {
  const [prompt, setPrompt] = useState("");
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);

  const generateImages = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, numberOfImages: 2 }),
      });

      const data = await response.json();

      if (data.success) {
        setImages(data.images);
      }
    } catch (error) {
      console.error("Erreur:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Décrivez l'image à générer..."
      />
      <button onClick={generateImages} disabled={loading}>
        {loading ? "Génération..." : "Générer"}
      </button>

      <div className="images-grid">
        {images.map((img, index) => (
          <img
            key={index}
            src={`data:${img.mimeType};base64,${img.data}`}
            alt={`Généré ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

export default ImageGenerator;
```

## Bonnes pratiques

### Optimisation des prompts

- Soyez spécifique et descriptif
- Incluez le style artistique souhaité
- Mentionnez les couleurs, l'éclairage, la composition
- Utilisez des virgules pour séparer les concepts

Exemple de bon prompt :

```
"Un chat cyberpunk avec des yeux néon, style digital art,
éclairage dramatique, couleurs vibrantes, haute qualité, 8k"
```

### Gestion des coûts

- Mettez en cache les résultats fréquents
- Limitez le nombre de générations par utilisateur
- Utilisez un système de files d'attente pour les requêtes massives

### Sécurité

- Validez et nettoyez les prompts utilisateurs
- Implémentez des filtres de contenu inapproprié
- Limitez la taille des requêtes
- Utilisez des variables d'environnement pour les credentials

## Limites et quotas

- Consultez les limites de quota dans la console GCP
- Par défaut : 60 requêtes par minute
- Taille maximale des images : dépend du modèle
- Coût par image généré : vérifiez la tarification actuelle

## Dépannage

### Erreur d'authentification

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/chemin/vers/cle.json"
```

### Erreur de quota dépassé

- Augmentez vos quotas dans GCP Console
- Implémentez un système de retry avec backoff exponentiel

### Images de mauvaise qualité

- Améliorez vos prompts
- Ajustez le guidanceScale
- Utilisez des negative prompts plus détaillés

## Ressources

- [Documentation Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Tarification](https://cloud.google.com/vertex-ai/pricing)
- [Guide des modèles Imagen](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)

## Conclusion

Vous disposez maintenant d'une implémentation complète pour générer des images avec l'API Google. N'hésitez pas à personnaliser et adapter ce code à vos besoins spécifiques.
