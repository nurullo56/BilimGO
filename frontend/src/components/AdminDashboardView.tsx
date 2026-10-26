import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Coins,
  Crown,
  Eye,
  GraduationCap,
  MessageSquare,
  RefreshCw,
  ShoppingBag,
  TrendingUp,
  Users,
} from 'lucide-react';
import { AppView } from '../types';
import { AdminOverviewStats, fetchAdminOverview } from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface AdminDashboardViewProps {
  onNavigate: (view: AppView) => void;
}

export const AdminDashboardView: React.FC<AdminDashboardViewProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<AdminOverviewStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const data = await fetchAdminOverview();
      setStats(data);
    } catch (err) {
      console.error('Statistika olishda xatolik:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    triggerHaptic('light');
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3 text-tg-hint">
        <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-medium">Boshqaruv markazi yuklanmoqda...</span>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
  };

  return (
    <div className="px-4 pb-24 space-y-5 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 rounded-3xl p-5 text-white shadow-lg relative overflow-hidden">
        <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-white/10 rounded-full blur-xl pointer-events-none" />

        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => {
              triggerHaptic('selection');
              onNavigate({ type: 'profile' });
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/20 hover:bg-black/30 backdrop-blur-md text-xs font-semibold text-white transition active:scale-95 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Orqaga</span>
          </button>

          <button
            onClick={handleRefresh}
            className={`p-2 rounded-xl bg-black/20 hover:bg-black/30 backdrop-blur-md text-white transition active:scale-95 cursor-pointer ${
              refreshing ? 'animate-spin' : ''
            }`}
            title="Yangilash"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center text-2xl shadow-inner shrink-0">
            👑
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-black tracking-tight">
              Admin Boshqaruv Markazi
            </h1>
            <p className="text-xs text-amber-100 font-medium">
              Platformaning to'liq ko'rsatkichlari va tahlili
            </p>
          </div>
        </div>
      </div>

      {/* Main Metric Cards Grid (6 Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {/* 1. Jami Foydalanuvchilar */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-blue-500 mb-2">
            <Users className="w-5 h-5" />
            <span className="text-[10px] font-bold bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded-full">
              Foydalanuvchi
            </span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {stats?.total_users || 0}
          </p>
          <span className="text-[11px] text-tg-hint font-medium">Jami Ro'yxatdan o'tgan</span>
        </div>

        {/* 2. Faol Mentorlar */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-indigo-500 mb-2">
            <Crown className="w-5 h-5" />
            <span className="text-[10px] font-bold bg-indigo-500/10 text-indigo-500 px-2 py-0.5 rounded-full">
              Mentorlar
            </span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {stats?.active_mentors || 0}
          </p>
          <span className="text-[11px] text-tg-hint font-medium">Faol Kuratorlar</span>
        </div>

        {/* 3. Faol Kurslar */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-emerald-500 mb-2">
            <BookOpen className="w-5 h-5" />
            <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded-full">
              Kurslar
            </span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {stats?.active_courses || 0}
          </p>
          <span className="text-[11px] text-tg-hint font-medium">Nashr qilingan</span>
        </div>

        {/* 4. Muvaffaqiyatli Savdolar */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-amber-500 mb-2">
            <ShoppingBag className="w-5 h-5" />
            <span className="text-[10px] font-bold bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-full">
              Sotuvlar
            </span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {stats?.total_sales_count || 0}
          </p>
          <span className="text-[11px] text-tg-hint font-medium">To'langan buyurtmalar</span>
        </div>

        {/* 5. Jami Tushum (2 ustun kengligida) */}
        <div className="col-span-2 sm:col-span-2 bg-tg-section border border-tg-secondary rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-emerald-500 mb-2">
            <Coins className="w-5 h-5" />
            <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Umumiy Tushum
            </span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {formatCurrency(stats?.total_revenue || 0)}
          </p>
          <span className="text-[11px] text-tg-hint font-medium">Click va Payme orqali tushgan mablag'</span>
        </div>
      </div>

      {/* Quick Action Navigation Links */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 space-y-3 shadow-xs">
        <h3 className="text-xs font-bold text-tg-hint uppercase tracking-wider px-1">
          Tezkor Boshqaruv
        </h3>

        <div className="space-y-2">
          {/* 1. Talabalar & Mentorlar tahlili */}
          <button
            onClick={() => {
              triggerHaptic('selection');
              onNavigate({ type: 'mentor-stats' });
            }}
            className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-tg-secondary/50 hover:bg-tg-secondary text-left transition active:scale-[0.99] cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs sm:text-sm font-bold text-tg-text">
                  Talabalar va Mentorlar Tahlili
                </p>
                <p className="text-[11px] text-tg-hint">
                  Har bir kabinetdagi o'quvchilar progressini ko'rish
                </p>
              </div>
            </div>
            <span className="text-tg-hint text-sm">➔</span>
          </button>

          {/* 2. Guruh chatlari */}
          <button
            onClick={() => {
              triggerHaptic('selection');
              onNavigate({ type: 'cabinet' });
            }}
            className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-tg-secondary/50 hover:bg-tg-secondary text-left transition active:scale-[0.99] cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center shrink-0">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs sm:text-sm font-bold text-tg-text">
                  Guruh Chatlari va Kabinetlar
                </p>
                <p className="text-[11px] text-tg-hint">
                  Mentorlik kabinetlari va xabarlarni ko'rish
                </p>
              </div>
            </div>
            <span className="text-tg-hint text-sm">➔</span>
          </button>

          {/* 3. Kurslar katalogi */}
          <button
            onClick={() => {
              triggerHaptic('selection');
              onNavigate({ type: 'catalog' });
            }}
            className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-tg-secondary/50 hover:bg-tg-secondary text-left transition active:scale-[0.99] cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs sm:text-sm font-bold text-tg-text">
                  Kurslar Ro'yxati
                </p>
                <p className="text-[11px] text-tg-hint">
                  Platformada nashr qilingan barcha darsliklar
                </p>
              </div>
            </div>
            <span className="text-tg-hint text-sm">➔</span>
          </button>
        </div>
      </div>
    </div>
  );
};
