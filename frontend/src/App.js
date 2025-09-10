import React, { useState, useEffect } from "react";
import "./App.css";
import { Upload, Camera, Palette, Send, Download, Mail, Sparkles, Crown, Star } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { Progress } from "./components/ui/progress";
import { toast, Toaster } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [options, setOptions] = useState({});
  const [formData, setFormData] = useState({
    atmosphere: '',
    suit_type: '',
    lapel_type: '',
    pocket_type: '',
    shoe_type: '',
    accessory_type: '',
    fabric_description: '',
    custom_shoe_description: '',
    custom_accessory_description: '',
    email: ''
  });
  const [modelImage, setModelImage] = useState(null);
  const [fabricImage, setFabricImage] = useState(null);
  const [modelPreview, setModelPreview] = useState(null);
  const [fabricPreview, setFabricPreview] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchOptions();
  }, []);

  const fetchOptions = async () => {
    try {
      const response = await axios.get(`${API}/options`);
      setOptions(response.data);
    } catch (error) {
      console.error("Error fetching options:", error);
      toast.error("Failed to load options");
    }
  };

  const handleFileChange = (event, type) => {
    const file = event.target.files[0];
    if (file) {
      if (type === 'model') {
        setModelImage(file);
        setModelPreview(URL.createObjectURL(file));
      } else {
        setFabricImage(file);
        setFabricPreview(URL.createObjectURL(file));
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
      toast.error("Please upload a model photo");
      return;
    }

    if (!formData.atmosphere || !formData.suit_type || !formData.lapel_type || 
        !formData.pocket_type || !formData.shoe_type || !formData.accessory_type) {
      toast.error("Please fill in all required fields");
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
        setGeneratedImage(response.data);
        toast.success("Outfit generated successfully!");
        
        if (response.data.email_sent) {
          toast.success("Image sent to your email!");
        }
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Error generating outfit:", error);
      toast.error("Failed to generate outfit. Please try again.");
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
        toast.success("Image downloaded!");
      } catch (error) {
        toast.error("Failed to download image");
      }
    }
  };

  const getAtmosphereDescription = (key) => {
    const descriptions = {
      rustic: "Rustic - Flowers and wood with floral arch",
      seaside: "Seaside - Beach ceremony with ocean backdrop", 
      chic_elegant: "Chic & Elegant - Castle hall like Versailles",
      hangover: "Hangover - Las Vegas Strip style celebration"
    };
    return descriptions[key] || key;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <Toaster position="top-right" richColors />
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-800 to-slate-600 rounded-xl flex items-center justify-center">
                <Crown className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  TailorView
                </h1>
                <p className="text-sm text-slate-500">Groom Outfit Visualizer</p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-slate-100 text-slate-700">
              <Sparkles className="w-4 h-4 mr-1" />
              AI-Powered
            </Badge>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <div className="space-y-6">
            <Card className="border-0 shadow-xl bg-white/50 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-slate-800">
                  <Camera className="w-5 h-5" />
                  Photo Upload
                </CardTitle>
                <CardDescription>Upload your model photo and optional fabric reference</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Model Image Upload */}
                <div>
                  <Label className="text-sm font-medium text-slate-700 mb-3 block">
                    Model Photo *
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
                      className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 rounded-xl hover:border-slate-400 cursor-pointer transition-colors bg-slate-50/50 hover:bg-slate-100/50"
                    >
                      {modelPreview ? (
                        <img src={modelPreview} alt="Model preview" className="w-full h-full object-cover rounded-xl" />
                      ) : (
                        <div className="text-center">
                          <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                          <p className="text-sm text-slate-600">Click to upload model photo</p>
                        </div>
                      )}
                    </label>
                  </div>
                </div>

                {/* Fabric Image Upload */}
                <div>
                  <Label className="text-sm font-medium text-slate-700 mb-3 block">
                    Fabric Reference (Optional)
                  </Label>
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
                      className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 rounded-xl hover:border-slate-400 cursor-pointer transition-colors bg-slate-50/50 hover:bg-slate-100/50"
                    >
                      {fabricPreview ? (
                        <img src={fabricPreview} alt="Fabric preview" className="w-full h-full object-cover rounded-xl" />
                      ) : (
                        <div className="text-center">
                          <Palette className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                          <p className="text-sm text-slate-600">Click to upload fabric photo</p>
                        </div>
                      )}
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-xl bg-white/50 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-slate-800">
                  <Star className="w-5 h-5" />
                  Outfit Customization
                </CardTitle>
                <CardDescription>Customize every detail of the groom's outfit</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Atmosphere */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Wedding Atmosphere *</Label>
                    <Select value={formData.atmosphere} onValueChange={(value) => handleInputChange('atmosphere', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose wedding atmosphere" />
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
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Suit Type *</Label>
                    <Select value={formData.suit_type} onValueChange={(value) => handleInputChange('suit_type', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose suit type" />
                      </SelectTrigger>
                      <SelectContent>
                        {options.suit_types?.map((type) => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Lapel Type */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Lapel Type *</Label>
                    <Select value={formData.lapel_type} onValueChange={(value) => handleInputChange('lapel_type', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose lapel type" />
                      </SelectTrigger>
                      <SelectContent>
                        {options.lapel_types?.map((type) => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Pocket Type */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Pocket Type *</Label>
                    <Select value={formData.pocket_type} onValueChange={(value) => handleInputChange('pocket_type', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose pocket type" />
                      </SelectTrigger>
                      <SelectContent>
                        {options.pocket_types?.map((type) => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Shoe Type */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Shoes *</Label>
                    <Select value={formData.shoe_type} onValueChange={(value) => handleInputChange('shoe_type', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose shoe type" />
                      </SelectTrigger>  
                      <SelectContent>
                        {options.shoe_types?.map((type) => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {formData.shoe_type === 'Custom' && (
                      <Textarea
                        placeholder="Describe your custom shoes..."
                        value={formData.custom_shoe_description}
                        onChange={(e) => handleInputChange('custom_shoe_description', e.target.value)}
                        className="mt-2"
                      />
                    )}
                  </div>

                  {/* Accessory Type */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Accessory *</Label>
                    <Select value={formData.accessory_type} onValueChange={(value) => handleInputChange('accessory_type', value)}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose accessory type" />
                      </SelectTrigger>
                      <SelectContent>
                        {options.accessory_types?.map((type) => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {formData.accessory_type === 'Custom' && (
                      <Textarea
                        placeholder="Describe your custom accessory..."
                        value={formData.custom_accessory_description}
                        onChange={(e) => handleInputChange('custom_accessory_description', e.target.value)}
                        className="mt-2"
                      />
                    )}
                  </div>

                  {/* Fabric Description */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Fabric Description</Label>
                    <Textarea
                      placeholder="Describe the fabric (e.g., eucalyptus green wool, navy pinstripe, etc.)"
                      value={formData.fabric_description}
                      onChange={(e) => handleInputChange('fabric_description', e.target.value)}
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <Label className="text-sm font-medium text-slate-700 mb-2 block">Email (Optional)</Label>
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                    />
                    <p className="text-xs text-slate-500 mt-1">Receive the generated image via email</p>
                  </div>

                  <Separator className="my-6" />

                  <Button
                    type="submit"
                    disabled={isGenerating}
                    className="w-full h-12 bg-gradient-to-r from-slate-800 to-slate-600 hover:from-slate-700 hover:to-slate-500 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
                  >
                    {isGenerating ? (
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Generating...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5" />
                        Generate Outfit
                      </div>
                    )}
                  </Button>

                  {isGenerating && (
                    <div className="space-y-2">
                      <Progress value={progress} className="w-full" />
                      <p className="text-sm text-slate-600 text-center">
                        Generating your custom outfit visualization...
                      </p>
                    </div>
                  )}
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="space-y-6">
            <Card className="border-0 shadow-xl bg-white/50 backdrop-blur-sm min-h-[600px]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-800">
                  <Star className="w-5 h-5" />
                  Generated Outfit
                </CardTitle>
                <CardDescription>Your custom groom outfit visualization</CardDescription>
              </CardHeader>
              <CardContent>
                {generatedImage ? (
                  <div className="space-y-4">
                    <div className="relative rounded-xl overflow-hidden bg-slate-100">
                      <img
                        src={`${BACKEND_URL}${generatedImage.download_url}`}
                        alt="Generated outfit"
                        className="w-full h-auto"
                      />
                    </div>
                    
                    <div className="flex gap-3">
                      <Button
                        onClick={downloadImage}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                      
                      {formData.email && (
                        <Button variant="outline" className="flex-1">
                          <Mail className="w-4 h-4 mr-2" />
                          Sent to Email
                        </Button>
                      )}
                    </div>
                    
                    <div className="text-xs text-slate-500 text-center">
                      Generated with AI • Watermarked by TailorView
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-96 text-slate-400">
                    <Camera className="w-16 h-16 mb-4" />
                    <p className="text-lg font-medium">No outfit generated yet</p>
                    <p className="text-sm">Upload photos and customize settings to generate</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;