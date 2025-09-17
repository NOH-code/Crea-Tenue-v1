import React, { useState, useEffect } from "react";
import "./App.css";
import { Upload, Camera, Palette, Send, Download, Mail, Sparkles, Crown, Star, Settings, Users, BarChart3, Trash2, Eye, FileDown, Moon, Sun, LogOut } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { Progress } from "./components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { toast, Toaster } from "sonner";
import axios from "axios";
import * as XLSX from 'xlsx';
import AuthForm from "./components/Auth";
import UserManagementTab from "./components/UserManagementTab";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  // Authentication state
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // UI state
  const [currentView, setCurrentView] = useState('generator'); // 'generator' or 'admin'
  const [adminTab, setAdminTab] = useState('dashboard'); // 'dashboard', 'emailing', or 'users'
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Generator state
  const [generatedImages, setGeneratedImages] = useState([]);
  const [selectedImages, setSelectedImages] = useState([]);
  const [options, setOptions] = useState({});
  const [formData, setFormData] = useState({
    atmosphere: 'champetre',
    suit_type: 'Costume 2 pièces',
    lapel_type: 'Revers cran droit standard',
    pocket_type: 'En biais, sans rabat',
    shoe_type: 'Mocassins noirs',
    accessory_type: 'Cravate',
    fabric_description: '',
    custom_shoe_description: '',
    custom_accessory_description: '',
    email: ''
  });
  const [files, setFiles] = useState({
    model_image: null,
    fabric_image: null,
    shoe_image: null,
    accessory_image: null
  });
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Admin state
  const [adminRequests, setAdminRequests] = useState([]);
  const [adminStats, setAdminStats] = useState({});
  
  // User's own requests state  
  const [myRequests, setMyRequests] = useState([]);
  
  // Email template state
  const [emailTemplate, setEmailTemplate] = useState({
    subject: 'Votre Visualisation de Tenue de Marié Personnalisée',
    body: `Cher Client,

Merci d'avoir utilisé notre service de visualisation de tenue de marié !

Veuillez trouver vos visualisations de tenue générées en pièce jointe.

Cordialement,
L'équipe Blandin & Delloye`
  });

  // Check for saved authentication on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user_data');
    
    if (savedToken && savedUser) {
      try {
        const userdata = JSON.parse(savedUser);
        setAccessToken(savedToken);
        setUser(userdata);
        setIsAuthenticated(true);
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
      }
    }

    // Setup axios interceptor for automatic logout on auth errors
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 || error.response?.status === 403) {
          // Token expired or invalid - auto logout
          if (isAuthenticated) {
            toast.error("Session expirée. Reconnexion nécessaire.");
            handleLogout();
          }
        }
        return Promise.reject(error);
      }
    );

    // Cleanup interceptor on unmount
    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [isAuthenticated]);

  // Fetch options on authentication
  useEffect(() => {
    if (isAuthenticated) {
      fetchOptions();
      
      // Set up periodic token validation
      const tokenCheckInterval = setInterval(async () => {
        try {
          await axios.get(`${API}/auth/me`);
        } catch (error) {
          if (error.response?.status === 401 || error.response?.status === 403) {
            console.log('Token expired, logging out...');
            handleLogout();
          }
        }
      }, 5 * 60 * 1000); // Check every 5 minutes

      return () => clearInterval(tokenCheckInterval);
    }
  }, [isAuthenticated]);

  const handleAuthSuccess = (userData, token) => {
    setUser(userData);
    setAccessToken(token);
    setIsAuthenticated(true);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    fetchOptions();
  };

  const handleLogout = () => {
    setUser(null);
    setAccessToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    delete axios.defaults.headers.common['Authorization'];
    toast.success("Déconnecté avec succès");
  };

  const fetchOptions = async () => {
    try {
      const response = await axios.get(`${API}/options`);
      setOptions(response.data);
    } catch (error) {
      console.error('Error fetching options:', error);
      toast.error("Erreur lors du chargement des options");
    }
  };

  const fetchAdminData = async () => {
    if (user.role !== 'admin') return;
    
    try {
      const [requestsResponse, statsResponse] = await Promise.all([
        axios.get(`${API}/admin/requests`),
        axios.get(`${API}/admin/stats`)
      ]);
      
      setAdminRequests(requestsResponse.data);
      setAdminStats(statsResponse.data);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      
      // Handle authentication errors - auto logout
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expirée. Reconnexion nécessaire.");
        handleLogout();
        return;
      }
      
      toast.error("Erreur lors du chargement des données admin");
    }
  };

  const fetchMyRequests = async () => {
    try {
      const response = await axios.get(`${API}/my-requests`);
      setMyRequests(response.data);
    } catch (error) {
      console.error('Error fetching my requests:', error);
      
      // Handle authentication errors - auto logout
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expirée. Reconnexion nécessaire.");
        handleLogout();
        return;
      }
      
      toast.error("Erreur lors du chargement de vos requêtes");
    }
  };

  const handleFileChange = (fileType, file) => {
    setFiles(prev => ({ ...prev, [fileType]: file }));
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateOutfit = async () => {
    if (!files.model_image) {
      toast.error("Veuillez sélectionner une image de modèle");
      return;
    }

    // Check user credits
    if (user.images_used_total >= user.images_limit_total) {
      toast.error(`Limite d'images atteinte (${user.images_used_total}/${user.images_limit_total})`);
      return;
    }

    setIsGenerating(true);
    const formDataToSend = new FormData();
    
    // Add files
    formDataToSend.append('model_image', files.model_image);
    if (files.fabric_image) formDataToSend.append('fabric_image', files.fabric_image);
    if (files.shoe_image) formDataToSend.append('shoe_image', files.shoe_image);
    if (files.accessory_image) formDataToSend.append('accessory_image', files.accessory_image);
    
    // Add form data
    Object.keys(formData).forEach(key => {
      if (formData[key]) {
        formDataToSend.append(key, formData[key]);
      }
    });

    try {
      const response = await axios.post(`${API}/generate`, formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        // Update generated images
        const newImage = {
          id: response.data.request_id,
          filename: response.data.image_filename,
          download_url: response.data.download_url,
          details: { ...formData }
        };
        setGeneratedImages(prev => [newImage, ...prev]);
        
        // Update user credits
        if (response.data.user_credits) {
          setUser(prev => ({
            ...prev,
            images_used_total: response.data.user_credits.used,
            images_limit_total: response.data.user_credits.limit
          }));
        }

        // Show success message
        toast.success(`Image générée avec succès ! Crédit restant: ${response.data.user_credits?.remaining || 0}`);
      }
    } catch (error) {
      console.error('Generation error:', error);
      
      // Handle authentication errors - auto logout
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expirée. Reconnexion nécessaire.");
        handleLogout();
        return;
      }
      
      if (error.response?.status === 403) {
        toast.error("Limite d'images atteinte");
      } else {
        toast.error("Erreur lors de la génération de l'image");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleImageSelection = (imageId) => {
    setSelectedImages(prev => {
      if (prev.includes(imageId)) {
        return prev.filter(id => id !== imageId);
      } else {
        return [...prev, imageId];
      }
    });
  };

  const downloadExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(
      adminRequests.map(request => ({
        ID: request.id,
        Utilisateur: request.user_email || 'N/A',
        Ambiance: request.atmosphere,
        'Type de costume': request.suit_type,
        Revers: request.lapel_type,
        Poches: request.pocket_type,
        Chaussures: request.shoe_type,
        Accessoire: request.accessory_type,
        Email: request.email || 'N/A',
        'Description tissu': request.fabric_description || 'N/A',
        Date: new Date(request.timestamp).toLocaleDateString('fr-FR'),
        'Lien téléchargement': `${BACKEND_URL}/api/download/generated_${request.id}.png`
      }))
    );
    
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Requêtes');
    XLSX.writeFile(workbook, `requetes_tailorview_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  const sendSingleImage = async (imageId) => {
    if (!formData.email) {
      toast.error("Veuillez saisir une adresse email");
      return;
    }

    try {
      const response = await axios.post(`${API}/send-multiple`, {
        email: formData.email,
        imageIds: [imageId],
        subject: emailTemplate.subject,
        body: emailTemplate.body
      });

      if (response.data.success) {
        toast.success("Image envoyée par email !");
      } else {
        toast.error("Erreur lors de l'envoi de l'email");
      }
    } catch (error) {
      console.error('Send single error:', error);
      
      // Handle authentication errors - auto logout
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expirée. Reconnexion nécessaire.");
        handleLogout();
        return;
      }
      
      toast.error("Erreur lors de l'envoi de l'email");
    }
  };

  const sendMultipleImages = async () => {
    if (selectedImages.length === 0) {
      toast.error("Veuillez sélectionner au moins une image");
      return;
    }

    if (!formData.email) {
      toast.error("Veuillez saisir une adresse email");
      return;
    }

    try {
      const response = await axios.post(`${API}/send-multiple`, {
        email: formData.email,
        imageIds: selectedImages,
        subject: emailTemplate.subject,
        body: emailTemplate.body
      });

      if (response.data.success) {
        toast.success(`${selectedImages.length} image(s) envoyée(s) par email !`);
        setSelectedImages([]);
      } else {
        toast.error("Erreur lors de l'envoi des emails");
      }
    } catch (error) {
      console.error('Send multiple error:', error);
      
      // Handle authentication errors - auto logout
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expirée. Reconnexion nécessaire.");
        handleLogout();
        return;
      }
      
      toast.error("Erreur lors de l'envoi des emails");
    }
  };

  // If not authenticated, show auth form
  if (!isAuthenticated) {
    return (
      <>
        <AuthForm onAuthSuccess={handleAuthSuccess} isDarkMode={isDarkMode} />
        <Toaster position="top-right" />
      </>
    );
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDarkMode ? 'bg-gradient-to-br from-slate-900 via-green-950 to-slate-800 text-white' : 'bg-white'}`}>
      <div className="container mx-auto p-4 max-w-7xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center space-x-4">
            <img 
              src={isDarkMode ? "/blandin-delloye-logo-light.png" : "/blandin-delloye-logo-dark.png"}
              alt="Blandin & Delloye" 
              className="h-12 w-auto max-w-[200px] object-contain"
              style={{ aspectRatio: 'auto' }}
            />
          </div>
          
          <div className="flex items-center space-x-4">
            {/* User info and credits */}
            <div className="text-right">
              <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                {user.nom}
              </p>
              <p className={`text-xs ${isDarkMode ? 'text-green-300' : 'text-slate-600'}`}>
                Images: {user.images_used_total}/{user.images_limit_total}
              </p>
            </div>
            
            {/* Theme toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDarkMode(!isDarkMode)}
              className={`p-2 w-10 h-10 ${isDarkMode ? 'border-green-800 text-white hover:bg-green-900 bg-slate-800' : 'border-gray-300'}`}
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            
            {/* Administration access - available for all users */}
            <Button
              variant="outline"
              size="sm"
              className={`p-2 w-10 h-10 ${isDarkMode ? 'border-green-800 text-white hover:bg-green-900 bg-slate-800' : 'border-gray-300'}`}
              title="Administration"
              onClick={() => {
                setCurrentView(currentView === 'admin' ? 'generator' : 'admin');
                if (currentView !== 'admin') {
                  if (user.role === 'admin') {
                    fetchAdminData();
                  } else {
                    fetchMyRequests();
                  }
                }
              }}
            >
              <Settings className="w-4 h-4" />
            </Button>
            
            {/* Logout */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className={`p-2 w-10 h-10 ${isDarkMode ? 'border-green-800 text-white hover:bg-green-900 bg-slate-800' : 'border-gray-300'}`}
              title="Déconnexion"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Main Content */}
        {currentView === 'generator' ? (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Generator Form */}
            <div className="lg:col-span-2 space-y-6">
              <Card className={`${isDarkMode ? 'bg-slate-900 border-green-900' : 'bg-white'}`}>
                <CardHeader>
                  <CardTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                    <Camera className="w-5 h-5 inline mr-2" />
                    Configuration de la tenue
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* File uploads */}
                  <div>
                    <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Image du modèle *</Label>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleFileChange('model_image', e.target.files[0])}
                      className={isDarkMode ? 'bg-slate-800 text-white border-green-800 file:bg-green-700 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 hover:file:bg-green-600' : 'file:bg-gray-100 file:text-gray-700 file:border-0 file:rounded file:px-3 file:py-1 file:mr-3'}
                    />
                  </div>

                  {/* Form selects */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Ambiance</Label>
                      <Select 
                        value={formData.atmosphere} 
                        onValueChange={(value) => handleFormChange('atmosphere', value)}
                      >
                        <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.atmospheres?.map((atmosphere) => (
                            <SelectItem key={atmosphere.value} value={atmosphere.value}>
                              {atmosphere.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Type de costume</Label>
                      <Select 
                        value={formData.suit_type} 
                        onValueChange={(value) => handleFormChange('suit_type', value)}
                      >
                        <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.suit_types?.map((suit) => (
                            <SelectItem key={suit} value={suit}>
                              {suit}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* More form fields */}
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Revers</Label>
                      <Select 
                        value={formData.lapel_type} 
                        onValueChange={(value) => handleFormChange('lapel_type', value)}
                      >
                        <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.lapel_types?.map((lapel) => (
                            <SelectItem key={lapel} value={lapel}>
                              {lapel}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Poches</Label>
                      <Select 
                        value={formData.pocket_type} 
                        onValueChange={(value) => handleFormChange('pocket_type', value)}
                      >
                        <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.pocket_types?.map((pocket) => (
                            <SelectItem key={pocket} value={pocket}>
                              {pocket}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Chaussures</Label>
                      <Select 
                        value={formData.shoe_type} 
                        onValueChange={(value) => handleFormChange('shoe_type', value)}
                      >
                        <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.shoe_types?.map((shoe) => (
                            <SelectItem key={shoe} value={shoe}>
                              {shoe}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {/* Conditional description field for shoes */}
                      {formData.shoe_type === 'Description texte' && (
                        <div className="mt-3">
                          <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Description des chaussures</Label>
                          <Textarea
                            value={formData.custom_shoe_description}
                            onChange={(e) => handleFormChange('custom_shoe_description', e.target.value)}
                            placeholder="Décrivez les chaussures souhaitées..."
                            rows={3}
                            className={isDarkMode ? 'bg-slate-800 text-white border-green-800 placeholder:text-green-400' : 'placeholder:text-gray-500'}
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Accessoire</Label>
                    <Select 
                      value={formData.accessory_type} 
                      onValueChange={(value) => handleFormChange('accessory_type', value)}
                    >
                      <SelectTrigger className={isDarkMode ? 'bg-slate-800 text-white border-green-800' : ''}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {options.accessory_types?.map((accessory) => (
                          <SelectItem key={accessory} value={accessory}>
                            {accessory}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    {/* Conditional description field for accessories */}
                    {formData.accessory_type === 'Description texte' && (
                      <div className="mt-3">
                        <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Description de l'accessoire</Label>
                        <Textarea
                          value={formData.custom_accessory_description}
                          onChange={(e) => handleFormChange('custom_accessory_description', e.target.value)}
                          placeholder="Décrivez l'accessoire souhaité..."
                          rows={3}
                          className={isDarkMode ? 'bg-slate-800 text-white border-green-800 placeholder:text-green-400' : 'placeholder:text-gray-500'}
                        />
                      </div>
                    )}
                  </div>

                  {/* Optional descriptions */}
                  <div>
                    <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Description du tissu (optionnel)</Label>
                    <Textarea
                      value={formData.fabric_description}
                      onChange={(e) => handleFormChange('fabric_description', e.target.value)}
                      placeholder="Décrivez le tissu souhaité..."
                      className={isDarkMode ? 'bg-slate-800 text-white border-green-800 placeholder:text-green-400' : 'placeholder:text-gray-500'}
                    />
                  </div>

                  {/* Optional image uploads */}
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Image tissu (optionnel)</Label>
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange('fabric_image', e.target.files[0])}
                        className={isDarkMode ? 'bg-slate-800 text-white border-green-800 file:bg-green-700 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 hover:file:bg-green-600' : 'file:bg-gray-100 file:text-gray-700 file:border-0 file:rounded file:px-3 file:py-1 file:mr-3'}
                      />
                    </div>
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Image chaussures (optionnel)</Label>
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange('shoe_image', e.target.files[0])}
                        className={isDarkMode ? 'bg-slate-800 text-white border-green-800 file:bg-green-700 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 hover:file:bg-green-600' : 'file:bg-gray-100 file:text-gray-700 file:border-0 file:rounded file:px-3 file:py-1 file:mr-3'}
                      />
                    </div>
                    <div>
                      <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Image accessoire (optionnel)</Label>
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange('accessory_image', e.target.files[0])}
                        className={isDarkMode ? 'bg-slate-800 text-white border-green-800 file:bg-green-700 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 hover:file:bg-green-600' : 'file:bg-gray-100 file:text-gray-700 file:border-0 file:rounded file:px-3 file:py-1 file:mr-3'}
                      />
                    </div>
                  </div>

                  {/* Email field */}
                  <div>
                    <Label className={isDarkMode ? 'text-green-300' : 'text-gray-700'}>Email (pour recevoir l'image)</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleFormChange('email', e.target.value)}
                      placeholder="votre.email@exemple.com"
                      className={isDarkMode ? 'bg-slate-800 text-white border-green-800 placeholder:text-green-400' : 'placeholder:text-gray-500'}
                    />
                  </div>

                  {/* Generate button */}
                  <Button 
                    onClick={generateOutfit} 
                    disabled={isGenerating || !files.model_image || user.images_used_total >= user.images_limit_total}
                    className={`w-full ${isDarkMode ? 'bg-green-700 hover:bg-green-600 text-white border-green-600' : ''}`}
                  >
                    {isGenerating ? (
                      <>
                        <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                        Génération en cours...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Générer la tenue ({user.images_limit_total - user.images_used_total} crédits restants)
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Generated Images */}
            <div className="space-y-6">
              <Card className={`${isDarkMode ? 'bg-slate-900 border-green-900' : 'bg-white'}`}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                      <Eye className="w-5 h-5 inline mr-2" />
                      Images générées
                    </CardTitle>
                    {selectedImages.length > 0 && (
                      <Button 
                        size="sm" 
                        onClick={sendMultipleImages}
                        className={isDarkMode ? 'bg-green-800 hover:bg-green-700' : ''}
                      >
                        <Mail className="w-4 h-4 mr-2" />
                        Envoyer ({selectedImages.length})
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {generatedImages.length === 0 ? (
                    <div className="text-center py-8">
                      <Camera className={`w-12 h-12 mx-auto mb-4 ${isDarkMode ? 'text-green-700' : 'text-gray-400'}`} />
                      <p className={isDarkMode ? 'text-green-300' : 'text-gray-600'}>
                        Aucune image générée pour le moment
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {generatedImages.map((image) => (
                        <div key={image.id} className={`border rounded-lg overflow-hidden ${isDarkMode ? 'border-green-800' : 'border-gray-200'}`}>
                          <div className="relative">
                            <img
                              src={`${BACKEND_URL}${image.download_url}`}
                              alt="Generated outfit"
                              className="w-full h-auto"
                            />
                            <div className="absolute top-2 right-2 flex space-x-2">
                              <input
                                type="checkbox"
                                checked={selectedImages.includes(image.id)}
                                onChange={() => handleImageSelection(image.id)}
                                className="w-4 h-4"
                              />
                            </div>
                          </div>
                          <div className="p-3">
                            <div className="flex justify-between items-center">
                              <p className={`text-sm ${isDarkMode ? 'text-green-300' : 'text-gray-600'}`}>
                                {image.details.atmosphere} • {image.details.suit_type}
                              </p>
                              <div className="flex items-center space-x-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => sendSingleImage(image.id)}
                                  className={`${isDarkMode ? 'border-green-800 text-green-300 hover:bg-green-900' : 'border-gray-300'}`}
                                  title="Envoyer cette image par email"
                                >
                                  <Mail className="w-4 h-4" />
                                </Button>
                                <a
                                  href={`${BACKEND_URL}${image.download_url}`}
                                  download
                                  className={`${isDarkMode ? 'text-green-400 hover:text-green-300' : 'text-blue-600 hover:text-blue-800'}`}
                                  title="Télécharger l'image"
                                >
                                  <Download className="w-4 h-4" />
                                </a>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          /* Admin Panel */
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Panneau d'Administration
              </h2>
              <Button
                variant="outline"
                onClick={() => setCurrentView('generator')}
                className={isDarkMode ? 'border-slate-600 text-white hover:bg-slate-700' : ''}
              >
                Retour au générateur
              </Button>
            </div>

            {/* Admin Tabs */}
            <div className="flex space-x-1 bg-gray-100 dark:bg-slate-800 p-1 rounded-lg">
              <Button
                variant={adminTab === 'dashboard' ? 'default' : 'ghost'}
                onClick={() => setAdminTab('dashboard')}
                className={adminTab === 'dashboard' ? '' : (isDarkMode ? 'text-white hover:bg-slate-700' : '')}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Tableau de bord
              </Button>
              <Button
                variant={adminTab === 'users' ? 'default' : 'ghost'}
                onClick={() => setAdminTab('users')}
                className={adminTab === 'users' ? '' : (isDarkMode ? 'text-white hover:bg-slate-700' : '')}
              >
                <Users className="w-4 h-4 mr-2" />
                Utilisateurs
              </Button>
              <Button
                variant={adminTab === 'emailing' ? 'default' : 'ghost'}
                onClick={() => setAdminTab('emailing')}
                className={adminTab === 'emailing' ? '' : (isDarkMode ? 'text-white hover:bg-slate-700' : '')}
              >
                <Mail className="w-4 h-4 mr-2" />
                Emailing
              </Button>
            </div>

            {/* Admin Content */}
            {adminTab === 'dashboard' && (
              <div className="space-y-6">
                {/* Statistics Cards */}
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className={isDarkMode ? 'bg-slate-800 border-slate-700' : ''}>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <p className={`text-sm font-medium ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
                            Total requêtes
                          </p>
                          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            {adminStats.total_requests || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className={isDarkMode ? 'bg-slate-800 border-slate-700' : ''}>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                          <Sparkles className="w-6 h-6 text-green-600 dark:text-green-300" />
                        </div>
                        <div>
                          <p className={`text-sm font-medium ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
                            Images générées
                          </p>
                          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            {adminStats.generated_images_count || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Detailed Requests Table */}
                <Card className={isDarkMode ? 'bg-slate-800 border-slate-700' : ''}>
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className={isDarkMode ? 'text-white' : ''}>
                        Historique des requêtes
                      </CardTitle>
                      <Button onClick={downloadExcel} variant="outline">
                        <FileDown className="w-4 h-4 mr-2" />
                        Export XLSX
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className={isDarkMode ? 'border-slate-700' : ''}>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Miniature</TableHead>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>ID</TableHead>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Utilisateur</TableHead>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Sélections</TableHead>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Email envoyé</TableHead>
                            <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {adminRequests.map((request) => (
                            <TableRow key={request.id} className={isDarkMode ? 'border-slate-700' : ''}>
                              <TableCell>
                                <img
                                  src={`${BACKEND_URL}/api/download/generated_${request.id}.png`}
                                  alt="Generated outfit"
                                  className="w-16 h-16 object-cover rounded border"
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                  }}
                                />
                              </TableCell>
                              <TableCell className={`font-mono text-xs ${isDarkMode ? 'text-white' : ''}`}>
                                {request.id.substring(0, 8)}...
                              </TableCell>
                              <TableCell className={isDarkMode ? 'text-white' : ''}>
                                {request.user_email || request.email || 'N/A'}
                              </TableCell>
                              <TableCell className={`text-sm ${isDarkMode ? 'text-white' : ''}`}>
                                <div>
                                  <strong>{request.atmosphere}</strong><br/>
                                  {request.suit_type} • {request.lapel_type}<br/>
                                  {request.pocket_type} • {request.shoe_type}<br/>
                                  {request.accessory_type}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={request.email ? 'default' : 'secondary'}>
                                  {request.email ? 'Oui' : 'Non'}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <a
                                  href={`${BACKEND_URL}/api/download/generated_${request.id}.png`}
                                  download
                                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                                >
                                  <Download className="w-4 h-4" />
                                </a>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {adminTab === 'users' && (
              <UserManagementTab 
                isDarkMode={isDarkMode} 
                accessToken={accessToken} 
              />
            )}

            {adminTab === 'emailing' && (
              <Card className={isDarkMode ? 'bg-slate-800 border-slate-700' : ''}>
                <CardHeader>
                  <CardTitle className={isDarkMode ? 'text-white' : ''}>
                    Configuration Email
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className={isDarkMode ? 'text-white' : ''}>Sujet</Label>
                    <Input
                      value={emailTemplate.subject}
                      onChange={(e) => setEmailTemplate(prev => ({ ...prev, subject: e.target.value }))}
                      className={isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}
                    />
                  </div>
                  <div>
                    <Label className={isDarkMode ? 'text-white' : ''}>Corps du message</Label>
                    <Textarea
                      value={emailTemplate.body}
                      onChange={(e) => setEmailTemplate(prev => ({ ...prev, body: e.target.value }))}
                      rows={8}
                      className={isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}
                    />
                  </div>
                  <Button onClick={() => toast.success("Template sauvegardé")}>
                    Sauvegarder le template
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
      
      <Toaster position="top-right" />
    </div>
  );
}

export default App;