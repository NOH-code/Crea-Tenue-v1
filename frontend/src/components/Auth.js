import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { UserPlus, LogIn, Mail } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthDialog = ({ isOpen, onClose, onLogin, isDarkMode }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    titre: 'Monsieur',
    email: '',
    password: '',
    date_evenement: '',
    accept_communications: false
  });

  const handleInputChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        onLogin(response.data.user, response.data.access_token);
        toast.success('Connexion réussie !');
        onClose();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur de connexion');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Validate required fields
      if (!formData.nom || !formData.prenom || !formData.email || !formData.password) {
        toast.error('Veuillez remplir tous les champs obligatoires');
        return;
      }

      if (!formData.accept_communications) {
        toast.error('Vous devez accepter les communications pour continuer');
        return;
      }

      const response = await axios.post(`${API}/auth/register`, formData);

      if (response.data.success) {
        toast.success('Compte créé ! Vérifiez votre email pour activer votre compte.');
        setIsLogin(true);
        setFormData({
          nom: '',
          prenom: '',
          titre: 'Monsieur',
          email: '',
          password: '',
          date_evenement: '',
          accept_communications: false
        });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création du compte');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={`sm:max-w-md ${isDarkMode ? 'bg-slate-800 text-white border-white' : ''}`}>
        <DialogHeader>
          <DialogTitle className={isDarkMode ? 'text-white' : ''}>
            {isLogin ? 'Connexion' : 'Créer un compte'}
          </DialogTitle>
          <DialogDescription className={isDarkMode ? 'text-white' : ''}>
            {isLogin 
              ? 'Connectez-vous à votre compte TailorView'
              : 'Créez votre compte pour accéder aux services TailorView'
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={isLogin ? handleLogin : handleRegister} className="space-y-4">
          {!isLogin && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className={isDarkMode ? 'text-white' : ''}>Titre *</Label>
                  <Select 
                    value={formData.titre} 
                    onValueChange={(value) => handleInputChange('titre', value)}
                  >
                    <SelectTrigger className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Monsieur">Monsieur</SelectItem>
                      <SelectItem value="Madame">Madame</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className={isDarkMode ? 'text-white' : ''}>Nom *</Label>
                  <Input
                    value={formData.nom}
                    onChange={(e) => handleInputChange('nom', e.target.value)}
                    className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
                    required
                  />
                </div>
                <div>
                  <Label className={isDarkMode ? 'text-white' : ''}>Prénom *</Label>
                  <Input
                    value={formData.prenom}
                    onChange={(e) => handleInputChange('prenom', e.target.value)}
                    className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
                    required
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <Label className={isDarkMode ? 'text-white' : ''}>Email *</Label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
              required
            />
          </div>

          <div>
            <Label className={isDarkMode ? 'text-white' : ''}>Mot de passe *</Label>
            <Input
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
              placeholder={isLogin ? '' : 'Min 8 caractères, 1 chiffre et 1 lettre'}
              required
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <Label className={isDarkMode ? 'text-white' : ''}>Date de l'événement (optionnel)</Label>
                <Input
                  type="date"
                  value={formData.date_evenement}
                  onChange={(e) => handleInputChange('date_evenement', e.target.value)}
                  className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="accept_communications"
                  checked={formData.accept_communications}
                  onCheckedChange={(checked) => handleInputChange('accept_communications', checked)}
                />
                <Label htmlFor="accept_communications" className={`text-sm ${isDarkMode ? 'text-white' : ''}`}>
                  J'accepte de recevoir des communications de votre part *
                </Label>
              </div>
            </>
          )}

          <div className="space-y-2">
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer le compte')}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsLogin(!isLogin)}
              className={`w-full ${isDarkMode ? 'text-white hover:bg-slate-700' : ''}`}
            >
              {isLogin ? 'Créer un compte' : 'Déjà un compte ? Se connecter'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const UserProfile = ({ user, onLogout, isDarkMode }) => {
  return (
    <div className={`p-4 border-b ${isDarkMode ? 'border-white' : 'border-slate-200'}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`font-medium ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>
            {user.titre} {user.prenom} {user.nom}
          </p>
          <p className={`text-sm ${isDarkMode ? 'text-white' : 'text-slate-600'}`}>
            {user.email} • {user.role}
          </p>
          {user.role === 'client' && (
            <p className={`text-xs ${isDarkMode ? 'text-white' : 'text-slate-500'}`}>
              Images: {user.images_used_total}/{user.images_limit_total} • 
              Aujourd'hui: {user.images_used_today}/3
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onLogout}>
          Déconnexion
        </Button>
      </div>
    </div>
  );
};