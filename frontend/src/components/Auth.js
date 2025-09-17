import React, { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthForm = ({ onAuthSuccess, isDarkMode }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    nom: '',
    email: '',
    password: ''
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleRegister = async () => {
    if (!formData.nom || !formData.email || !formData.password) {
      toast.error("Tous les champs sont obligatoires");
      return;
    }

    if (formData.password.length < 8) {
      toast.error("Le mot de passe doit contenir au moins 8 caractères");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.error("Adresse email invalide");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, formData);
      
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user_data', JSON.stringify(response.data.user));
      
      toast.success("Compte créé avec succès !");
      onAuthSuccess(response.data.user, response.data.access_token);
      
    } catch (error) {
      console.error('Registration error:', error);
      const message = error.response?.data?.detail || 'Erreur lors de la création du compte';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!formData.email || !formData.password) {
      toast.error("Email et mot de passe requis");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });
      
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user_data', JSON.stringify(response.data.user));
      
      toast.success("Connexion réussie !");
      onAuthSuccess(response.data.user, response.data.access_token);
      
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Erreur lors de la connexion';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white p-4">
      <Card className="w-full max-w-md bg-white border-gray-200">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-6">
            <img 
              src="/blandin-delloye-logo-dark.png" 
              alt="Blandin & Delloye" 
              className="h-16 w-auto"
            />
          </div>
        </CardHeader>
        
        <CardContent>
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2 bg-gray-100">
              <TabsTrigger value="login">
                Connexion
              </TabsTrigger>
              <TabsTrigger value="register">
                Inscription
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="login" className="space-y-4 mt-6">
              <div className="space-y-2">
                <Label htmlFor="login-email">
                  Email
                </Label>
                <Input
                  id="login-email"
                  type="email"
                  placeholder="votre.email@exemple.com"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="login-password">
                  Mot de passe
                </Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  disabled={isLoading}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleLogin();
                    }
                  }}
                />
              </div>
              
              <Button 
                onClick={handleLogin}
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? "Connexion..." : "Se connecter"}
              </Button>
            </TabsContent>
            
            <TabsContent value="register" className="space-y-4 mt-6">
              <div className="space-y-2">
                <Label htmlFor="register-name">
                  Nom complet
                </Label>
                <Input
                  id="register-name"
                  type="text"
                  placeholder="Prénom Nom"
                  value={formData.nom}
                  onChange={(e) => handleInputChange('nom', e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="register-email">
                  Email
                </Label>
                <Input
                  id="register-email"
                  type="email"
                  placeholder="votre.email@exemple.com"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="register-password">
                  Mot de passe
                </Label>
                <Input
                  id="register-password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  disabled={isLoading}
                />
                <p className="text-sm text-slate-600">
                  Minimum 8 caractères avec au moins 1 chiffre et 1 lettre
                </p>
              </div>
              
              <Button 
                onClick={handleRegister}
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? "Création..." : "Créer un compte"}
              </Button>
              
              <p className="text-xs text-center text-slate-600">
                Vous aurez droit à 5 générations d'images gratuites
              </p>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuthForm;