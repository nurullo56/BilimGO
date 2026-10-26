import React, { useEffect, useState } from 'react';

export const AdminDashboardView: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/admin/analytics/overview')
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Statistika olishda xatolik:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        <span>Yuklanmoqda...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 pb-24">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">👑</span>
        <div>
          <h1 className="text-xl font-bold">Admin Boshqaruv Paneli</h1>
          <p className="text-xs text-slate-400">Platforma umumiy ko'rsatkichlari</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <span className="text-slate-400 text-xs">Jami Foydalanuvchilar</span>
          <p className="text-2xl font-bold text-blue-400 mt-1">{stats?.total_users || 0}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <span className="text-slate-400 text-xs">Aktiv Kurslar</span>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{stats?.active_courses || 0}</p>
        </div>
      </div>
    </div>
  );
};
