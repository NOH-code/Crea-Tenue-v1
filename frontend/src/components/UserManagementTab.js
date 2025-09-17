import React, { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Users, Edit, Trash2, UserPlus, Shield, User, Crown } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagementTab = ({ isDarkMode, accessToken }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    role: '',
    images_limit_total: '',
    images_used_total: '',
    is_active: true
  });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error("Erreur lors du chargement des utilisateurs");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchUsers();
  }, [accessToken]);

  const handleEditUser = (user) => {
    setEditingUser(user);
    setEditForm({
      role: user.role,
      images_limit_total: user.images_limit_total.toString(),
      images_used_total: user.images_used_total.toString(),
      is_active: user.is_active
    });
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      const updateData = {
        role: editForm.role,
        images_limit_total: parseInt(editForm.images_limit_total),
        images_used_total: parseInt(editForm.images_used_total),
        is_active: editForm.is_active
      };
      
      await axios.put(`${API}/admin/users/${editingUser.id}`, updateData, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      
      toast.success("Utilisateur mis à jour avec succès");
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error("Erreur lors de la mise à jour de l'utilisateur");
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur ${userName} ?`)) {
      return;
    }
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      
      toast.success("Utilisateur supprimé avec succès");
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error("Erreur lors de la suppression de l'utilisateur");
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <Crown className="w-4 h-4" />;
      case 'user':
        return <Shield className="w-4 h-4" />;
      case 'client':
      default:
        return <User className="w-4 h-4" />;
    }
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'user':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'client':
      default:
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    }
  };

  const getStatusBadgeColor = (isActive) => {
    return isActive 
      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Chargement des utilisateurs...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Gestion des Utilisateurs
          </h2>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            {users.length} utilisateur{users.length > 1 ? 's' : ''} enregistré{users.length > 1 ? 's' : ''}
          </p>
        </div>
        
        <Button 
          onClick={fetchUsers}
          variant="outline"
          className={isDarkMode ? 'border-slate-600 text-white hover:bg-slate-700' : ''}
        >
          <Users className="w-4 h-4 mr-2" />
          Actualiser
        </Button>
      </div>

      <Card className={isDarkMode ? 'bg-slate-800 border-slate-700' : ''}>
        <CardHeader>
          <CardTitle className={isDarkMode ? 'text-white' : ''}>
            Liste des Utilisateurs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className={isDarkMode ? 'border-slate-700' : ''}>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Nom</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Email</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Rôle</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Images</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Statut</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Inscription</TableHead>
                  <TableHead className={isDarkMode ? 'text-slate-300' : ''}>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id} className={isDarkMode ? 'border-slate-700' : ''}>
                    <TableCell className={isDarkMode ? 'text-white' : ''}>
                      {user.nom}
                    </TableCell>
                    <TableCell className={isDarkMode ? 'text-white' : ''}>
                      {user.email}
                    </TableCell>
                    <TableCell>
                      <Badge className={getRoleBadgeColor(user.role)}>
                        {getRoleIcon(user.role)}
                        <span className="ml-1 capitalize">{user.role}</span>
                      </Badge>
                    </TableCell>
                    <TableCell className={isDarkMode ? 'text-white' : ''}>
                      <div className="flex flex-col">
                        <span>{user.images_used_total}/{user.images_limit_total}</span>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{
                              width: `${Math.min((user.images_used_total / user.images_limit_total) * 100, 100)}%`
                            }}
                          ></div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusBadgeColor(user.is_active)}>
                        {user.is_active ? 'Actif' : 'Inactif'}
                      </Badge>
                    </TableCell>
                    <TableCell className={`text-sm ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                      {formatDate(user.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditUser(user)}
                          className={isDarkMode ? 'border-slate-600 text-white hover:bg-slate-700' : ''}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        {user.role !== 'admin' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteUser(user.id, user.nom)}
                            className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600 dark:hover:bg-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <Dialog open={editingUser !== null} onOpenChange={() => setEditingUser(null)}>
        <DialogContent className={`sm:max-w-[425px] ${isDarkMode ? 'bg-slate-800 text-white border-slate-700' : ''}`}>
          <DialogHeader>
            <DialogTitle className={isDarkMode ? 'text-white' : ''}>
              Modifier l'utilisateur
            </DialogTitle>
            <DialogDescription className={isDarkMode ? 'text-slate-400' : ''}>
              {editingUser?.nom} ({editingUser?.email})
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="role" className="text-right">
                Rôle
              </Label>
              <Select
                value={editForm.role}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, role: value }))}
              >
                <SelectTrigger className={`col-span-3 ${isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="client">Client</SelectItem>
                  <SelectItem value="user">Utilisateur</SelectItem>
                  <SelectItem value="admin">Administrateur</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="images_limit" className="text-right">
                Limite d'images
              </Label>
              <Input
                id="images_limit"
                type="number"
                value={editForm.images_limit_total}
                onChange={(e) => setEditForm(prev => ({ ...prev, images_limit_total: e.target.value }))}
                className={`col-span-3 ${isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}`}
              />
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="images_used" className="text-right">
                Images utilisées
              </Label>
              <Input
                id="images_used"
                type="number"
                value={editForm.images_used_total}
                onChange={(e) => setEditForm(prev => ({ ...prev, images_used_total: e.target.value }))}
                className={`col-span-3 ${isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}`}
              />
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="is_active" className="text-right">
                Statut
              </Label>
              <Select
                value={editForm.is_active.toString()}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, is_active: value === 'true' }))}
              >
                <SelectTrigger className={`col-span-3 ${isDarkMode ? 'bg-slate-700 text-white border-slate-600' : ''}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Actif</SelectItem>
                  <SelectItem value="false">Inactif</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              onClick={() => setEditingUser(null)}
              className={isDarkMode ? 'border-slate-600 text-white hover:bg-slate-700' : ''}
            >
              Annuler
            </Button>
            <Button 
              onClick={handleUpdateUser}
              className={isDarkMode ? 'bg-slate-600 hover:bg-slate-500' : ''}
            >
              Sauvegarder
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagementTab;