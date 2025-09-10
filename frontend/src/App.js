import React, { useState, useEffect } from "react";
import "./App.css";
import { Upload, Camera, Palette, Send, Download, Mail, Sparkles, Crown, Star, Settings, Users, BarChart3, Trash2, Eye, FileDown, Moon, Sun } from "lucide-react";
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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState('generator'); // 'generator' or 'admin'
  const [adminTab, setAdminTab] = useState('dashboard'); // 'dashboard', 'emailing', or 'users'
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [adminCode, setAdminCode] = useState('');
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const [generatedImages, setGeneratedImages] = useState([]); // Carrousel des images générées
  const [emailTemplate, setEmailTemplate] = useState({
    subject: 'Votre Visualisation de Tenue de Marié Personnalisée',
    body: `Cher Client,

Merci d'avoir utilisé notre service de visualisation de tenue de marié !

Veuillez trouver vos visualisations de tenue générées en pièce jointe.

Cordialement,
L'équipe Blandin & Delloye`
  });
  const [options, setOptions] = useState({});
  const [formData, setFormData] = useState({
    atmosphere: 'rustic',
    suit_type: '2-piece suit',
    lapel_type: 'Standard notch lapel',
    pocket_type: 'Slanted, no flaps',
    shoe_type: 'Black loafers',
    accessory_type: 'Tie',
    fabric_description: '',
    custom_shoe_description: '',
    custom_accessory_description: '',
    email: ''
  });
  const [modelImage, setModelImage] = useState(null);
  const [fabricImage, setFabricImage] = useState(null);
  const [shoeImage, setShoeImage] = useState(null);
  const [accessoryImage, setAccessoryImage] = useState(null);
  const [modelPreview, setModelPreview] = useState(null);
  const [fabricPreview, setFabricPreview] = useState(null);
  const [shoePreview, setShoePreview] = useState(null);
  const [accessoryPreview, setAccessoryPreview] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [progress, setProgress] = useState(0);
  
  // Admin state
  const [adminRequests, setAdminRequests] = useState([]);
  const [adminStats, setAdminStats] = useState({});
  const [isLoadingAdmin, setIsLoadingAdmin] = useState(false);

  useEffect(() => {
    fetchOptions();
    if (currentView === 'admin') {
      fetchAdminData();
    }
  }, [currentView]);

  const fetchOptions = async () => {
    try {
      const response = await axios.get(`${API}/options`);
      setOptions(response.data);
    } catch (error) {
      console.error("Error fetching options:", error);
      toast.error("Échec du chargement des options");
    }
  };

  const fetchAdminData = async () => {
    setIsLoadingAdmin(true);
    try {
      const [requestsResponse, statsResponse] = await Promise.all([
        axios.get(`${API}/admin/requests`),
        axios.get(`${API}/admin/stats`)
      ]);
      setAdminRequests(requestsResponse.data);
      setAdminStats(statsResponse.data);
    } catch (error) {
      console.error("Error fetching admin data:", error);
      toast.error("Échec du chargement des données admin");
    } finally {
      setIsLoadingAdmin(false);
    }
  };

  const deleteRequest = async (requestId) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette demande ?")) return;
    
    try {
      await axios.delete(`${API}/admin/request/${requestId}`);
      toast.success("Demande supprimée avec succès");
      fetchAdminData(); // Refresh data
    } catch (error) {
      console.error("Error deleting request:", error);
      toast.error("Échec de la suppression");
    }
  };

  const handleFileChange = (event, type) => {
    const file = event.target.files[0];
    if (file) {
      switch(type) {
        case 'model':
          setModelImage(file);
          setModelPreview(URL.createObjectURL(file));
          break;
        case 'fabric':
          setFabricImage(file);
          setFabricPreview(URL.createObjectURL(file));
          break;
        case 'shoe':
          setShoeImage(file);
          setShoePreview(URL.createObjectURL(file));
          break;
        case 'accessory':
          setAccessoryImage(file);
          setAccessoryPreview(URL.createObjectURL(file));
          break;
      }
    }
  };

  const handleInputChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 800);
    return interval;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!modelImage) {
      toast.error("Veuillez télécharger une photo de modèle");
      return;
    }

    if (!formData.atmosphere || !formData.suit_type || !formData.lapel_type || 
        !formData.pocket_type || !formData.shoe_type || !formData.accessory_type) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }

    setIsGenerating(true);
    const progressInterval = simulateProgress();

    try {
      const data = new FormData();
      data.append('model_image', modelImage);
      if (fabricImage) {
        data.append('fabric_image', fabricImage);
      }
      if (shoeImage) {
        data.append('shoe_image', shoeImage);
      }
      if (accessoryImage) {
        data.append('accessory_image', accessoryImage);
      }
      
      Object.keys(formData).forEach(key => {
        if (formData[key]) {
          data.append(key, formData[key]);
        }
      });

      const response = await axios.post(`${API}/generate`, data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.data.success) {
        const newImage = {
          ...response.data,
          modelImageData: modelPreview, // Garder la référence du modèle
          timestamp: new Date().toISOString()
        };
        
        setGeneratedImage(newImage);
        
        // Ajouter au carrousel (max 3 images)
        setGeneratedImages(prev => {
          const updated = [...prev, newImage];
          return updated.slice(-3); // Garder seulement les 3 dernières
        });
        
        toast.success("Tenue générée avec succès !");
        
        // Gestion des messages d'email avec popup de confirmation
        if (formData.email) {
          if (response.data.email_sent) {
            toast.success(`✅ Email envoyé avec succès à ${formData.email} !`, {
              duration: 5000,
              description: "Vérifiez votre boîte de réception et vos spams."
            });
          } else {
            toast.error(`❌ Échec de l'envoi de l'email à ${formData.email}`, {
              duration: 7000,
              description: response.data.email_message || "Vérifiez l'adresse email ou contactez l'administrateur."
            });
          }
        }
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Error generating outfit:", error);
      toast.error("Échec de la génération de la tenue. Veuillez réessayer.");
    } finally {
      setIsGenerating(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const downloadImage = async () => {
    if (generatedImage?.download_url) {
      try {
        const response = await fetch(`${BACKEND_URL}${generatedImage.download_url}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = generatedImage.image_filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("Image téléchargée !");
      } catch (error) {
        toast.error("Échec du téléchargement de l'image");
      }
    }
  };

  const getAtmosphereDescription = (key) => {
    const descriptions = {
      rustic: "Champètre - Fleurs et bois avec arche florale",
      seaside: "Bord de mer - Cérémonie sur la plage avec océan", 
      chic_elegant: "Chic et élégant - Château comme Versailles",
      hangover: "Very Bad Trip - Style célébration Las Vegas"
    };
    return descriptions[key] || key;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const generatePromptPreview = (request) => {
    return `Costume ${request.suit_type}, ambiance ${request.atmosphere}, revers ${request.lapel_type}, poches ${request.pocket_type}, chaussures ${request.shoe_type}, accessoire ${request.accessory_type}`;
  };

  const sendMultipleImages = async () => {
    if (!formData.email) {
      toast.error("Veuillez saisir un email");
      return;
    }
    
    if (generatedImages.length === 0) {
      toast.error("Aucune image à envoyer");
      return;
    }
    
    try {
      const imageIds = generatedImages.map(img => img.request_id);
      const response = await axios.post(`${API}/send-multiple`, {
        email: formData.email,
        imageIds: imageIds,
        subject: emailTemplate.subject,
        body: emailTemplate.body
      });
      
      if (response.data.success) {
        toast.success(`${generatedImages.length} images envoyées par email !`);
      }
    } catch (error) {
      toast.error("Échec de l'envoi multiple");
    }
  };

  const handleAdminAccess = () => {
    if (adminCode === '1149') {
      setIsAdminAuthenticated(true);
      setCurrentView('admin');
      setAdminCode('');
      fetchAdminData();
      toast.success("Accès administrateur accordé");
    } else {
      toast.error("Code administrateur incorrect");
      setAdminCode('');
    }
  };

  const AdminCodeDialog = () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="p-2 w-10 h-10"
          title="Administration"
        >
          <Settings className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className={`sm:max-w-[425px] ${isDarkMode ? 'bg-slate-800 text-white' : ''}`}>
        <DialogHeader>
          <DialogTitle className={isDarkMode ? 'text-white' : ''}>Accès Administration</DialogTitle>
          <DialogDescription className={isDarkMode ? 'text-slate-400' : ''}>
            Entrez le code administrateur pour accéder au panneau d'administration.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="admin-code" className="text-right">
              Code
            </Label>
            <Input
              id="admin-code"
              type="password"
              value={adminCode}
              onChange={(e) => setAdminCode(e.target.value)}
              placeholder="Entrez le code"
              className={`col-span-3 ${isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}`}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAdminAccess();
                }
              }}
            />
          </div>
        </div>
        <div className="flex justify-end">
          <Button onClick={handleAdminAccess} className={isDarkMode ? 'bg-slate-600 hover:bg-slate-500' : ''}>
            Accéder
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );

  const downloadCSV = () => {
    const headers = ['Date', 'Ambiance', 'Costume', 'Revers', 'Poches', 'Chaussures', 'Accessoire', 'Email', 'Tissu', 'Prompt'];
    const csvData = adminRequests.map(request => [
      formatDate(request.timestamp),
      getAtmosphereDescription(request.atmosphere),
      request.suit_type === '2-piece suit' ? '2 pièces' : '3 pièces',
      request.lapel_type,
      request.pocket_type,
      request.shoe_type,
      request.accessory_type,
      request.email || 'N/A',
      request.fabric_description || 'N/A',
      `"${generatePromptPreview(request)}"`
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `demandes_tailorview_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("CSV téléchargé !");
  };

  const EmailingTab = () => (
    <div className="space-y-6">
      <Card className={`border-0 shadow-xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm' : 'bg-white/50 backdrop-blur-sm'}`}>
        <CardHeader>
          <CardTitle className={isDarkMode ? 'text-white' : 'text-slate-800'}>
            📧 Gestion des Templates Email
          </CardTitle>
          <CardDescription className={isDarkMode ? 'text-white' : ''}>
            Personnalisez les emails envoyés aux clients
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className={isDarkMode ? 'text-white' : 'text-slate-700'}>Objet de l'email</Label>
            <Input
              value={emailTemplate.subject}
              onChange={(e) => setEmailTemplate(prev => ({...prev, subject: e.target.value}))}
              className={isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}
            />
          </div>
          <div>
            <Label className={isDarkMode ? 'text-white' : 'text-slate-700'}>Corps de l'email</Label>
            <Textarea
              rows={10}
              value={emailTemplate.body}
              onChange={(e) => setEmailTemplate(prev => ({...prev, body: e.target.value}))}
              className={isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}
            />
          </div>
          <Button 
            onClick={() => toast.success("Template email sauvegardé !")}
            className={isDarkMode ? 'bg-slate-600 hover:bg-slate-500' : ''}
          >
            Sauvegarder le Template
          </Button>
        </CardContent>
      </Card>
      
      <Card className={`border-0 shadow-xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm' : 'bg-white/50 backdrop-blur-sm'}`}>
        <CardHeader>
          <CardTitle className={isDarkMode ? 'text-white' : 'text-slate-800'}>
            📊 Statistiques d'Envoi
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className={`p-4 rounded ${isDarkMode ? 'bg-slate-700' : 'bg-slate-100'}`}>
              <div className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>
                {adminRequests.filter(r => r.email).length}
              </div>
              <div className={`text-sm ${isDarkMode ? 'text-white' : 'text-slate-600'}`}>
                Emails envoyés
              </div>
            </div>
            <div className={`p-4 rounded ${isDarkMode ? 'bg-slate-700' : 'bg-slate-100'}`}>
              <div className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>
                {((adminRequests.filter(r => r.email).length / adminStats.total_requests) * 100 || 0).toFixed(1)}%
              </div>
              <div className={`text-sm ${isDarkMode ? 'text-white' : 'text-slate-600'}`}>
                Taux d'envoi
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const AdminView = () => (
    <div className="space-y-6">
      {/* Admin Tabs */}
      <div className="flex space-x-4 border-b border-slate-300">
        <Button
          variant={adminTab === 'dashboard' ? 'default' : 'ghost'}
          onClick={() => setAdminTab('dashboard')}
          className={isDarkMode ? 'text-white' : ''}
        >
          📊 Dashboard
        </Button>
        <Button
          variant={adminTab === 'emailing' ? 'default' : 'ghost'}
          onClick={() => setAdminTab('emailing')}
          className={isDarkMode ? 'text-white' : ''}
        >
          📧 Emailing
        </Button>
      </div>

      {adminTab === 'dashboard' ? (
        <>
      {/* Admin Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>Total Demandes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isDarkMode ? 'text-slate-100' : ''}`}>{adminStats.total_requests || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>Aujourd'hui</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isDarkMode ? 'text-slate-100' : ''}`}>{adminStats.today_requests || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>Images Générées</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isDarkMode ? 'text-slate-100' : ''}`}>{adminStats.generated_images_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>Ambiance Populaire</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-sm font-medium ${isDarkMode ? 'text-slate-100' : ''}`}>
              {adminStats.atmosphere_stats?.[0]?._id || 'N/A'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`flex items-center gap-2 ${isDarkMode ? 'text-slate-100' : ''}`}>
                <Users className="w-5 h-5" />
                Toutes les Demandes
              </CardTitle>
              <CardDescription className={isDarkMode ? 'text-slate-400' : ''}>Historique complet des demandes de tenues</CardDescription>
            </div>
            <Button onClick={downloadCSV} className="flex items-center gap-2" size="sm">
              <FileDown className="w-4 h-4" />
              Télécharger CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingAdmin ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Miniature</TableHead>
                    <TableHead>Ambiance</TableHead>
                    <TableHead>Costume</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Prompt</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {adminRequests.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell className="text-sm">
                        {formatDate(request.timestamp)}
                      </TableCell>
                      <TableCell>
                        <img 
                          src={`${BACKEND_URL}/api/download/generated_${request.id}.png`}
                          alt="Miniature"
                          className="w-12 h-12 object-cover rounded border"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {getAtmosphereDescription(request.atmosphere)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {request.suit_type === '2-piece suit' ? '2 pièces' : '3 pièces'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {request.email || 'N/A'}
                      </TableCell>
                      <TableCell className="text-xs max-w-xs">
                        <div className="truncate" title={generatePromptPreview(request)}>
                          {generatePromptPreview(request)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(`${BACKEND_URL}/api/download/generated_${request.id}.png`, '_blank')}
                            className="flex items-center gap-1 px-2 py-1"
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deleteRequest(request.id)}
                            className="flex items-center gap-1 px-2 py-1"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {adminRequests.length === 0 && (
                <div className="text-center py-8 text-slate-500">
                  Aucune demande trouvée
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      </>
      ) : (
        <EmailingTab />
      )}
    </div>
  );

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDarkMode ? 'dark bg-slate-900' : 'bg-gradient-to-br from-slate-50 via-white to-slate-100'}`}>
      <Toaster position="top-right" richColors />
      {/* Header */}
      <header className={`backdrop-blur-md border-b sticky top-0 z-50 transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/80 border-slate-700' : 'bg-white/80 border-slate-200'}`}>
        {/* Mobile Logo Banner */}
        <div className={`md:hidden mobile-logo-banner transition-colors duration-300 ${isDarkMode ? 'bg-gradient-to-r from-slate-800 to-slate-700' : ''}`}>
          <img 
            src={isDarkMode 
              ? "https://customer-assets.emergentagent.com/job_tailorview/artifacts/zbc9zzks_logo%20blanc%20sans%20fond.png"
              : "https://customer-assets.emergentagent.com/job_tailorview/artifacts/sgrg1l59_logo%20noir%20sans%20fond.png"
            }
            alt="Logo" 
            className="h-32 object-contain"
          />
        </div>
        
        {/* Main Header */}
        <div className="container mx-auto px-4 py-3 mobile-header">
          <div className="flex items-center justify-between">
            {/* Desktop Logo - 100% plus grand */}
            <div className="hidden md:flex items-center">
              <img 
                src={isDarkMode 
                  ? "https://customer-assets.emergentagent.com/job_tailorview/artifacts/zbc9zzks_logo%20blanc%20sans%20fond.png"
                  : "https://customer-assets.emergentagent.com/job_tailorview/artifacts/sgrg1l59_logo%20noir%20sans%20fond.png"
                }
                alt="Logo" 
                className="w-48 h-48 lg:w-64 lg:h-64 object-contain"
              />
            </div>
            
            {/* Navigation - Compact buttons */}
            <div className="flex items-center space-x-2 mobile-nav-buttons">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-2 w-10 h-10"
                title={isDarkMode ? "Mode clair" : "Mode sombre"}
              >
                {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </Button>
              
              <Button
                variant={currentView === 'generator' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('generator')}
                className="p-2 w-10 h-10"
                title="Générateur"
              >
                <Camera className="w-4 h-4" />
              </Button>
              
              {isAdminAuthenticated ? (
                <Button
                  variant={currentView === 'admin' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setCurrentView('admin');
                    fetchAdminData();
                  }}
                  className="p-2 w-10 h-10"
                  title="Administration"
                >
                  <Settings className="w-4 h-4" />
                </Button>
              ) : (
                <AdminCodeDialog />
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-7xl">
        {currentView === 'generator' ? (
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Configuration Panel */}
            <div className="space-y-6">
              <Card className={`border-0 shadow-xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm' : 'bg-white/50 backdrop-blur-sm'}`}>
                <CardHeader className="pb-4">
                  <CardTitle className={`flex items-center gap-2 ${isDarkMode ? 'text-slate-100' : 'text-slate-800'}`}>
                    <Camera className="w-5 h-5" />
                    Téléchargement de Photos
                  </CardTitle>
                  <CardDescription className={isDarkMode ? 'text-slate-400' : ''}>Téléchargez votre photo de modèle et référence de tissu optionnelle</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Model Image Upload */}
                  <div>
                    <Label className={`text-sm font-medium mb-3 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>
                      Photo Modèle *
                    </Label>
                    <div className="relative">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange(e, 'model')}
                        className="hidden"
                        id="model-upload"
                      />
                      <label
                        htmlFor="model-upload"
                        className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed cursor-pointer transition-colors ${isDarkMode ? 'border-slate-600 bg-slate-700/50 hover:bg-slate-600/50 hover:border-slate-500' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-100/50 hover:border-slate-400'}`}
                      >
                        {modelPreview ? (
                          <img src={modelPreview} alt="Aperçu modèle" className="w-full h-full object-cover" />
                        ) : (
                          <div className="text-center">
                            <Upload className={`w-8 h-8 mx-auto mb-2 ${isDarkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                            <p className={`text-sm ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>Cliquez pour télécharger la photo du modèle</p>
                          </div>
                        )}
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className={`border-0 shadow-xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm' : 'bg-white/50 backdrop-blur-sm'}`}>
                <CardHeader className="pb-4">
                  <CardTitle className={`flex items-center gap-2 ${isDarkMode ? 'text-slate-100' : 'text-slate-800'}`}>
                    <Star className="w-5 h-5" />
                    Personnalisation de la Tenue
                  </CardTitle>
                  <CardDescription className={isDarkMode ? 'text-slate-400' : ''}>Personnalisez chaque détail de la tenue du marié</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Atmosphere */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Ambiance Mariage *</Label>
                      <Select value={formData.atmosphere} onValueChange={(value) => handleInputChange('atmosphere', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez l'ambiance du mariage" />
                        </SelectTrigger>
                        <SelectContent>
                          {options.atmospheres?.map((atmosphere) => (
                            <SelectItem key={atmosphere} value={atmosphere}>
                              {getAtmosphereDescription(atmosphere)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Suit Type */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Type de Costume *</Label>
                      <Select value={formData.suit_type} onValueChange={(value) => handleInputChange('suit_type', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez le type de costume" />
                        </SelectTrigger>
                        <SelectContent>
                          {options.suit_types?.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type === '2-piece suit' ? 'Costume 2 pièces' : 
                               type === '3-piece suit' ? 'Costume 3 pièces' : type}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Lapel Type */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Type de Revers *</Label>
                      <Select value={formData.lapel_type} onValueChange={(value) => handleInputChange('lapel_type', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez le type de revers" />
                        </SelectTrigger>
                        <SelectContent>
                          {options.lapel_types?.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type === 'Standard notch lapel' ? 'Revers cran standard' :
                               type === 'Wide notch lapel' ? 'Revers cran large' :
                               type === 'Standard peak lapel' ? 'Revers pointe standard' :
                               type === 'Wide peak lapel' ? 'Revers pointe large' :
                               type === 'Shawl collar with satin lapel' ? 'Col châle avec revers satin' :
                               type === 'Standard double-breasted peak lapel' ? 'Revers pointe croisé standard' :
                               type === 'Wide double-breasted peak lapel' ? 'Revers pointe croisé large' : type}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Pocket Type */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Type de Poches *</Label>
                      <Select value={formData.pocket_type} onValueChange={(value) => handleInputChange('pocket_type', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez le type de poches" />
                        </SelectTrigger>
                        <SelectContent>
                          {options.pocket_types?.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type === 'Slanted, no flaps' ? 'Inclinées, sans rabats' :
                               type === 'Slanted with flaps' ? 'Inclinées avec rabats' :
                               type === 'Straight with flaps' ? 'Droites avec rabats' :
                               type === 'Straight, no flaps' ? 'Droites, sans rabats' :
                               type === 'Patch pockets' ? 'Poches plaquées' : type}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Fabric Description */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Description du Tissu</Label>
                      <Select value={formData.fabric_description === 'PHOTO' ? 'photo' : 'text'} 
                              onValueChange={(value) => {
                                if (value === 'text') {
                                  handleInputChange('fabric_description', '');
                                } else {
                                  handleInputChange('fabric_description', 'PHOTO');
                                }
                              }}>
                        <SelectTrigger className="w-full mb-2">
                          <SelectValue placeholder="Choisissez le type de description" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="text">Description texte</SelectItem>
                          <SelectItem value="photo">Exemple photo</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      {formData.fabric_description === 'PHOTO' ? (
                        <div className="relative">
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => handleFileChange(e, 'fabric')}
                            className="hidden"
                            id="fabric-upload"
                          />
                          <label
                            htmlFor="fabric-upload"
                            className={`flex flex-col items-center justify-center w-full h-24 border-2 border-dashed cursor-pointer transition-colors ${isDarkMode ? 'border-slate-600 bg-slate-700/50 hover:bg-slate-600/50 hover:border-slate-500' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-100/50 hover:border-slate-400'}`}
                          >
                            {fabricPreview ? (
                              <img src={fabricPreview} alt="Aperçu tissu" className="w-full h-full object-cover" />
                            ) : (
                              <div className="text-center">
                                <Palette className={`w-6 h-6 mx-auto mb-1 ${isDarkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                                <p className={`text-xs ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>Photo du tissu</p>
                              </div>
                            )}
                          </label>
                        </div>
                      ) : (
                        <Textarea
                          placeholder="Décrivez le tissu (ex: laine vert eucalyptus, rayures marine, etc.)"
                          value={formData.fabric_description}
                          onChange={(e) => handleInputChange('fabric_description', e.target.value)}
                          className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
                        />
                      )}
                    </div>

                    {/* Shoe Type */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Chaussures *</Label>
                      <Select value={formData.shoe_type} onValueChange={(value) => handleInputChange('shoe_type', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez le type de chaussures" />
                        </SelectTrigger>  
                        <SelectContent>
                          <SelectItem value="Black loafers">Mocassins noirs</SelectItem>
                          <SelectItem value="Brown loafers">Mocassins marron</SelectItem>
                          <SelectItem value="Black one-cut">Richelieu noires</SelectItem>
                          <SelectItem value="Brown one-cut">Richelieu marron</SelectItem>
                          <SelectItem value="White sneakers">Baskets blanches</SelectItem>
                          <SelectItem value="Description texte">Description texte</SelectItem>
                          <SelectItem value="Exemple photo">Exemple photo</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      {formData.shoe_type === 'Description texte' && (
                        <Textarea
                          placeholder="Décrivez vos chaussures personnalisées..."
                          value={formData.custom_shoe_description}
                          onChange={(e) => handleInputChange('custom_shoe_description', e.target.value)}
                          className={`mt-2 ${isDarkMode ? 'bg-slate-700 text-white border-white' : ''}`}
                        />
                      )}
                      
                      {formData.shoe_type === 'Exemple photo' && (
                        <div className="relative mt-2">
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => handleFileChange(e, 'shoe')}
                            className="hidden"
                            id="shoe-upload"
                          />
                          <label
                            htmlFor="shoe-upload"
                            className={`flex flex-col items-center justify-center w-full h-24 border-2 border-dashed cursor-pointer transition-colors ${isDarkMode ? 'border-slate-600 bg-slate-700/50 hover:bg-slate-600/50 hover:border-slate-500' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-100/50 hover:border-slate-400'}`}
                          >
                            {shoePreview ? (
                              <img src={shoePreview} alt="Aperçu chaussures" className="w-full h-full object-cover" />
                            ) : (
                              <div className="text-center">
                                <Upload className={`w-6 h-6 mx-auto mb-1 ${isDarkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                                <p className={`text-xs ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>Photo des chaussures</p>
                              </div>
                            )}
                          </label>
                        </div>
                      )}
                    </div>

                    {/* Accessory Type */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Accessoire *</Label>
                      <Select value={formData.accessory_type} onValueChange={(value) => handleInputChange('accessory_type', value)}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choisissez le type d'accessoire" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Bow tie">Nœud papillon</SelectItem>
                          <SelectItem value="Tie">Cravate</SelectItem>
                          <SelectItem value="Description texte">Description texte</SelectItem>
                          <SelectItem value="Photo">Photo</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      {formData.accessory_type === 'Description texte' && (
                        <Textarea
                          placeholder="Décrivez votre accessoire personnalisé..."
                          value={formData.custom_accessory_description}
                          onChange={(e) => handleInputChange('custom_accessory_description', e.target.value)}
                          className={`mt-2 ${isDarkMode ? 'bg-slate-700 text-white border-white' : ''}`}
                        />
                      )}
                      
                      {formData.accessory_type === 'Photo' && (
                        <div className="relative mt-2">
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => handleFileChange(e, 'accessory')}
                            className="hidden"
                            id="accessory-upload"
                          />
                          <label
                            htmlFor="accessory-upload"
                            className={`flex flex-col items-center justify-center w-full h-24 border-2 border-dashed cursor-pointer transition-colors ${isDarkMode ? 'border-slate-600 bg-slate-700/50 hover:bg-slate-600/50 hover:border-slate-500' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-100/50 hover:border-slate-400'}`}
                          >
                            {accessoryPreview ? (
                              <img src={accessoryPreview} alt="Aperçu accessoire" className="w-full h-full object-cover" />
                            ) : (
                              <div className="text-center">
                                <Upload className={`w-6 h-6 mx-auto mb-1 ${isDarkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                                <p className={`text-xs ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>Photo de l'accessoire</p>
                              </div>
                            )}
                          </label>
                        </div>
                      )}
                    </div>

                    {/* Email */}
                    <div>
                      <Label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>Email (Optionnel)</Label>
                      <Input
                        type="email"
                        placeholder="votre@email.com"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        className={isDarkMode ? 'bg-slate-700 text-white border-white' : ''}
                      />
                      <p className={`text-xs mt-1 ${isDarkMode ? 'text-slate-300' : 'text-slate-500'}`}>Recevez l'image générée par email</p>
                    </div>

                    <Separator className="my-6" />

                    <Button
                      type="submit"
                      disabled={isGenerating}
                      className={`w-full h-12 font-medium shadow-lg hover:shadow-xl transition-all duration-200 ${isDarkMode ? 'bg-gradient-to-r from-slate-700 to-slate-600 hover:from-slate-600 hover:to-slate-500 text-white' : 'bg-gradient-to-r from-slate-800 to-slate-600 hover:from-slate-700 hover:to-slate-500 text-white'}`}
                    >
                      {isGenerating ? (
                        <div className="flex items-center gap-2">
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                          Génération en cours...
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-5 h-5" />
                          Générer la Tenue
                        </div>
                      )}
                    </Button>

                    {isGenerating && (
                      <div className="space-y-2">
                        <Progress value={progress} className="w-full" />
                        <p className={`text-sm text-center ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                          Génération de votre visualisation de tenue personnalisée...
                        </p>
                      </div>
                    )}
                  </form>
                </CardContent>
              </Card>
            </div>

            {/* Results Panel */}
            <div className="space-y-6">
              <Card className={`border-0 shadow-xl min-h-[600px] transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm' : 'bg-white/50 backdrop-blur-sm'}`}>
                <CardHeader>
                  <CardTitle className={`flex items-center gap-2 ${isDarkMode ? 'text-slate-100' : 'text-slate-800'}`}>
                    <Star className="w-5 h-5" />
                    Tenue Générée
                  </CardTitle>
                  <CardDescription className={isDarkMode ? 'text-slate-400' : ''}>Votre visualisation de tenue de marié personnalisée</CardDescription>
                </CardHeader>
                <CardContent>
                  {generatedImage ? (
                    <div className="space-y-4">
                      <div className={`relative overflow-hidden ${isDarkMode ? 'bg-slate-700' : 'bg-slate-100'}`}>
                        <img
                          src={`${BACKEND_URL}${generatedImage.download_url}`}
                          alt="Tenue générée"
                          className="w-full h-auto"
                        />
                      </div>
                      
                      {/* Carrousel des images générées */}
                      {generatedImages.length > 1 && (
                        <div className="space-y-2">
                          <h4 className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-slate-700'}`}>
                            Autres variantes ({generatedImages.length})
                          </h4>
                          <div className="flex space-x-2 overflow-x-auto pb-2">
                            {generatedImages.map((img, index) => (
                              <div key={index} className="flex-shrink-0">
                                <img
                                  src={`${BACKEND_URL}${img.download_url}`}
                                  alt={`Variante ${index + 1}`}
                                  className={`w-16 h-16 object-cover cursor-pointer border-2 transition-colors ${
                                    generatedImage.request_id === img.request_id 
                                      ? 'border-blue-500' 
                                      : isDarkMode ? 'border-slate-600' : 'border-slate-300'
                                  }`}
                                  onClick={() => setGeneratedImage(img)}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="flex gap-3">
                        <Button
                          onClick={downloadImage}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Télécharger
                        </Button>
                        
                        {generatedImages.length > 0 && formData.email && (
                          <Button 
                            onClick={sendMultipleImages}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                          >
                            <Mail className="w-4 h-4 mr-2" />
                            Envoyer {generatedImages.length} image{generatedImages.length > 1 ? 's' : ''}
                          </Button>
                        )}
                        
                        {formData.email && generatedImages.length === 1 && (
                          <Button variant="outline" className="flex-1">
                            <Mail className="w-4 h-4 mr-2" />
                            Envoyé par Email
                          </Button>
                        )}
                      </div>
                      
                      <div className={`text-xs text-center ${isDarkMode ? 'text-white' : 'text-slate-500'}`}>
                        Généré avec IA • Filigrane par Blandin & Delloye
                      </div>
                    </div>
                  ) : (
                    <div className={`flex flex-col items-center justify-center h-96 ${isDarkMode ? 'text-slate-400' : 'text-slate-400'}`}>
                      <Camera className="w-16 h-16 mb-4" />
                      <p className={`text-lg font-medium ${isDarkMode ? 'text-white' : ''}`}>Aucune tenue générée</p>
                      <p className={`text-sm ${isDarkMode ? 'text-white' : ''}`}>Téléchargez des photos et personnalisez les paramètres pour générer</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          isAdminAuthenticated ? <AdminView /> : (
            <div className="flex items-center justify-center h-64">
              <Card className={`border-0 shadow-xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-800/50 backdrop-blur-sm text-white' : 'bg-white/50 backdrop-blur-sm'}`}>
                <CardContent className="p-8 text-center">
                  <Settings className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                  <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>
                    Accès Administration Requis
                  </h3>
                  <p className={`text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                    Veuillez utiliser le bouton d'administration pour vous connecter.
                  </p>
                </CardContent>
              </Card>
            </div>
          )
        )}
      </main>
    </div>
  );
}

export default App;