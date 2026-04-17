import React, { useState, useEffect } from 'react';
import { groupsApi } from '../services/api';

export interface Group {
    group_id: number;
    name: string;
    description: string;
    capacity: number;
    is_active: boolean;
    participant_count: number;
    created_at: string;
}

const GroupsManagementPage: React.FC = () => {
    const [groups, setGroups] = useState<Group[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchGroups();
    }, []);

    const fetchGroups = async () => {
        try {
            setLoading(true);
            const response = await groupsApi.adminList();
            setGroups(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load groups. Please ensure you have admin permissions.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActive = async (groupId: number) => {
        try {
            await groupsApi.toggleActive(groupId);
            fetchGroups(); // Refresh list
        } catch (err) {
            setError('Failed to update group status.');
            console.error(err);
        }
    };

    if (loading) return (
        <div className="flex justify-center items-center h-screen">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Group Management</h1>
                    <p className="text-gray-600">Monitor and control participant group distribution and status.</p>
                </div>
                <button 
                    onClick={fetchGroups}
                    className="btn-premium px-4 py-2"
                >
                    Refresh Data
                </button>
            </header>

            {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
                    <p className="text-red-700">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {groups.map((group) => (
                    <div key={group.group_id} className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden transition-all hover:shadow-xl">
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="text-xl font-bold text-gray-800">{group.name}</h3>
                                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${group.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                                    {group.is_active ? 'Active' : 'Inactive'}
                                </div>
                            </div>
                            
                            <p className="text-gray-600 text-sm mb-6 line-clamp-2 h-10">
                                {group.description || 'No description provided for this group.'}
                            </p>

                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-500 font-medium">Capacity Usage</span>
                                        <span className={`font-bold ${group.participant_count >= group.capacity ? 'text-red-600' : 'text-indigo-600'}`}>
                                            {group.participant_count} / {group.capacity}
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div 
                                            className={`h-2 rounded-full transition-all duration-500 ${
                                                (group.participant_count / group.capacity) > 0.9 ? 'bg-red-500' : 'bg-indigo-600'
                                            }`}
                                            style={{ width: `${Math.min((group.participant_count / group.capacity) * 100, 100)}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div className="bg-gray-50 p-4 border-t border-gray-100 flex justify-end">
                            <button
                                onClick={() => handleToggleActive(group.group_id)}
                                className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${
                                    group.is_active 
                                    ? 'bg-amber-100 text-amber-700 hover:bg-amber-200' 
                                    : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                                }`}
                            >
                                {group.is_active ? 'Deactivate Group' : 'Activate Group'}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GroupsManagementPage;
