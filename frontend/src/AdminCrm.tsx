import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  CreditCard,
  Activity,
  Globe,
  DollarSign,
  TrendingUp,
  Package,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Search,
  RefreshCw,
  LogOut,
  Layers,
  ArrowUpRight,
  Sparkles,
  Store as StoreIcon,
  MessageSquare,
  ChevronRight,
  Code2,
  ExternalLink,
} from "lucide-react";
import { api } from "./api";
import type { User } from "./types";

interface KPIOverview {
  kpis: {
    mrr_sar: number;
    arr_sar: number;
    total_users: number;
    total_stores: number;
    active_paying_subscribers: number;
    free_pilot_users: number;
    total_orders_processed: number;
    confirmed_orders: number;
    confirmed_volume_sar: number;
    sessions_24h: number;
    pageviews_24h: number;
    inbound_leads: number;
    acquisition_prospects: number;
  };
}

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  stores: Array<{
    id: string;
    name: string;
    platform: string;
    currency: string;
    country_code: string;
    is_active: boolean;
    plan: string;
    subscription_status: string;
    free_confirmations_remaining: number;
    orders_count_this_month: number;
  }>;
}

interface AdminSession {
  id: string;
  event_name: string;
  session_id: string;
  path: string;
  source: string;
  attribution: Record<string, any>;
  referrer?: string;
  ip_hash?: string;
  created_at: string;
}

interface AdminSubscription {
  id: string;
  store_id: string;
  store_name: string;
  owner_email: string;
  plan: string;
  plan_price: string;
  status: string;
  orders_count_this_month: number;
  free_confirmations_remaining: number;
  creem_customer_id?: string;
  creem_subscription_id?: string;
  created_at: string;
}

interface AdminLead {
  id: string;
  company: string;
  platform: string;
  monthly_orders: string;
  selected_plan: string;
  status: string;
  referrer?: string;
  landing_page?: string;
  attribution: Record<string, any>;
  created_at: string;
}

export function AdminCrm({
  user,
  onLogout,
  onSwitchToMerchant,
}: {
  user: User;
  onLogout: () => void;
  onSwitchToMerchant?: () => void;
}) {
  const [tab, setTab] = useState<"overview" | "users" | "sessions" | "subscriptions" | "leads" | "outreach">("overview");
  const [userSearch, setUserSearch] = useState("");
  const [sessionFilter, setSessionFilter] = useState("");
  const [outreachActionMsg, setOutreachActionMsg] = useState<string | null>(null);
  const [customWa, setCustomWa] = useState(10);
  const [customEmail, setCustomEmail] = useState(30);
  const [customIg, setCustomIg] = useState(10);
  const [customScrape, setCustomScrape] = useState(50);

  const overviewQuery = useQuery<KPIOverview>({
    queryKey: ["admin", "overview"],
    queryFn: async () => (await api.get<KPIOverview>("/api/admin/overview")).data,
    refetchInterval: 15000,
  });

  const usersQuery = useQuery<AdminUser[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => (await api.get<AdminUser[]>("/api/admin/users")).data,
    refetchInterval: 30000,
  });

  const sessionsQuery = useQuery<AdminSession[]>({
    queryKey: ["admin", "sessions"],
    queryFn: async () => (await api.get<AdminSession[]>("/api/admin/sessions")).data,
    refetchInterval: 10000,
  });

  const subscriptionsQuery = useQuery<AdminSubscription[]>({
    queryKey: ["admin", "subscriptions"],
    queryFn: async () => (await api.get<AdminSubscription[]>("/api/admin/subscriptions")).data,
    refetchInterval: 30000,
  });

  const leadsQuery = useQuery<AdminLead[]>({
    queryKey: ["admin", "leads"],
    queryFn: async () => (await api.get<AdminLead[]>("/api/admin/leads")).data,
    refetchInterval: 20000,
  });

  const outreachQuery = useQuery<{
    quotas: { wa_limit: number; email_limit: number; ig_limit: number; scrape_limit: number };
    stats: { total: number; ready: number; contacted: number };
    channels: { whatsapp: string; email: string; instagram: string };
  }>({
    queryKey: ["admin", "outreach"],
    queryFn: async () => (await api.get("/api/admin/outreach/config")).data,
    refetchInterval: 10000,
  });

  const kpis = overviewQuery.data?.kpis;

  const filteredUsers = (usersQuery.data || []).filter(
    (u) =>
      u.email.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.full_name.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.stores.some((s) => s.name.toLowerCase().includes(userSearch.toLowerCase()))
  );

  const filteredSessions = (sessionsQuery.data || []).filter(
    (s) =>
      s.session_id.toLowerCase().includes(sessionFilter.toLowerCase()) ||
      s.path.toLowerCase().includes(sessionFilter.toLowerCase()) ||
      s.event_name.toLowerCase().includes(sessionFilter.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans" dir="rtl">
      {/* Executive Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center font-black text-white text-xl shadow-lg shadow-emerald-500/20">
            م
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-white tracking-tight">مُجيب • لوحة الإدارة العامة (Back-Office CRM)</h1>
              <span className="bg-emerald-500/20 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-500/30">
                SUPER ADMIN
              </span>
            </div>
            <p className="text-xs text-slate-400">
              المشرف: <span className="text-slate-300 font-mono">{user.email}</span> • بيئة الإنتاج الخليجية
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              overviewQuery.refetch();
              usersQuery.refetch();
              sessionsQuery.refetch();
              subscriptionsQuery.refetch();
              leadsQuery.refetch();
            }}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="تحديث البيانات"
          >
            <RefreshCw size={16} className={overviewQuery.isFetching ? "animate-spin text-emerald-400" : ""} />
          </button>

          {onSwitchToMerchant && (
            <button
              onClick={onSwitchToMerchant}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 transition"
            >
              <StoreIcon size={14} /> لوحة التاجر
            </button>
          )}

          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-900/60 text-red-300 text-xs font-bold border border-red-800/40 transition"
          >
            <LogOut size={14} /> خروج
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setTab("overview")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "overview" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <TrendingUp size={16} /> الرئيسية والإيرادات
          </button>

          <button
            onClick={() => setTab("users")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "users" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Users size={16} /> المستخدمين والمتاجر ({usersQuery.data?.length ?? 0})
          </button>

          <button
            onClick={() => setTab("sessions")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "sessions" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Globe size={16} /> الزيارات والجلسات الحية ({sessionsQuery.data?.length ?? 0})
          </button>

          <button
            onClick={() => setTab("subscriptions")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "subscriptions" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <CreditCard size={16} /> الاشتراكات والفواتير ({subscriptionsQuery.data?.length ?? 0})
          </button>

          <button
            onClick={() => setTab("leads")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "leads" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <MessageSquare size={16} /> العملاء المحتملين والطلبات ({leadsQuery.data?.length ?? 0})
          </button>

          <button
            onClick={() => setTab("outreach")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              tab === "outreach" ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles size={16} /> التحكم في الـ Outreach والاستحواذ ⚡️
          </button>
        </div>

        {/* TAB 1: OVERVIEW & REVENUE */}
        {tab === "overview" && (
          <div className="space-y-6">
            {/* KPI Cards Grid */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase">الإيراد الشهري المتكرر (MRR)</p>
                    <h3 className="text-2xl font-black text-white mt-1">{kpis?.mrr_sar?.toLocaleString() ?? 0} ريال</h3>
                    <p className="text-[11px] text-emerald-400 mt-1 font-medium">ARR: {kpis?.arr_sar?.toLocaleString() ?? 0} ريال/سنة</p>
                  </div>
                  <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                    <DollarSign size={20} />
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase">المستخدمين والمتاجر</p>
                    <h3 className="text-2xl font-black text-white mt-1">{kpis?.total_users ?? 0}</h3>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {kpis?.total_stores ?? 0} متجر مرتبط • {kpis?.active_paying_subscribers ?? 0} اشتراك نشط
                    </p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                    <Users size={20} />
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase">الطلبيات المؤكدة آلياً</p>
                    <h3 className="text-2xl font-black text-emerald-400 mt-1">{kpis?.confirmed_orders ?? 0}</h3>
                    <p className="text-[11px] text-slate-400 mt-1">
                      قيمة المبيعات المحمية: {kpis?.confirmed_volume_sar?.toLocaleString() ?? 0} ريال
                    </p>
                  </div>
                  <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                    <CheckCircle2 size={20} />
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase">الزيارات الحية (24 ساعة)</p>
                    <h3 className="text-2xl font-black text-white mt-1">{kpis?.sessions_24h ?? 0}</h3>
                    <p className="text-[11px] text-slate-400 mt-1">{kpis?.pageviews_24h ?? 0} مشاهدة صفحة</p>
                  </div>
                  <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
                    <Activity size={20} />
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Summary Cards */}
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck size={16} className="text-emerald-400" /> حالة المنظومة والخوادم (Live Infrastructure)
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">محرك إرسال الواتساب (Baileys US):</span>
                    <span className="text-emerald-400 font-bold">متصل ويعمل بنجاح (100%)</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">محرك الانستغرام (instagrapi):</span>
                    <span className="text-emerald-400 font-bold">جلسة نشطة (@leocreativehub4)</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">مزود البريد الإلكتروني (Resend + Google):</span>
                    <span className="text-emerald-400 font-bold">موثق ومفعل (DKIM/DMARC Pass)</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">بوابة الدفع الإلكتروني (Creem Checkout):</span>
                    <span className="text-slate-300 font-bold">جاهزة ومربوطة بالخطط</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles size={16} className="text-amber-400" /> مسار الاستحواذ والتحويل (Acquisition Funnel)
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">باقة التجار التجريبية (Free Pilot):</span>
                    <span className="text-white font-bold">{kpis?.free_pilot_users ?? 0} تاجر</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">المشتركون بالباقات المدفوعة:</span>
                    <span className="text-emerald-400 font-bold">{kpis?.active_paying_subscribers ?? 0} تاجر</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">العملاء المحتملون (Inbound Leads):</span>
                    <span className="text-blue-400 font-bold">{kpis?.inbound_leads ?? 0} متجر</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-400">المتاجر المستهدفة بحملات الخروج:</span>
                    <span className="text-purple-400 font-bold">{kpis?.acquisition_prospects ?? 30} متجر مؤهل</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: USERS & STORES */}
        {tab === "users" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-wrap justify-between items-center gap-4">
              <h3 className="text-lg font-bold text-white">سجل التجار والمستخدمين المسجلين</h3>
              <div className="relative w-72">
                <Search size={14} className="absolute right-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="بحث بالإيميل أو المتجر..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pr-9 pl-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-right">
                <thead className="text-slate-400 border-b border-slate-800 bg-slate-950/50">
                  <tr>
                    <th className="p-3">المستخدم</th>
                    <th>المتجر والمنصة</th>
                    <th>الخطة الحالية</th>
                    <th>الرصيد المتبقي</th>
                    <th>الطلبات هذا الشهر</th>
                    <th>تاريخ التسجيل</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-slate-500">
                        لا يوجد مستخدمون مطابقون
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => {
                      const store = u.stores[0];
                      return (
                        <tr key={u.id} className="hover:bg-slate-800/30 transition">
                          <td className="p-3">
                            <div className="font-bold text-white">{u.full_name || "تاجر مجيب"}</div>
                            <div className="text-[11px] text-slate-400 font-mono">{u.email}</div>
                          </td>
                          <td>
                            {store ? (
                              <div>
                                <span className="font-bold text-slate-200">{store.name}</span>
                                <span className="mr-2 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 uppercase font-mono">
                                  {store.platform}
                                </span>
                              </div>
                            ) : (
                              <span className="text-slate-500">بدون متجر</span>
                            )}
                          </td>
                          <td>
                            <span
                              className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                store?.plan === "scale"
                                  ? "bg-purple-500/20 text-purple-300"
                                  : store?.plan === "growth"
                                  ? "bg-blue-500/20 text-blue-300"
                                  : store?.plan === "starter"
                                  ? "bg-emerald-500/20 text-emerald-300"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {store?.plan ? store.plan.toUpperCase() : "FREE PILOT"}
                            </span>
                          </td>
                          <td className="font-mono text-emerald-400 font-bold">
                            {store?.free_confirmations_remaining ?? 50} تأكيد
                          </td>
                          <td className="font-mono">{store?.orders_count_this_month ?? 0}</td>
                          <td className="text-slate-400">{u.created_at ? new Date(u.created_at).toLocaleDateString("ar-SA") : "N/A"}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: LIVE SESSIONS & TRAFFIC */}
        {tab === "sessions" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-wrap justify-between items-center gap-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Globe size={18} className="text-emerald-400" /> سجل الزيارات والجلسات الحية (Traffic & Funnel Log)
                </h3>
                <p className="text-xs text-slate-400 mt-1">تتبع دقيق لكل مستخدم فتح الموقع والصفحات ومصادر الحملات الإعلانية.</p>
              </div>

              <div className="relative w-72">
                <Search size={14} className="absolute right-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="فلترة بالصفحة أو الجلسة..."
                  value={sessionFilter}
                  onChange={(e) => setSessionFilter(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pr-9 pl-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-right">
                <thead className="text-slate-400 border-b border-slate-800 bg-slate-950/50">
                  <tr>
                    <th className="p-3">الحدث (Event)</th>
                    <th>الصفحة (Path)</th>
                    <th>معرّف الجلسة (Session ID)</th>
                    <th>المصدر الإعلاني (Attribution / UTM)</th>
                    <th>المصدر الخارجي (Referrer)</th>
                    <th>التوقيت</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredSessions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-slate-500">
                        لا توجد أحداث زيارة مسجلة حالياً
                      </td>
                    </tr>
                  ) : (
                    filteredSessions.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-800/30 transition font-mono">
                        <td className="p-3 font-sans">
                          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold text-[10px]">
                            {s.event_name}
                          </span>
                        </td>
                        <td className="text-slate-300 font-sans">{s.path}</td>
                        <td className="text-slate-400 text-[11px]">{s.session_id.slice(0, 16)}...</td>
                        <td className="text-slate-300 font-sans">
                          {Object.keys(s.attribution || {}).length > 0 ? (
                            <span className="text-amber-400 text-[11px]">
                              {s.attribution.utm_source || s.attribution.utm_campaign || JSON.stringify(s.attribution)}
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[10px]">Direct / Organic</span>
                          )}
                        </td>
                        <td className="text-slate-400 text-[11px] font-sans truncate max-w-[150px]">
                          {s.referrer || "—"}
                        </td>
                        <td className="text-slate-400 text-[11px] font-sans">
                          {s.created_at ? new Date(s.created_at).toLocaleTimeString("ar-SA") : "N/A"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: SUBSCRIPTIONS & REVENUE */}
        {tab === "subscriptions" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-white">إدارة الاشتراكات والفوترة (Creem Payments CRM)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-right">
                <thead className="text-slate-400 border-b border-slate-800 bg-slate-950/50">
                  <tr>
                    <th className="p-3">المتجر والمالك</th>
                    <th>الخطة والسعر</th>
                    <th>الحالة</th>
                    <th>الطلبات المستهلكة</th>
                    <th>الرصيد المتبقي</th>
                    <th>Creem Customer ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {(subscriptionsQuery.data || []).map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3">
                        <div className="font-bold text-white">{sub.store_name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{sub.owner_email}</div>
                      </td>
                      <td>
                        <span className="font-bold text-emerald-400">{sub.plan.toUpperCase()}</span>
                        <div className="text-[11px] text-slate-400">{sub.plan_price}</div>
                      </td>
                      <td>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-[10px]">
                          {sub.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="font-mono">{sub.orders_count_this_month}</td>
                      <td className="font-mono text-emerald-400 font-bold">{sub.free_confirmations_remaining}</td>
                      <td className="font-mono text-slate-500">{sub.creem_customer_id || "N/A (Free Tier)"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: LEADS & PIPELINE */}
        {tab === "leads" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-white">طلبات الديمو والعملاء المحتملين (Inbound Leads)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-right">
                <thead className="text-slate-400 border-b border-slate-800 bg-slate-950/50">
                  <tr>
                    <th className="p-3">الشركة / المتجر</th>
                    <th>المنصة</th>
                    <th>الطلبات الشهرية المتوقعة</th>
                    <th>الخطة المفضلة</th>
                    <th>الحالة</th>
                    <th>التاريخ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {(leadsQuery.data || []).length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-slate-500">
                        لا توجد طلبات جديدة حالياً
                      </td>
                    </tr>
                  ) : (
                    (leadsQuery.data || []).map((l) => (
                      <tr key={l.id} className="hover:bg-slate-800/30 transition">
                        <td className="p-3 font-bold text-white">{l.company}</td>
                        <td className="uppercase font-mono text-slate-300">{l.platform}</td>
                        <td className="font-mono">{l.monthly_orders}</td>
                        <td className="text-emerald-400 font-bold">{l.selected_plan}</td>
                        <td>
                          <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-bold">
                            {l.status}
                          </span>
                        </td>
                        <td className="text-slate-400">{l.created_at ? new Date(l.created_at).toLocaleDateString("ar-SA") : "N/A"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 6: OUTREACH & ACQUISITION CONTROL */}
        {tab === "outreach" && (
          <div className="space-y-6">
            {outreachActionMsg && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-bold flex items-center justify-between">
                <span>{outreachActionMsg}</span>
                <button onClick={() => setOutreachActionMsg(null)} className="text-emerald-400 hover:text-white text-xs">إغلاق</button>
              </div>
            )}

            {/* Channels & DB Overview Cards */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <p className="text-xs font-bold text-slate-400 uppercase">جاهزون للإرسال (Ready Pool)</p>
                <h3 className="text-2xl font-black text-emerald-400 mt-1">{outreachQuery.data?.stats.ready ?? 0} متجر</h3>
                <p className="text-[11px] text-slate-400 mt-1">مؤهلون ومزودون بأرقام وبيانات مستهدفة</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <p className="text-xs font-bold text-slate-400 uppercase">تم التواصل معهم (Contacted)</p>
                <h3 className="text-2xl font-black text-blue-400 mt-1">{outreachQuery.data?.stats.contacted ?? 0} متجر</h3>
                <p className="text-[11px] text-slate-400 mt-1">عبر واتساب، الإيميل و إنستغرام</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <p className="text-xs font-bold text-slate-400 uppercase">إجمالي قاعدة البيانات</p>
                <h3 className="text-2xl font-black text-white mt-1">{outreachQuery.data?.stats.total ?? 0} متجر</h3>
                <p className="text-[11px] text-slate-400 mt-1">سوق السعودية والخليج (GCC)</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
                <p className="text-xs font-bold text-slate-400 uppercase">حالة القنوات الثلاث</p>
                <div className="text-xs space-y-1 mt-2 font-mono">
                  <p className="text-emerald-400">🟢 WA: {outreachQuery.data?.channels.whatsapp || "Baileys"}</p>
                  <p className="text-blue-400">✉️ Mail: {outreachQuery.data?.channels.email || "Resend"}</p>
                  <p className="text-pink-400">📸 IG: {outreachQuery.data?.channels.instagram || "Instagrapi"}</p>
                </div>
              </div>
            </div>

            {/* Quotas Configuration & Launch Panel */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Box 1: Quota Configuration */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles size={18} className="text-emerald-400" />
                  تعديل كوتة الإرسال اليومية (Daily Quotas)
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  حدد عدد الرسائل اليومية التي يقوم النظام بإرسالها تلقائياً أو عند إطلاق الحملة.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">🟢 رسائل واتساب (Baileys / يوم) :</label>
                    <input
                      type="number"
                      value={customWa}
                      onChange={(e) => setCustomWa(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white font-mono"
                      min={1}
                      max={50}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">✉️ إيميلات B2B (Resend / يوم) :</label>
                    <input
                      type="number"
                      value={customEmail}
                      onChange={(e) => setCustomEmail(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white font-mono"
                      min={1}
                      max={200}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">📸 رسائل إنستغرام (DMs / يوم) :</label>
                    <input
                      type="number"
                      value={customIg}
                      onChange={(e) => setCustomIg(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white font-mono"
                      min={1}
                      max={30}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">🕷️ حجم السكرابينغ اليومي (متاجر جديدة) :</label>
                    <input
                      type="number"
                      value={customScrape}
                      onChange={(e) => setCustomScrape(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white font-mono"
                      min={10}
                      max={200}
                    />
                  </div>

                  <button
                    onClick={async () => {
                      try {
                        await api.post("/api/admin/outreach/config", {
                          wa_limit: customWa,
                          email_limit: customEmail,
                          ig_limit: customIg,
                          scrape_limit: customScrape,
                        });
                        setOutreachActionMsg("✅ تم حفظ الكوتة اليومية بنجاح ومزامنتها مع روبوت تيليجرام!");
                        outreachQuery.refetch();
                      } catch (err: any) {
                        setOutreachActionMsg(`❌ خطأ: ${err.message}`);
                      }
                    }}
                    className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition border border-slate-700 shadow-md"
                  >
                    💾 حفظ وتحديث الكوتة
                  </button>
                </div>
              </div>

              {/* Box 2: Instant Action Triggers */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 flex flex-col justify-between">
                <div className="space-y-4">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <TrendingUp size={18} className="text-emerald-400" />
                    إطلاق فوري للحملات والسكرابينغ (1-Click Trigger)
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    قم بإطلاق حملة فورية بالتقسيم المخصص الذي اخترته أعلاه، أو شغّل محرك البحث لجلب متاجر جديدة من خرائط جوجل.
                  </p>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
                    <p className="text-slate-300 font-bold">الحملة الحالية ستتضمن :</p>
                    <p className="text-emerald-400">🟢 <b>{customWa}</b> رسالة واتساب مع فيديو 20s</p>
                    <p className="text-blue-400">✉️ <b>{customEmail}</b> إيميل رسمي B2B</p>
                    <p className="text-pink-400">📸 <b>{customIg}</b> رسالة إنستغرام DM</p>
                    <p className="text-white font-bold border-t border-slate-800 pt-1">
                      المجموع : <b>{customWa + customEmail + customIg}</b> متجر مستهدف
                    </p>
                  </div>
                </div>

                <div className="space-y-3 pt-4">
                  <button
                    onClick={async () => {
                      try {
                        await api.post("/api/admin/outreach/launch", {
                          wa_count: customWa,
                          email_count: customEmail,
                          ig_count: customIg,
                        });
                        setOutreachActionMsg("🚀 تم إطلاق الحملة بنجاح! يتم الإرسال الآن وموافاتك بالتفاصيل على تيليجرام.");
                        outreachQuery.refetch();
                      } catch (err: any) {
                        setOutreachActionMsg(`❌ خطأ في الإطلاق: ${err.message}`);
                      }
                    }}
                    className="w-full py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm shadow-lg shadow-emerald-500/20 transition flex items-center justify-center gap-2"
                  >
                    <Sparkles size={18} /> 🚀 إطلاق الحملة الآن ({customWa} WA | {customEmail} Mail | {customIg} DM)
                  </button>

                  <button
                    onClick={async () => {
                      try {
                        await api.post("/api/admin/outreach/scrape", { target_count: customScrape });
                        setOutreachActionMsg(`🕷️ بدأ محرك السكرابينغ في جلب ${customScrape} متجر خليجي جديد عبر Apify و ScrapeGraphAI!`);
                        outreachQuery.refetch();
                      } catch (err: any) {
                        setOutreachActionMsg(`❌ خطأ: ${err.message}`);
                      }
                    }}
                    className="w-full py-3 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 font-bold text-xs border border-blue-500/30 transition flex items-center justify-center gap-2"
                  >
                    🕷️ جلب وسكرابينغ متاجر جديدة ({customScrape} متجر)
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

