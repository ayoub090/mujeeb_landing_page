import {useEffect, useRef, useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {
  BarChart3, Boxes, CheckCircle2, Clipboard, Code2, CreditCard, Link2,
  Download, LockKeyhole, LogOut, MessageCircle, PackageCheck, ShieldCheck, Sparkles,
  Trash2, TriangleAlert, ChevronRight, X, ArrowRightLeft, ShieldAlert, BadgePercent, HelpCircle,
  Zap, Coins, FileText, Search, Star, MapPin, Store
} from "lucide-react";
import {api} from "./api";
import {AdminCrm} from "./AdminCrm";
import {launchEmbeddedSignup} from "./meta";
import type {Order, Summary, User} from "./types";

const statusLabel: Record<string,string> = {
  pending:"جديد", awaiting_customer:"بانتظار العميل", confirmed:"مؤكد",
  cancelled:"ملغي", human_follow_up:"متابعة بشرية", shipped:"تم الشحن",
  delivered:"تم التسليم", returned:"مرتجع",
};

// 12/10 Conversion Landing Page + Interactive Auth modal
function Auth({onDone}:{onDone:()=>void}) {
  const shopifyInstall = new URLSearchParams(location.search).get("shopify") === "ready";
  const shopifyDomain = new URLSearchParams(location.search).get("shop") || "";
  const [mode,setMode]=useState<"login"|"register">(shopifyInstall ? "register" : "login");
  const [modalOpen,setModalOpen]=useState(shopifyInstall);
  const [error,setError]=useState("");

  // ROI Calculator States
  const [calcOrders, setCalcOrders] = useState(350);
  const [calcAov, setCalcAov] = useState(280);
  const [calcRto, setCalcRto] = useState(25);
  const [calcShipping, setCalcShipping] = useState(35);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError("");
    try { 
      await api.post(`/api/auth/${mode}`, Object.fromEntries(new FormData(e.currentTarget)));
      if (shopifyInstall) {
        await api.post("/api/integrations/shopify/claim", {});
        history.replaceState({}, "", "/dashboard/integrations?connected=shopify");
      }
      if (mode === "register") (window as any).twq?.("event", "tw-re98e-reaq4", {});
      onDone(); 
    }
    catch (err: any) { 
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (typeof detail === 'string' ? detail : "تأكد من صحة البيانات المدخلة"));
    }
  };

  // ROI Math
  const failedOrders = Math.round(calcOrders * (calcRto / 100));
  const packagingFee = 10;
  const lostShippingBefore = failedOrders * (calcShipping * 2 + packagingFee);
  const lostProductSales = failedOrders * calcAov;
  const totalCurrentLoss = lostShippingBefore + lostProductSales;

  // Assuming Mujeeb drops RTO to 12%
  const targetRto = 12;
  const savedOrders = Math.max(0, Math.round(calcOrders * ((calcRto - targetRto) / 100)));
  const savedShippingFees = savedOrders * (calcShipping * 2 + packagingFee);
  const recoveredSales = savedOrders * calcAov;
  const totalSavedRevenue = savedShippingFees + recoveredSales;

  const openAuth = (authMode: "login" | "register") => {
    setMode(authMode);
    setModalOpen(true);
  };

  return (
    <div className="mesh min-h-screen text-ink" dir="rtl">
      {/* Dynamic Sticky Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <a href="#" className="text-2xl font-black text-blue-deep flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-mint to-emerald-700 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-mint/20">م</div>
            مُجيب
          </a>
          <ul className="hidden md:flex gap-6 text-sm font-semibold text-slate-600">
            <li><a href="#problem" className="hover:text-sky transition-colors">المشكلة</a></li>
            <li><a href="#features" className="hover:text-sky transition-colors">المميزات</a></li>
            <li><a href="#demos" className="hover:text-sky transition-colors">شاهد الديمو</a></li>
            <li><a href="#how-it-works" className="hover:text-sky transition-colors">كيف يعمل</a></li>
            <li><a href="#calculator" className="hover:text-sky transition-colors">حاسبة التوفير</a></li>
            <li><a href="#pricing" className="hover:text-sky transition-colors">الأسعار</a></li>
          </ul>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => openAuth("login")} className="text-sm font-bold text-blue-deep hover:text-sky px-3 py-2 transition-colors">تسجيل الدخول</button>
          <button onClick={() => openAuth("register")} className="rounded-xl btn-gold text-sm font-black px-5 py-2.5 shadow-md">ابدأ مجاناً</button>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="pt-32 pb-20 px-6 max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold shadow-sm">
            <Sparkles size={14} className="text-gold animate-pulse" />
            <span>نظام إيرادات واتساب الذكي الأول للمتاجر الخليجية</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-blue-deep leading-tight">
            استرجع أرباحك الضائعة من <span className="text-transparent bg-clip-text bg-gradient-to-l from-emerald-600 to-teal-800">الدفع عند الاستلام</span> تلقائياً وبذكاء
          </h1>
          <p className="text-slate-600 text-lg leading-relaxed max-w-xl">
            مجيب يؤكد طلبات الدفع عند الاستلام (COD)، يجمع مواقع GPS الدقيقة للعملاء، ويخفّض المرتجعات RTO من 30% إلى 12% دون تغيير شركة شحنك.
          </p>
          <div className="flex flex-wrap gap-4 pt-2">
            <button onClick={() => openAuth("register")} className="rounded-xl btn-gold text-lg font-black px-8 py-4 shadow-xl hover:shadow-2xl shadow-emerald-500/10">
              ابدأ تجربتك المجانية (50 طلب)
            </button>
            <a href="#demos" className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-ink font-bold px-8 py-4 flex items-center justify-center gap-2">
              شاهد كيف يعمل خلال 30 ثانية
            </a>
          </div>
          <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-100 text-slate-500">
            <div>
              <p className="text-2xl font-black text-blue-deep">&lt; 30 ثانية</p>
              <p className="text-xs">سرعة تأكيد الطلب وتحديد الموقع</p>
            </div>
            <div>
              <p className="text-2xl font-black text-blue-deep">GPS دقيق</p>
              <p className="text-xs">تحديث العنوان تلقائياً للشحن</p>
            </div>
            <div>
              <p className="text-2xl font-black text-blue-deep">50 طلباً</p>
              <p className="text-xs">تجربة مجانية لقياس الأثر قبل الاشتراك</p>
            </div>
          </div>
        </div>

        <div id="how-it-works" className="lg:col-span-5">
          <div className="bg-white rounded-3xl p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-5">
              <div><p className="text-xs font-black text-emerald-700">مسار البداية</p><h2 className="mt-1 text-xl font-black text-blue-deep">جاهز خلال 3 دقائق</h2></div>
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-emerald-50 text-emerald-700"><CheckCircle2 size={23}/></div>
            </div>
            <ol className="mt-5 space-y-3">
              <li className="flex gap-3 rounded-2xl bg-slate-50 p-4"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-blue-deep text-sm font-black text-white">1</span><div><b className="text-sm">اربط متجرك</b><p className="mt-1 text-xs leading-5 text-slate-500">Shopify، سلة، زد، أو متجر مخصص.</p></div></li>
              <li className="flex gap-3 rounded-2xl bg-slate-50 p-4"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-emerald-600 text-sm font-black text-white">2</span><div><b className="text-sm">امسح رمز WhatsApp</b><p className="mt-1 text-xs leading-5 text-slate-500">من الأجهزة المرتبطة على هاتفك، بلا إعدادات معقدة.</p></div></li>
              <li className="flex gap-3 rounded-2xl bg-slate-50 p-4"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-slate-800 text-sm font-black text-white">3</span><div><b className="text-sm">ابدأ 50 تأكيداً مجاناً</b><p className="mt-1 text-xs leading-5 text-slate-500">تابع التأكيد والموقع وحالة الشحن من لوحة واحدة.</p></div></li>
            </ol>
            <button onClick={() => openAuth("register")} className="mt-5 w-full rounded-xl btn-gold p-3 font-black">ربط متجري مجاناً</button>
          </div>
        </div>
      </header>

      {/* Product demos: video assets will be added without changing this layout. */}
      <section id="demos" className="bg-slate-50 py-20 px-6 border-y border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-xs font-black uppercase tracking-widest text-sky">ديموهات مجيب</span>
            <h2 className="text-3xl font-black text-blue-deep mt-3">شاهد كيف تبدأ خلال 3 دقائق</h2>
            <p className="text-slate-500 mt-3">اختر متجرك، اربط WhatsApp بمسح رمز QR، ثم ابدأ أول 50 تأكيد طلب مجاناً.</p>
          </div>
          <div className="grid lg:grid-cols-2 gap-6">
            <DemoCard title="كيف يعمل مجيب في 30 ثانية" duration="35 ثانية" src="/videos/video1_onboarding.mp4" poster="/videos/video1_onboarding-poster.jpg" transcript="اربط متجرك على سلة أو زد في ثوانٍ برمز API الخاص بك، امسح رمز الواتساب... ومبارك عليك! نظام مُجيب صار جاهز لتأكيد أول 50 طلب لمتجرك مجاناً وبدون أي تعقيد." onStart={()=>openAuth("register")} />
            <DemoCard title="عرض توضيحي مباشر" duration="48 ثانية" src="/videos/video2_workflow.mp4" poster="/videos/video2_workflow-poster.jpg" transcript="بمجرد تسجيل العميل لطلب دفع عند الاستلام، يتولى مُجيب المحادثة فوراً بلهجة سعودية طبيعية. يؤكد الطلب، يسحب لوكيشن الـ GPS بدقة، ويحدث حالة الطلب في متجرك تلقائياً. تأكيد أسرع، ومرتجعات أقل." onStart={()=>openAuth("register")} />
          </div>
        </div>
      </section>

      {/* The Problem Section */}
      <section id="problem" className="bg-white py-20 px-6 border-y border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">لماذا تفقد متاجر الخليج 30% من أرباحها؟</h2>
            <p className="text-slate-500">طرق تأكيد طلبات الدفع عند الاستلام التقليدية تدمر هوامش الربح وتستنزف وقت الفريق.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <article className="bg-slate-50 border border-slate-100 rounded-3xl p-8 space-y-5">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center"><ShieldAlert size={24} /></div>
              <h3 className="text-xl font-bold text-blue-deep">الفوضى اليدوية التقليدية (قبل مجيب)</h3>
              <ul className="space-y-3 text-slate-600 text-sm">
                <li className="flex items-start gap-2">❌ <span className="font-medium">تكاليف شحن ذهاب وعودة للمشترين الوهميين.</span></li>
                <li className="flex items-start gap-2">❌ <span className="font-medium">ساعات طويلة تضيع يومياً في مكالمات التأكيد.</span></li>
                <li className="flex items-start gap-2">❌ <span className="font-medium">عدم الرد من العملاء يعلق الطلبات لأيام.</span></li>
                <li className="flex items-start gap-2">❌ <span className="font-medium">نسب مرتجعات RTO كارثية تصل إلى 30% وأكثر.</span></li>
              </ul>
            </article>

            <article className="bg-emerald-950 text-white rounded-3xl p-8 space-y-5 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl"></div>
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-mint flex items-center justify-center"><CheckCircle2 size={24} /></div>
              <h3 className="text-xl font-bold">التأكيد التلقائي بذكاء 180IQ (مع مجيب)</h3>
              <ul className="space-y-3 text-emerald-100 text-sm">
                <li className="flex items-start gap-2">✅ <span className="font-medium">إلغاء فوري وتلقائي للطلبات الوهمية قبل الشحن والتغليف.</span></li>
                <li className="flex items-start gap-2">✅ <span className="font-medium">تواصل فوري عبر الواتساب يعطي العميل خيار تأكيد بضغطة زر.</span></li>
                <li className="flex items-start gap-2">✅ <span className="font-medium">جمع مواقع GPS دقيقة لضمان تسليم الشحنات بنسبة 100%.</span></li>
                <li className="flex items-start gap-2">✅ <span className="font-medium">انخفاض نسبة المرتجعات لأقل من 12%؛ لتوفر آلاف الريالات.</span></li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      {/* Core Mujeeb SaaS Services Grid */}
      <section id="features" className="py-20 px-6 bg-slate-50/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <span className="text-xs text-sky font-black uppercase tracking-widest block">الخدمات والميزات المتكاملة</span>
            <h2 className="text-3xl font-black text-blue-deep">منظومة ذكية متكاملة لحماية وإدارة طلبياتك</h2>
            <p className="text-slate-500 text-sm">كل ما تحتاجه لتأكيد الطلبات، توضيح العناوين، ومتابعة حالة الشحن من مكان واحد.</p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            
            {/* Service 1 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><Link2 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">ربط المتاجر بضغطة زر</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">ربط سريع وآمن</p>
              <p className="text-xs text-slate-500 leading-relaxed">ربط رسمي وسريع مع منصات سلة (Salla) وزد (Zid) وشوبيفاي (Shopify) لسحب وإدارة الطلبات فوراً.</p>
            </article>

            {/* Service 2 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><MessageCircle size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">ربط WhatsApp Business بسهولة</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">امسح رمز QR وابدأ خلال دقائق</p>
              <p className="text-xs text-slate-500 leading-relaxed">اربط رقم WhatsApp الخاص بمتجرك في خطوة واحدة، ثم ابدأ تأكيد الطلبات مباشرة.</p>
            </article>

            {/* Service 3 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><CheckCircle2 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">تأكيد الطلبات التلقائي</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">تأكيد تلقائي للطلبات</p>
              <p className="text-xs text-slate-500 leading-relaxed">يتولى البوت التفاعل الفوري مع عملائك بالواتساب لتأكيد طلبيات الدفع عند الاستلام وفلترة الوهميين.</p>
            </article>

            {/* Service 4 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><MapPin size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">التحقق الجغرافي وتحديث العناوين</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">تحديث العنوان تلقائياً</p>
              <p className="text-xs text-slate-500 leading-relaxed">يجمع البوت إحداثيات GPS ويكتبها مباشرة في تفاصيل الشحن بسلة/زد لتتمكن من طباعة بوليصة التوصيل فورا.</p>
            </article>

            {/* Service 5 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><BadgePercent size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">عروض البيع الإضافي (Upsell)</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">عرض ذكي بعد التأكيد</p>
              <p className="text-xs text-slate-500 leading-relaxed">اقتراح عروض إضافية ذكية للعميل تلقائياً في الواتساب فور تأكيد طلبه لزيادة أرباحك.</p>
            </article>

            {/* Service 6 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><FileText size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">تحديثات فورية لفريقك</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">كل حالة واضحة في وقتها</p>
              <p className="text-xs text-slate-500 leading-relaxed">تابع حالة كل طلب وموقعه وآخر إجراء من مكان واحد، ليبقى فريق الشحن على اطلاع دائم.</p>
            </article>

            {/* Service 7 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><HelpCircle size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">التدخل البشري والتحويل الذكي</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">تحويل سلس لفريقك</p>
              <p className="text-xs text-slate-500 leading-relaxed">في حال طرح العميل سؤالاً معقداً أو تعديلاً، يتوقف البوت فوراً ويحيل الدردشة لصندوق الوارد المشترك.</p>
            </article>

            {/* Service 8 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><BarChart3 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">لوحة تحليل المخاطر والتحليلات</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">مؤشرات واضحة لاتخاذ القرار</p>
              <p className="text-xs text-slate-500 leading-relaxed">مراقبة تفصيلية لمعدلات التسليم ومستويات المخاطر وسلوك المشتري لضمان تحسين مستمر للهوامش.</p>
            </article>

          </div>
        </div>
      </section>

      {/* ROI Savings Calculator */}
      <section id="calculator" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">حاسبة العائد الاستثماري التفاعلية</h2>
            <p className="text-slate-500">حرك المؤشرات لترى مقدار المبالغ المهدورة وأرباحك المستردة بدقة.</p>
          </div>

          <div className="bg-white rounded-3xl p-8 lg:p-12 border border-slate-100 shadow-2xl grid lg:grid-cols-12 gap-10">
            {/* Input Controls */}
            <div className="lg:col-span-7 space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>عدد طلبات الدفع عند الاستلام شهرياً:</span>
                  <span className="text-sky">{calcOrders.toLocaleString()} طلب</span>
                </div>
                <input type="range" min="50" max="5000" step="50" value={calcOrders} onChange={e=>setCalcOrders(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>متوسط قيمة الطلب (AOV):</span>
                  <span className="text-sky">{calcAov} ريال</span>
                </div>
                <input type="range" min="50" max="1500" step="10" value={calcAov} onChange={e=>setCalcAov(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>نسبة المرتجعات الحالية (RTO):</span>
                  <span className="text-rose-600">{calcRto}%</span>
                </div>
                <input type="range" min="5" max="50" step="1" value={calcRto} onChange={e=>setCalcRto(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-rose-500"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>تكلفة الشحن لشركة الشحن (ذهاب وعودة):</span>
                  <span className="text-sky">{calcShipping} ريال</span>
                </div>
                <input type="range" min="15" max="100" step="5" value={calcShipping} onChange={e=>setCalcShipping(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>
            </div>

            {/* Results Panel */}
            <div className="lg:col-span-5 bg-blue-deep text-white rounded-2xl p-8 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"></div>
              <div className="space-y-6 relative z-10">
                <div>
                  <span className="text-xs text-rose-300 font-bold uppercase tracking-wider block">الخسارة الشهرية الحالية لمتجرك:</span>
                  <strong className="text-xl text-rose-200 line-through block mt-1">{totalCurrentLoss.toLocaleString()} ريال</strong>
                </div>
                <div>
                  <span className="text-xs text-emerald-300 font-bold uppercase tracking-wider block">الأرباح المستردة شهرياً مع مجيب:</span>
                  <strong className="text-4xl text-mint font-black block mt-2">{totalSavedRevenue.toLocaleString()} ريال</strong>
                </div>
                <p className="text-xs text-blue-200 leading-relaxed">
                  الحسابات تفترض انخفاض نسبة المرتجعات إلى <strong>12%</strong>، وتوفير تكاليف الشحن المهدر وتجهيز المرتجعات.
                </p>
              </div>

              <button onClick={() => openAuth("register")} className="mt-8 w-full btn-gold font-black py-4 rounded-xl shadow-lg relative z-10 border-none text-base">
                وفر {totalSavedRevenue.toLocaleString()} ريال شهرياً وابدأ مجاناً
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-slate-50 py-20 px-6 border-t border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">استثمر جزءاً صغيراً مما نوفره لك</h2>
            <p className="text-slate-500">باقات شفافة وبسيطة، بدون رسوم مخفية أو عمولات على الرسائل.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <article className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between hover:shadow-xl transition-all">
              <div>
                <p className="font-black text-xl text-blue-deep">الباقة المبتدئة (Starter)</p>
                <p className="text-slate-400 text-sm mt-1">للمتاجر الجديدة والناشئة</p>
                <strong className="text-3xl font-black text-sky block mt-6">299 ريال <span className="text-sm font-normal text-slate-400">($79) /شهرياً</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">✓ تأكيد تلقائي حتى 1,000 طلب/شهر</li>
                  <li className="flex items-center gap-2 font-bold text-emerald-800">✓ ميزة التحقق من موقع GPS مشمولة</li>
                  <li className="flex items-center gap-2">✓ ربط فوري مع سلة، زد، وشوبيفاي</li>
                  <li className="flex items-center gap-2 text-slate-400">✗ صندوق الوارد المشترك للتحويل البشري</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full bg-slate-100 text-slate-700 font-bold p-3 rounded-xl hover:bg-slate-200 transition-colors">البدء مجاناً</button>
            </article>

            <article className="bg-white border-2 border-emerald-500 rounded-3xl p-8 flex flex-col justify-between shadow-2xl relative">
              <span className="absolute -top-3 right-8 rounded-full bg-emerald-500 px-4 py-1 text-xs font-bold text-white shadow">🚀 الموصى بها (180IQ)</span>
              <div>
                <p className="font-black text-xl text-blue-deep">باقة النمو (Growth)</p>
                <p className="text-slate-400 text-sm mt-1">تأكيد متقدم وذكاء اصطناعي كامل</p>
                <strong className="text-3xl font-black text-sky block mt-6">599 ريال <span className="text-sm font-normal text-slate-400">($159) /شهرياً</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">✓ تأكيد تلقائي متقدم للطلبيات</li>
                  <li className="flex items-center gap-2 font-bold text-emerald-800">✓ حماية التوصيل الكاملة (GPS + فحص العناوين)</li>
                  <li className="flex items-center gap-2 font-bold text-blue-800">✓ صندوق المحادثات المشترك والتحويل البشري</li>
                  <li className="flex items-center gap-2">✓ لوحات تحكم متقدمة ودعم أولوي</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full btn-gold font-bold p-3.5 rounded-xl shadow-lg border-none">البدء مجاناً</button>
            </article>

            <article className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between hover:shadow-xl transition-all">
              <div>
                <p className="font-black text-xl text-blue-deep">باقة التوسع (Scale)</p>
                <p className="text-slate-400 text-sm mt-1">للماركات الكبرى ومتعددة المتاجر</p>
                <strong className="text-3xl font-black text-sky block mt-6">1,199 ريال <span className="text-sm font-normal text-slate-400">($319) /شهرياً</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">✓ تأكيد COD لعدد غير محدود من المتاجر</li>
                  <li className="flex items-center gap-2">✓ ربط متاجر متعددة بلوحة واحدة</li>
                  <li className="flex items-center gap-2">✓ تكامل مع API المخصص والمخازن</li>
                  <li className="flex items-center gap-2 font-bold text-blue-800">✓ خادم مخصص للماركة ودعم مخصص</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full bg-slate-100 text-slate-700 font-bold p-3 rounded-xl hover:bg-slate-200 transition-colors">البدء مجاناً</button>
            </article>
          </div>
        </div>
      </section>

      {/* FAQ / Transparency Section */}
      <section className="bg-white py-16 px-6 border-t border-slate-100">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <h3 className="text-2xl font-black text-blue-deep">أسئلة شائعة وشفافية تامة ⚖️</h3>
            <p className="text-slate-500 text-sm">كل ما تود معرفته عن الفوترة، حماية البيانات والربط الرسمي مع Meta.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mt-10">
            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">كيف يتم احتساب رسوم محادثات واتساب (Meta)؟</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                نقوم بربط متجرك وحساب WABA بالمنصة مجاناً وبضغطة زر. رسوم محادثات واتساب (Conversation Fees) يتم دفعها واحتسابها مباشرة لحسابك في Meta حسب سياسة فيسبوك الرسمية، مما يضمن لك الشفافية المطلقة دون أي عمولة إضافية من مجيب.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">هل يتم تحديث العنوان تلقائياً في سلة وزد؟</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                نعم، بمجرد قيام العميل بمشاركة موقعه الجغرافي (GPS) بالواتساب، يقوم مجيب بكتابة إحداثيات وموقع العميل مباشرة داخل تفاصيل الشحن الخاصة بالطلب في سلة/زد لتتمكن من طباعة البوليصات فوراً وشحنها دون أي إدخال يدوي.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">ماذا يحدث عندما يكتب العميل رداً معقداً للبوت؟</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                يحتوي مجيب على نظام تحويل بشري ذكي (Agent Handover)؛ في حال طرح العميل سؤالاً خارج نطاق التأكيد أو طلب تعديلاً، يتوقف البوت فوراً ويحيل المحادثة لصندوق الوارد المشترك ليتدخل فريق الدعم الخاص بك يدوياً.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">هل ميزة التحقق من موقع GPS متوفرة في الباقة المبتدئة؟</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                نعم! قمنا بنقل ميزة التحقق من الـ GPS للباقة المبتدئة (Starter) بحد أقصى 300 طلب شهرياً لتتمكن من اختبار القيمة الفعلية للمنصة وتقليل المرتجعات قبل الحاجة لترقية باقتك.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">هل بيانات الموقع آمنة ومتوافقة مع الخصوصية؟</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                يشارك العميل موقعه بموافقته الواضحة فقط. نستخدم أقل قدر لازم من البيانات، ونحميها أثناء النقل والتخزين، مع إمكانية طلب التصدير أو الحذف من لوحة الخصوصية. يظل التاجر مسؤولاً عن إشعار عملائه والالتزام بمتطلبات PDPL المحلية.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Integration showcase */}
      <section className="py-20 px-6 bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto text-center space-y-8">
          <h3 className="text-lg font-bold text-slate-400 uppercase tracking-widest">ربط وتكامل رسمي سريع</h3>
          <div className="flex flex-wrap justify-center gap-8 items-center opacity-75">
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">سلة Salla</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">زد Zid</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Shopify</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Custom API</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 text-center text-slate-400 text-xs border-t border-slate-100 bg-slate-50">
        <p>© 2026 مجيب (Mujeeb). جميع الحقوق محفوظة لشركاء الهوية.</p>
        <div className="mt-2 flex justify-center gap-4">
          <a href="/privacy.html" className="hover:underline">سياسة الخصوصية</a>
          <a href="/terms.html" className="hover:underline">شروط الخدمة</a>
        </div>
        <p className="mt-2">Mujeeb is operated by <strong className="text-slate-600">AYOUB FADIL</strong> · <a href="mailto:support@usemujeeb.com" className="text-slate-600 hover:underline">support@usemujeeb.com</a></p>
        <div className="mt-4 flex justify-center gap-4 flex-wrap">
          <a href="/data-deletion.html" className="hover:underline">Delete my data</a>
          <a href="https://x.com/DigiClub09" target="_blank" rel="noreferrer" aria-label="Mujeeb on X" className="font-bold text-slate-600 hover:text-black">𝕏 X</a>
          <a href="https://www.linkedin.com/company/mujeeb/" target="_blank" rel="noreferrer" aria-label="Mujeeb on LinkedIn" className="font-bold text-slate-600 hover:text-blue-700">in LinkedIn</a>
        </div>
      </footer>

      {/* Authentication Modal Overlay */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl w-full max-w-xl overflow-hidden shadow-2xl relative border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
            <button onClick={() => setModalOpen(false)} className="absolute top-4 left-4 p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-50 transition-colors">
              <X size={20} />
            </button>
            <form onSubmit={submit} className="p-8 sm:p-10 flex flex-col justify-center">
              <p className="inline-block px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold w-fit mb-3">50 تأكيد طلب مجاناً</p>
              <h3 className="text-2xl font-black mt-2 text-ink">{mode === "login" ? "مرحباً بعودتك" : "ابدأ تأكيد طلباتك مجاناً"}</h3>
              <p className="text-slate-500 text-sm mt-1">اربط متجرك وWhatsApp، ثم ابدأ تأكيد طلبات الدفع عند الاستلام بلا بطاقة بنكية.</p>
              {shopifyInstall && <p className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-bold text-emerald-800">تمت موافقة Shopify لمتجر {shopifyDomain}. أنشئ حسابك أو سجّل الدخول لإكمال الربط تلقائياً.</p>}

              <div className="grid gap-3 mt-7">
                {mode === "register" && (
                  <>
                    <input name="full_name" required placeholder="الاسم الكامل" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <input name="phone" required placeholder="+9665xxxxxxxx" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <input name="store_name" required defaultValue={shopifyDomain.replace(".myshopify.com", "")} placeholder="اسم المتجر" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <input type="hidden" name="platform" value={shopifyInstall ? "shopify" : "custom"} />
                    <input type="hidden" name="country_code" value="SA" />
                    <p className="rounded-xl bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-500">ستختار طريقة ربط متجرك في الخطوة التالية.</p>
                  </>
                )}
                <input name="email" type="email" required placeholder="البريد الإلكتروني للعمل" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                <input name="password" type="password" minLength={10} required placeholder="كلمة المرور" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                
                {error && <p className="text-rose-600 text-sm font-bold bg-rose-50 p-2 rounded">{error}</p>}
                
                <button className="rounded-xl btn-gold font-black p-4 mt-2 text-lg shadow-xl hover:shadow-2xl">
                  {mode === "login" ? "تسجيل الدخول" : "ابدأ 50 تأكيد طلب مجاناً"}
                </button>
              </div>

              <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="mt-5 text-sm text-sky font-bold hover:underline">
                {mode === "login" ? "متجر جديد؟ أنشئ حسابك لبدء التجربة" : "لديك حساب؟ سجّل الدخول هنا"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({title,value,detail,icon:Icon,tone}:{title:string;value:string|number;detail:string;icon:any;tone:string}) {
  return <article className="glass rounded-2xl p-5"><div className="flex justify-between"><div><p className="text-sm text-slate-500">{title}</p><p className="text-3xl font-black mt-2">{value}</p></div><div className={`w-11 h-11 rounded-xl grid place-items-center ${tone}`}><Icon size={21}/></div></div><p className="text-xs text-slate-500 mt-4">{detail}</p></article>;
}

function DemoCard({title,duration,transcript,src,poster,onStart}:{title:string;duration:string;transcript:string;src:string;poster:string;onStart?:()=>void}) {
  const [open,setOpen]=useState(false);
  const [playing,setPlaying]=useState(false);
  const videoRef=useRef<HTMLVideoElement>(null);
  const play=()=>{setPlaying(true);void videoRef.current?.play();};
  return <article className="rounded-3xl bg-white p-5 shadow-xl border border-slate-100">
    <div className="aspect-video rounded-2xl bg-slate-950 relative overflow-hidden group">
      <video ref={videoRef} className="h-full w-full object-cover" src={src} poster={poster} controls={playing} preload="metadata" playsInline onPlay={()=>setPlaying(true)} onEnded={()=>setPlaying(false)} aria-label={title}/>
      {!playing&&<button type="button" onClick={play} aria-label={`تشغيل ${title}`} className="absolute inset-0 grid place-items-center bg-slate-950/15 transition-colors hover:bg-slate-950/25 focus:outline-none focus:ring-4 focus:ring-inset focus:ring-white/60"><span className="grid h-16 w-16 place-items-center rounded-full border border-white/50 bg-white/90 text-2xl text-blue-deep shadow-2xl transition-transform group-hover:scale-110">▶</span></button>}
      <span className="absolute right-4 top-4 rounded-full border border-white/30 bg-slate-950/75 px-3 py-1.5 text-[11px] font-bold text-white backdrop-blur">مدعوم بالترجمة العربية الخليجية</span>
    </div>
    <div className="mt-4 flex items-center justify-between gap-3"><p className="font-black text-blue-deep">{title}</p><span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">{duration}</span></div>
    <button onClick={()=>setOpen(!open)} className="mt-4 text-sm font-bold text-sky">{open?"إخفاء النص":"قراءة نص الفيديو"}</button>
    {open&&<p className="mt-3 rounded-xl bg-slate-50 p-4 text-sm leading-7 text-slate-600">{transcript}</p>}
    <button onClick={onStart} className="mt-4 w-full rounded-xl btn-gold p-3 font-black">ابدأ مجاناً مع 50 طلباً</button>
  </article>;
}

function DeveloperApi({storeId}:{storeId:string}) {
  const [createdKey,setCreatedKey]=useState(""); const [message,setMessage]=useState("");
  const keys=useQuery({queryKey:["api-keys",storeId],queryFn:async()=> (await api.get("/api/api-keys",{params:{store_id:storeId}})).data});
  const generate=async()=>{const r=await api.post("/api/api-keys",{store_id:storeId,name:"Pilot integration"});setCreatedKey(r.data.api_key);setMessage("انسخ المفتاح الآن. لن نعرضه كاملاً مرة أخرى.");keys.refetch();};
  const snippet=`curl -X POST https://api.usemujeeb.com/api/orders/custom \\\n+  -H "Content-Type: application/json" \\\n+  -H "X-Mujeeb-API-Key: YOUR_KEY" \\\n+  -d '{"order_id":"1001","customer_name":"Customer","customer_phone":"+966501234567","amount":250,"currency":"SAR","payment_method":"COD","items":[]}'`;
  return <section className="mt-8 max-w-4xl"><div className="flex items-center gap-3"><Code2 className="text-sky"/><div><h2 className="text-xl font-black">تكامل API للمتاجر</h2><p className="text-sm text-slate-500">Shopify، WooCommerce، Laravel وأي متجر مخصص.</p></div></div>
    <div className="grid lg:grid-cols-2 gap-5 mt-5"><article className="glass rounded-2xl p-6"><h3 className="font-black">مفتاح المتجر</h3><p className="text-sm text-slate-500 mt-2">يُحفظ المفتاح مشفراً كبصمة، ويمكن إلغاؤه in any time.</p>{createdKey?<><div dir="ltr" className="mt-4 break-all rounded-xl bg-slate-950 p-4 text-xs text-emerald-300">{createdKey}</div><button onClick={()=>navigator.clipboard.writeText(createdKey)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> نسخ المفتاح</button></>:<button onClick={generate} className="mt-5 rounded-xl bg-ink text-white px-5 py-3 font-bold">إنشاء مفتاح API</button>}{message&&<p className="mt-3 text-xs text-amber-700">{message}</p>}<p className="mt-5 text-xs text-slate-500">المفاتيح النشطة: {keys.data?.length||0}</p></article>
    <article className="glass rounded-2xl p-6"><h3 className="font-black">أرسل أول طلب</h3><pre dir="ltr" className="mt-4 overflow-auto rounded-xl bg-slate-950 p-4 text-[11px] leading-5 text-slate-200">{snippet}</pre><button onClick={()=>navigator.clipboard.writeText(snippet)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> نسخ المثال</button></article></div></section>;
}

function Billing({storeId,shopifyConnected}:{storeId:string;shopifyConnected:boolean}) {
  const [checkingOut,setCheckingOut]=useState("");
  const [message,setMessage]=useState("");
  const creemLinks: Record<string, string> = {
    starter: "https://www.creem.io/payment/prod_2vqJ5mN9UsaIs92R0GGEGT",
    growth: "https://www.creem.io/payment/prod_7jta2efsRo349gYRj8401C",
    scale: "https://www.creem.io/payment/prod_6FvTUHYPbiKxTrai4rOZGP"
  };
  const plans=[
    {id:"starter",name:"Starter",price:"99",usd:"$29",orders:"حتى 300 طلب شهرياً",detail:"لمتجر واحد وتأكيد فوري مع GPS"},
    {id:"growth",name:"Growth",price:"249",usd:"$69",orders:"حتى 2,000 طلب شهرياً",detail:"صندوق مشترك وتحويل للفريق البشري",featured:true},
    {id:"scale",name:"Scale",price:"499",usd:"$139",orders:"حتى 5,000 طلب شهرياً",detail:"للمتاجر الكبرى وحجم الطلبات المرتفع"},
  ];
  const checkout=async(plan:string)=>{
    setCheckingOut(plan); setMessage("");
    try {
      if (shopifyConnected) {
        const pricing = await api.get("/api/integrations/shopify/pricing", {params:{store_id:storeId}});
        location.href = pricing.data.url;
        return;
      }
      const r = await api.post("/api/payments/checkout",{store_id:storeId,plan});
      if (r.data?.url) {
        location.href = r.data.url;
        return;
      }
      throw new Error("No URL returned");
    }
    catch(err:any){
      if (creemLinks[plan]) {
        location.href = creemLinks[plan];
        return;
      }
      setMessage(err.response?.status===503?"الدفع الإلكتروني لهذه الخطة قيد التفعيل. تواصل معنا لتثبيت عرض المؤسسين.":"تعذر فتح صفحة الدفع الآمنة. حاول مرة أخرى.");
      setCheckingOut("");
    }
  };
  return <section className="mt-8 max-w-5xl"><p className="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-bold w-fit mb-3">نموذج أعمال يضمن ربحك</p><h2 className="text-3xl font-black mt-2 text-ink">استثمر جزءاً صغيراً مما نوفره لك</h2><p className="text-slate-500 mt-3 text-lg">بدون عمولات إضافية على الرسائل للحفاظ على هامش ربحك عالياً. ادفع بعد تحقق القيمة الفعلية من النظام.</p><div className="grid md:grid-cols-3 gap-5 mt-8">{plans.map(plan=><article key={plan.id} className={`glass rounded-2xl p-8 relative flex flex-col ${plan.featured?"border-2 border-mint shadow-2xl shadow-mint/10":""}`}>{plan.featured&&<span className="absolute -top-3 right-8 rounded-full bg-mint px-4 py-1.5 text-xs font-bold text-white shadow-lg">الباقة الموصى بها</span>}<p className="font-black text-2xl text-blue-deep">{plan.name}</p><p className="mt-5 text-4xl font-black text-sky">{plan.price} <span className="text-sm font-medium text-slate-400">ريال ({plan.usd})/شهر</span></p><p className="mt-5 font-bold p-3 bg-sky-50 rounded-xl text-blue-deep text-center">{plan.orders}</p><p className="mt-4 min-h-16 text-sm text-slate-500 leading-relaxed font-medium">{plan.detail}</p><button onClick={()=>checkout(plan.id)} disabled={!!checkingOut} className={`mt-auto w-full rounded-xl p-4 font-bold text-lg transition-transform ${plan.featured?"btn-gold":"bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>{checkingOut===plan.id?"جارٍ التحميل الآمن...":`اختيار باقة ${plan.name}`}</button></article>)}</div>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800 border border-amber-200">{message}</p>}<p className="mt-6 text-xs text-slate-400 text-center uppercase tracking-wider">{shopifyConnected?"الفوترة تتم مباشرة وآمان عبر Shopify":"نظام فواتير آمن مدعوم بـ Creem"} | إلغاء متى شئت</p></section>;
}

function ZeroFrictionOnboarding({storeId,storeName,freeRemaining,onReady}:{storeId:string;storeName:string;freeRemaining:number;onReady:()=>void}) {
  const [platform,setPlatform]=useState<"shopify"|"salla"|"zid"|"custom"|"">("");
  const [shop,setShop]=useState(""); const [merchantKey,setMerchantKey]=useState("");
  const [qr,setQr]=useState(""); const [notice,setNotice]=useState(""); const [busy,setBusy]=useState(false); const [showKeyGuide,setShowKeyGuide]=useState(false); const [customKey,setCustomKey]=useState("");
  const connections=useQuery({queryKey:["onboarding-connections",storeId],queryFn:async()=> (await api.get("/api/integrations/status",{params:{store_id:storeId}})).data});
  const whatsapp=useQuery({
    queryKey:["onboarding-whatsapp",storeId],
    queryFn:async()=> (await api.get("/api/waapi/status",{params:{store_id:storeId}})).data,
    refetchInterval: qr ? 3000 : false,
  });
  const connectedStore=Boolean(connections.data?.shopify?.connected || connections.data?.salla?.connected || connections.data?.zid?.connected || connections.data?.custom?.connected);
  const connectedWhatsapp=Boolean(whatsapp.data?.connected);
  const connectShopify=async()=>{try{setBusy(true);const r=await api.post("/api/integrations/shopify/start",{store_id:storeId,shop});location.href=r.data.url}catch(err:any){setNotice(err.response?.data?.detail||"تعذر بدء ربط Shopify")}finally{setBusy(false)}};
  const connectMerchant=async()=>{try{setBusy(true);await api.post(`/api/integrations/${platform}/merchant-key`,{store_id:storeId,token:merchantKey});setMerchantKey("");setNotice("تم ربط المتجر بنجاح. ستصل الطلبات تلقائياً إلى مجيب.");connections.refetch();onReady()}catch(err:any){setNotice(err.response?.data?.detail||"تعذر ربط المتجر. تحقق من رمز الربط.")}finally{setBusy(false)}};
  const createCustomAccess=async()=>{try{setBusy(true);const r=await api.post("/api/integrations/custom/start",{store_id:storeId});setCustomKey(r.data.api_key||"");setNotice(r.data.api_key?"تم إنشاء وصول آمن لمتجرك. سلّم المفتاح التالي لمطور متجرك مرة واحدة فقط.":"وصول مطور متجرك جاهز بالفعل. إذا احتجت مفتاحاً جديداً، تواصل مع الدعم.");connections.refetch();onReady()}catch(err:any){setNotice(err.response?.data?.detail||"تعذر تجهيز وصول متجرك المخصص.")}finally{setBusy(false)}};
  const createChannel=async()=>{try{setBusy(true);const r=await api.post("/api/waapi/provision",{store_id:storeId});setQr(r.data.qr||"");setNotice("");whatsapp.refetch();onReady()}catch(err:any){setNotice(err.response?.data?.detail||"تعذر إنشاء قناة WhatsApp")}finally{setBusy(false)}};
  const sendTest=async()=>{try{setBusy(true);await api.post("/api/waapi/test-message",{store_id:storeId});setNotice("تم إرسال رسالة الاختبار إلى رقمك. تحقق من WhatsApp الآن.")}catch(err:any){setNotice(err.response?.data?.detail||"تعذر إرسال رسالة الاختبار. تأكد من مسح QR أولاً.")}finally{setBusy(false)}};
  const cards=[{id:"shopify",name:"Shopify",copy:"ربط آمن خلال دقيقتين"},{id:"salla",name:"سلة",copy:"مفتاح ربط واحد من متجرك"},{id:"zid",name:"زد",copy:"رمز ربط واحد من متجرك"},{id:"custom",name:"متجر مخصص",copy:"ربط سريع مع فريق مجيب"}] as const;
  const keyLabel=platform==="salla"?"مفتاح ربط سلة":"رمز ربط زد";
  return <section className="mt-8 max-w-5xl" dir="rtl">
    <div className="rounded-3xl bg-gradient-to-l from-blue-deep to-slate-900 p-7 text-white"><p className="text-emerald-300 font-black text-sm">تجربتك المجانية</p><h2 className="text-3xl font-black mt-2">50 تأكيد طلبات مجاناً لمتجرك</h2><p className="text-blue-100 mt-3">لا تحتاج بطاقة بنكية. اربط متجرك ثم WhatsApp وابدأ التشغيل.</p><div className="mt-5 inline-flex rounded-xl bg-white/10 border border-white/20 px-4 py-2 font-black">{50-freeRemaining} / 50 طلب مستخدم</div></div>
    {notice&&<p className="mt-5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 p-4 text-sm">{notice}</p>}
    <div className="mt-7 grid gap-5">
      <article className="glass rounded-2xl p-6"><div className="flex gap-4 items-start"><span className="grid place-items-center w-9 h-9 rounded-full bg-blue-deep text-white font-black">1</span><div><h3 className="font-black text-xl">اربط متجرك</h3><p className="text-slate-500 text-sm mt-1">اختر منصتك. تبدأ مزامنة الطلبات تلقائياً بعد الربط.</p></div></div><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-5">{cards.map(item=><button key={item.id} onClick={()=>{setPlatform(item.id);setNotice("")}} className={`text-right rounded-xl border p-4 transition ${platform===item.id?"border-sky bg-sky-50":"border-slate-200 hover:border-sky"}`}><Store className="text-sky mb-5" size={21}/><b>{item.name}</b><span className="block text-xs text-slate-500 mt-2">{item.copy}</span><span className="mt-4 block border-t border-slate-100 pt-3 text-[11px] font-bold text-slate-400">حوالي دقيقتين · اتصال آمن · مزامنة تلقائية</span></button>)}</div>
      {platform==="shopify"&&<div className="mt-5 rounded-xl bg-slate-50 p-4"><label className="text-sm font-bold">اسم متجر Shopify</label><div className="mt-2 flex gap-2" dir="ltr"><input value={shop} onChange={e=>setShop(e.target.value)} placeholder="store.myshopify.com" className="flex-1 rounded-xl border border-slate-200 p-3 text-sm"/><button disabled={!shop||busy} onClick={connectShopify} className="rounded-xl bg-blue-deep text-white px-5 font-bold disabled:opacity-50">ربط المتجر</button></div></div>}
      {(platform==="salla"||platform==="zid")&&<div className="mt-5 rounded-xl bg-slate-50 p-4"><div className="flex items-center justify-between gap-4"><label className="text-sm font-bold">{keyLabel}</label><button type="button" onClick={()=>setShowKeyGuide(!showKeyGuide)} className="text-xs font-bold text-sky">{showKeyGuide?"إخفاء الدليل":"شاهد الدليل · 15 ثانية"}</button></div><p className="text-xs text-slate-500 mt-1">انسخه من إعدادات متجرك. نحفظه بأمان ونكمل الربط تلقائياً.</p>{showKeyGuide&&<div className="mt-3 rounded-xl border border-sky-100 bg-white p-3 text-xs leading-6 text-slate-600">{platform==="salla"?"من لوحة سلة: الإعدادات ← خيارات المطور ← أنشئ مفتاح API، ثم انسخه هنا.":"من إعدادات متجر زد: أنشئ X-Manager-Token، ثم انسخه هنا."}</div>}<div className="mt-2 flex gap-2"><input value={merchantKey} onChange={e=>setMerchantKey(e.target.value)} type="password" placeholder={keyLabel} className="flex-1 rounded-xl border border-slate-200 p-3 text-sm"/><button disabled={!merchantKey||busy} onClick={connectMerchant} className="rounded-xl bg-blue-deep text-white px-5 font-bold disabled:opacity-50">ربط المتجر</button></div></div>}
      {platform==="custom"&&<div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><p>أنشئ وصولاً آمناً لمطور متجرك في خطوة واحدة. لا تحتاج لأي إعداد الآن.</p><button disabled={busy} onClick={createCustomAccess} className="mt-3 rounded-xl bg-blue-deep px-5 py-3 font-bold text-white disabled:opacity-50">إنشاء وصول المطور</button>{customKey&&<div className="mt-4 rounded-xl bg-slate-950 p-4 text-xs text-emerald-300 break-all" dir="ltr">{customKey}</div>}{customKey&&<button onClick={()=>navigator.clipboard.writeText(customKey)} className="mt-3 text-sm font-bold text-sky">نسخ المفتاح لمطور المتجر</button>}</div>}</article>
      <article className="glass rounded-2xl p-6"><div className="flex gap-4 items-start"><span className="grid place-items-center w-9 h-9 rounded-full bg-emerald-600 text-white font-black">2</span><div><h3 className="font-black text-xl">اربط WhatsApp Business</h3><p className="text-slate-500 text-sm mt-1">بعد ربط متجرك، أنشئ القناة ثم امسح رمز QR من WhatsApp ← الأجهزة المرتبطة.</p></div></div>{connectedWhatsapp?<div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800"><div className="flex items-center gap-2 font-black"><CheckCircle2 size={20}/> تم ربط WhatsApp بنجاح</div><p className="mt-1 text-sm">{whatsapp.data?.display_phone || "قناتك جاهزة الآن"}</p></div>:!qr?<><button disabled={busy||!connectedStore} onClick={createChannel} className="mt-5 rounded-xl bg-emerald-600 text-white px-6 py-3 font-black disabled:opacity-50">إنشاء القناة وإظهار QR</button>{!connectedStore&&<p className="mt-3 text-xs text-slate-500">أكمل ربط متجرك أولاً لتفعيل هذه الخطوة.</p>}</>:<div className="mt-5 grid sm:grid-cols-[180px_1fr] gap-5 items-center"><img src={qr} alt="رمز QR لربط WhatsApp" className="w-44 h-44 bg-white rounded-xl p-2 border"/><p className="text-sm text-slate-600 leading-7">افتح WhatsApp على هاتفك، اختر الأجهزة المرتبطة، ثم امسح الرمز. سيؤكد مجيب الاتصال تلقائياً خلال ثوانٍ.</p></div>}</article>
      <article className="glass rounded-2xl p-6"><div className="flex gap-4 items-start"><span className="grid place-items-center w-9 h-9 rounded-full bg-slate-800 text-white font-black">3</span><div><h3 className="font-black text-xl">شغّل أول 50 تأكيداً مجاناً</h3><p className="text-slate-500 text-sm mt-1">تحقق من جاهزية الربط، ثم أرسل رسالة اختبار إلى رقمك.</p></div></div><div className="mt-5 space-y-3 text-sm"><p className={`flex items-center gap-2 ${connectedStore?"text-emerald-700":"text-slate-500"}`}><CheckCircle2 size={18}/> {connectedStore?`تم ربط المتجر: ${storeName}`:"بانتظار ربط المتجر"}</p><p className={`flex items-center gap-2 ${connectedWhatsapp?"text-emerald-700":"text-slate-500"}`}><CheckCircle2 size={18}/> {connectedWhatsapp?`تم ربط WhatsApp: ${whatsapp.data?.display_phone || "متصل"}`:"امسح QR لإتمام ربط WhatsApp"}</p><p className={`flex items-center gap-2 ${connectedStore&&connectedWhatsapp?"text-emerald-700":"text-slate-500"}`}><CheckCircle2 size={18}/> {connectedStore&&connectedWhatsapp?"النظام جاهز لتأكيد الطلبات":"يكمل النظام تلقائياً بعد الخطوتين"}</p></div><button disabled={!connectedStore||!connectedWhatsapp||busy} onClick={sendTest} className="mt-5 rounded-xl bg-blue-deep text-white px-6 py-3 font-black disabled:opacity-40">إرسال طلب تجريبي حقيقي</button></article>
    </div>
  </section>;
}

function OperationalDashboard({summary,orders}:{summary:Summary;orders:Order[]}) {
  const [details,setDetails]=useState<string|null>(null);
  const remaining=summary.free_pilot_remaining ?? 50;
  const selectedOrder=orders.find(order=>order.id===details);
  return <section className="mt-8" dir="rtl">
    <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-4">
      <Stat title="الطلبات المستلمة" value={summary.total} detail="كل الطلبات الواردة" icon={PackageCheck} tone="bg-blue-100 text-blue-700"/>
      <Stat title="الطلبات المؤكدة" value={`${summary.confirmation_rate}%`} detail={`${summary.confirmed} طلب مؤكد`} icon={CheckCircle2} tone="bg-emerald-100 text-emerald-700"/>
      <Stat title="الطلبات الملغاة" value={summary.cancelled} detail="لا تشحن قبل التأكيد" icon={X} tone="bg-rose-100 text-rose-700"/>
      <Stat title="مواقع GPS المستلمة" value={(summary as any).gps_verified_count ?? 0} detail="عناوين أوضح للشحن" icon={MapPin} tone="bg-indigo-100 text-indigo-700"/>
      <Stat title="رصيد التجربة" value={`${remaining} / 50`} detail="تأكيد مجاني متبقٍ" icon={Coins} tone="bg-amber-100 text-amber-700"/>
    </div>
    <section className="mt-7 rounded-2xl bg-white border border-slate-100 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-100"><h2 className="text-xl font-black">سجل الطلبات</h2><p className="text-sm text-slate-500 mt-1">تابع ما تم تأكيده وما يحتاج متابعة، من دون تفاصيل تقنية.</p></div>
      {orders.length ? <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th className="p-4 text-right">رقم الطلب</th><th className="p-4 text-right">العميل</th><th className="p-4 text-right">المبلغ</th><th className="p-4 text-right">الحالة</th><th className="p-4 text-right">الموقع</th><th className="p-4 text-right">آخر إجراء</th></tr></thead><tbody>{orders.map(order=><tr key={order.id} className="border-t border-slate-100 hover:bg-slate-50"><td className="p-4 font-bold">#{order.external_order_number || order.id.slice(0,8)}</td><td className="p-4 text-slate-600">{order.customer_name || "عميل المتجر"}</td><td className="p-4 font-bold">{order.amount} {order.currency}</td><td className="p-4"><span className={`status-${order.status} px-3 py-1 text-xs`}>{statusLabel[order.status] || order.status}</span></td><td className="p-4">{order.gps_lat&&order.gps_lng?<a className="inline-flex items-center gap-1 text-sky font-bold" target="_blank" rel="noreferrer" href={`https://www.google.com/maps?q=${order.gps_lat},${order.gps_lng}`}><MapPin size={14}/> موقع مؤكد</a>:<span className="text-slate-400">بانتظار الموقع</span>}</td><td className="p-4"><button onClick={()=>setDetails(details===order.id?null:order.id)} className="font-bold text-sky">عرض التفاصيل</button></td></tr>)}</tbody></table></div>:<div className="p-12 text-center text-slate-500">ستظهر طلبات متجرك هنا فور وصولها.</div>}
      {selectedOrder&&<div className="mx-5 mb-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><div className="flex items-center justify-between gap-3"><p className="font-black text-ink">تفاصيل الطلب #{selectedOrder.external_order_number || selectedOrder.id.slice(0,8)}</p><button onClick={()=>setDetails(null)} className="font-bold text-sky">إغلاق</button></div><div className="mt-3 grid sm:grid-cols-3 gap-3 text-xs"><p><span className="text-slate-400">آخر حالة:</span> {statusLabel[selectedOrder.status] || selectedOrder.status}</p><p><span className="text-slate-400">وقت الاستلام:</span> {new Date(selectedOrder.created_at).toLocaleString("ar-SA")}</p><p><span className="text-slate-400">فحص الطلب:</span> جاهز للشحن بعد التأكيد</p></div>{selectedOrder.items.length>0&&<p className="mt-3 text-xs"><span className="text-slate-400">المنتجات:</span> {selectedOrder.items.map(item=>item.name || item.title || "منتج").join("، ")}</p>}</div>}
    </section>
  </section>;
}

function DevWhatsAppSimulator({storeId}:{storeId:string}) {
  const [session,setSession]=useState<any>(null);
  const [message,setMessage]=useState("");
  const start=async()=>{try{setMessage("");setSession((await api.post("/api/dev/whatsapp/session",{store_id:storeId})).data);}catch(err:any){setMessage(err.response?.data?.detail||"تعذر بدء المحاكي");}};
  const emit=async(event:string,payload:Record<string,unknown>={})=>{if(!session)return;setSession((await api.post(`/api/dev/whatsapp/session/${session.id}/event`,{event,payload})).data);};
  return <article className="glass rounded-2xl p-6 border border-amber-200 bg-amber-50/40"><MessageCircle className="text-amber-600"/><h3 className="font-black text-lg mt-5">Pilote WhatsApp local</h3><p className="text-sm text-slate-600 mt-2">Simule le QR et le parcours Mujeeb sans connecter de compte WhatsApp réel.</p>{!session?<button onClick={start} className="mt-5 w-full rounded-xl bg-amber-600 text-white p-2 font-bold">Démarrer le pilote</button>:<div className="mt-4 space-y-3"><div className="mx-auto grid grid-cols-9 gap-0 w-28 h-28 bg-white p-2 border-4 border-slate-900" aria-label="QR de simulation">{Array.from({length:81},(_,i)=><span key={i} className={(i*17+i*i)%7<3?"bg-slate-900":"bg-white"}/>)}</div><p className="text-[11px] text-center font-mono break-all text-slate-500">{session.qr_payload}</p><div className="grid grid-cols-2 gap-2"><button onClick={()=>emit("qr_scanned")} className="rounded-lg bg-slate-900 text-white p-2 text-xs font-bold">Simuler scan</button><button onClick={()=>emit("order_created",{order_id:"DEV-001"})} className="rounded-lg bg-emerald-600 text-white p-2 text-xs font-bold">Simuler commande</button><button onClick={()=>emit("location_received",{lat:29.3759,lng:47.9774})} className="rounded-lg bg-sky-600 text-white p-2 text-xs font-bold">Simuler GPS</button><button onClick={()=>emit("store_synced",{status:"confirmed"})} className="rounded-lg bg-indigo-600 text-white p-2 text-xs font-bold">Simuler sync</button></div><p className="text-xs font-bold text-amber-800">Statut : {session.status} · événements : {session.events.length}</p></div>}{message&&<p className="mt-3 text-xs text-rose-700">{message}</p>}</article>;
}

function Privacy() {
  const [password,setPassword]=useState(""); const [message,setMessage]=useState("");
  const deletion=useQuery({queryKey:["deletion-status"],queryFn:async()=> (await api.get("/api/privacy/deletion-request")).data});
  const download=async()=>{const r=await api.get("/api/privacy/export");const blob=new Blob([JSON.stringify(r.data,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="mujeeb-data-export.json";link.click();URL.revokeObjectURL(url);};
  const schedule=async()=>{setMessage("");try{const r=await api.post("/api/privacy/deletion-request",{password});setMessage(`تمت جدولة الحذف في ${new Date(r.data.scheduled_for).toLocaleDateString("ar-SA")}.`);setPassword("");deletion.refetch();}catch(err:any){setMessage(err.response?.data?.detail||"تعذر جدولة الحذف");}};
  const cancel=async()=>{await api.delete("/api/privacy/deletion-request");setMessage("تم إلغاء طلب الحذف.");deletion.refetch();};
  return <section className="mt-8 max-w-4xl"><h2 className="text-2xl font-black">بياناتك تحت سيطرتك</h2><p className="text-slate-500 mt-2">نزّل نسخة قابلة للقراءة أو اطلب حذف الحساب آلياً بعد مهلة أمان 7 أيام.</p>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">{message}</p>}<div className="grid md:grid-cols-2 gap-5 mt-6"><article className="glass rounded-2xl p-6"><Download className="text-sky"/><h3 className="font-black text-lg mt-4">تصدير البيانات</h3><p className="text-sm text-slate-500 mt-2">الحساب، المتاجر، الطلبات والعملاء دون كلمات المرور أو مفاتيح الوصول.</p><button onClick={download} className="mt-5 rounded-xl bg-ink px-5 py-3 text-white font-bold">تنزيل JSON</button></article><article className="glass rounded-2xl p-6"><Trash2 className="text-rose-600"/><h3 className="font-black text-lg mt-4">حذف الحساب</h3>{deletion.data?.status==="scheduled"?<><p className="text-sm text-slate-500 mt-2">الحذف مجدول في {new Date(deletion.data.scheduled_for).toLocaleDateString("ar-SA")}.</p><button onClick={cancel} className="mt-5 rounded-xl border border-slate-300 px-5 py-3 font-bold">إلغاء الطلب</button></>:<><p className="text-sm text-slate-500 mt-2">أكد كلمة المرور. سيبقى بإمكانك إلغاء الطلب خلال المهلة.</p><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="كلمة المرور" className="mt-4 w-full rounded-xl border border-slate-200 p-3"/><button disabled={!password} onClick={schedule} className="mt-3 rounded-xl bg-rose-600 px-5 py-3 text-white font-bold disabled:opacity-50">جدولة الحذف</button></>}</article></div></section>;
}

function Dashboard({user,onLogout}:{user:User;onLogout:()=>void}) {
  const store=user.stores[0];
  const initialTab = location.pathname.endsWith("/integrations")
    ? "integrations"
    : location.pathname.endsWith("/billing")
      ? "billing"
      : "overview";
  const [tab,setTab]=useState(initialTab);
  const [showUpsell, setShowUpsell] = useState(true);
  // These states support legacy views that are not reachable from merchant navigation.
  // The only supported testing UI is protected under /admin.
  const [activeSimId, setActiveSimId] = useState<string | null>(null);
  const [simStep, setSimStep] = useState<"ready" | "pending_confirm" | "pending_gps" | "pending_upsell" | "completed">("ready");
  const [simAmount, setSimAmount] = useState(320);

  const summary=useQuery({queryKey:["summary",store.id],queryFn:async()=> (await api.get<any>("/api/orders/summary",{params:{store_id:store.id}})).data});
  const orders=useQuery({queryKey:["orders",store.id],queryFn:async()=> (await api.get<Order[]>("/api/orders",{params:{store_id:store.id}})).data});
  const integrationStatus=useQuery({queryKey:["integration-status",store.id],queryFn:async()=> (await api.get("/api/integrations/status",{params:{store_id:store.id}})).data});
  const waapiStatus=useQuery({queryKey:["waapi-status",store.id],queryFn:async()=> (await api.get("/api/waapi/status",{params:{store_id:store.id}})).data});
  
  const s = summary.data || {
    total:0, confirmed:0, cancelled:0, human_follow_up:0, confirmation_rate:0,
    plan:"free", free_pilot_remaining:50, gps_verified_count: 0,
    upsell_conversion_count: 0, upsell_revenue: 0.0, google_sheets_sync_healthy: false
  };
  const storeConnected=Boolean(integrationStatus.data?.shopify?.connected || integrationStatus.data?.salla?.connected || integrationStatus.data?.zid?.connected || integrationStatus.data?.custom?.connected);
  const systemReady=storeConnected && Boolean(waapiStatus.data?.connected);

  const startSimulator = async () => {
    try {
      const r = await api.post("/api/orders/simulate-chatbot");
      setActiveSimId(r.data.order_id);
      setSimStep("pending_confirm");
      setSimAmount(320);
    } catch {
      alert("يرجى التأكد من إضافة متجر أولاً.");
    }
  };

  const handleSimAction = async (action: "confirm" | "share_location" | "accept_upsell" | "reject_upsell") => {
    if (!activeSimId) return;
    try {
      const r = await api.post(`/api/orders/${activeSimId}/chatbot`, {action});
      if (action === "confirm") setSimStep("pending_gps");
      else if (action === "share_location") setSimStep("pending_upsell");
      else { setSimStep("completed"); setActiveSimId(null); summary.refetch(); orders.refetch(); }
      setSimAmount(Number(r.data.amount));
    } catch (err) { console.error(err); }
  };

  const nav=[
    {id:"overview",label:"لوحة القيادة",icon:BarChart3},
    {id:"orders",label:"سجل الطلبات",icon:Boxes},
    {id:"integrations",label:"ربط المتجر وWhatsApp",icon:Link2},
    {id:"billing",label:"الاشتراك والترقية",icon:CreditCard},
    {id:"privacy",label:"الخصوصية والأمان",icon:ShieldCheck}
  ];

  return <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]" dir="rtl"><aside className="bg-blue-deep text-white p-6 lg:min-h-screen border-l border-blue-900 shadow-[4px_0_24px_rgba(30,58,138,0.2)]"><div className="text-2xl font-black mb-10 flex items-center gap-2"><div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mint to-teal-800 flex items-center justify-center shadow-lg shadow-mint/20 text-xl font-bold">M</div>مُجيب</div><nav className="flex lg:flex-col gap-2 overflow-auto">{nav.map(n=><button key={n.id} onClick={()=>setTab(n.id)} className={`flex items-center gap-3 rounded-xl px-4 py-3.5 whitespace-nowrap transition-colors font-medium ${tab===n.id?"bg-white text-blue-deep shadow-md font-bold":"text-blue-200 hover:bg-white/10 hover:text-white"}`}><n.icon size={20}/>{n.label}</button>)}</nav><button onClick={onLogout} className="mt-12 lg:mt-[40vh] flex items-center gap-3 text-blue-300 hover:text-white transition-colors w-full px-4"><LogOut size={20}/> تسجيل الخروج</button></aside>
  <main className="mesh p-5 lg:px-10 lg:py-8"><header className="flex justify-between items-center bg-white/50 backdrop-blur-md p-4 rounded-2xl border border-slate-100 shadow-sm"><div><p className="text-sm font-bold text-sky">{store.name} · {store.country_code}</p><h1 className="text-2xl font-black mt-1 text-ink">أهلاً، {user.full_name.split(" ")[0]}</h1></div><div className="flex items-center gap-3"><button onClick={()=>setTab("billing")} className="px-4 py-2 font-bold text-sm bg-blue-deep text-white rounded-xl shadow-md hover:bg-blue-800 transition-colors">ترقية الحساب</button><span className="rounded-xl border border-mint bg-emerald-50 text-emerald-800 px-4 py-2 text-sm font-black shadow-sm">{s.plan==="free"?`التجربة (تبقى ${s.free_pilot_remaining??50} طلب)`:`باقة ${s.plan}`}</span></div></header>
  
  {showUpsell && s.plan==="free" && (s.free_pilot_remaining ?? 50) <= 5 && tab==="overview" && (
    <div className="mt-6 glass rounded-2xl p-6 border-l-4 border-l-gold relative flex flex-col sm:flex-row justify-between items-center shadow-xl shadow-gold/5 bg-gradient-to-r from-amber-50 to-white overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-gold/10 rounded-full blur-3xl"></div>
      <div className="z-10">
        <h3 className="text-lg font-black text-ink flex items-center gap-2"><Sparkles className="text-gold" size={18} /> بقي 5 تأكيدات مجانية فقط</h3>
        <p className="text-slate-600 text-sm mt-1">انتقل إلى Starter لتستمر تأكيدات الطلبات دون انقطاع، مع GPS حتى 300 طلب شهرياً.</p>
      </div>
      <div className="flex gap-3 mt-4 sm:mt-0 z-10 w-full sm:w-auto">
        <button className="text-slate-500 text-sm font-bold px-3 hover:text-ink transition-colors" onClick={() => setShowUpsell(false)}>إخفاء التنبيه</button>
        <button onClick={() => setTab("billing")} className="btn-gold whitespace-nowrap text-sm px-6 py-2.5 rounded-xl shadow-lg border-none w-full sm:w-auto">انتقل إلى Starter</button>
      </div>
    </div>
  )}

  {tab==="overview"&&(systemReady ? <OperationalDashboard summary={s} orders={orders.data || []}/> : <ZeroFrictionOnboarding storeId={store.id} storeName={store.name} freeRemaining={s.free_pilot_remaining ?? 50} onReady={() => {summary.refetch();integrationStatus.refetch();waapiStatus.refetch();}}/>)}

  {tab==="legacy-overview"&&<>
    {/* Core Stats Overview */}
    <section className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mt-8">
      <Stat title="إجمالي الطلبات المستلمة" value={s.total} detail="هذا الشهر (واتساب)" icon={PackageCheck} tone="bg-blue-100 text-blue-700 shadow-blue-500/10"/>
      <Stat title="نسبة التأكيد التلقائي" value={`${s.confirmation_rate}%`} detail={`تم تأكيد ${s.confirmed} طلب بالكامل`} icon={CheckCircle2} tone="bg-emerald-100 text-emerald-700 shadow-emerald-500/10"/>
      <Stat title="مواقع GPS المستلمة" value={s.gps_verified_count} detail="عناوين دقيقة بنسبة 100%" icon={MapPin} tone="bg-indigo-100 text-indigo-700 shadow-indigo-500/10"/>
      <Stat title="إيرادات الـ Upsell" value={`${s.upsell_revenue} ر.س`} detail={`تحويل ${s.upsell_conversion_count} عروض إضافية`} icon={BadgePercent} tone="bg-amber-100 text-amber-700 shadow-amber-500/10"/>
    </section>

    {/* Google Sheets Sync status banner */}
    <div className="mt-6 flex items-center justify-between p-4 rounded-xl bg-white border border-slate-100 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${s.google_sheets_sync_healthy ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`}></div>
        <p className="text-sm font-bold text-slate-700">تحديث جداول جوجل (Google Sheets):</p>
        <span className="text-xs text-slate-500">{s.google_sheets_sync_healthy ? "نشط ومزامن تلقائياً ✓" : "غير مفعل (اذهب إلى تفعيل القنوات للربط)"}</span>
      </div>
      {s.google_sheets_sync_healthy && <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">جاهز للعمل</span>}
    </div>

    {/* Interactive Chatbot Simulation Sandbox */}
    <section className="glass rounded-2xl p-8 mt-6 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-sky/5 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
      
      <div className="flex justify-between items-center relative z-10 border-b border-slate-100 pb-5">
        <div>
          <h2 className="font-black text-xl text-ink">محاكي المحادثة وتأكيد الطلبيات (Sandbox)</h2>
          <p className="text-sm font-medium text-slate-500 mt-2">اختبر دورة حياة البوت بالكامل: التأكيد، جمع GPS، وتقديم عروض الـ Upsell.</p>
        </div>
        <div className="w-12 h-12 bg-sky-100 text-sky rounded-2xl flex items-center justify-center border border-sky-200 shadow-lg shadow-sky/20"><Sparkles /></div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8 mt-6 items-start relative z-10">
        <div className="lg:col-span-7 space-y-4">
          {simStep === "ready" ? (
            <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
              <MessageCircle className="mx-auto text-slate-400 mb-3" size={32} />
              <h4 className="font-bold text-slate-700">ابدأ تجربة البوت التفاعلي</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">سيقوم النظام بإنشاء طلب وهمي بقيمة 320 ريال وبدء محادثة تأكيد آلية بالواتساب.</p>
              <button onClick={startSimulator} className="mt-5 rounded-xl bg-blue-deep hover:bg-blue-800 text-white font-bold text-sm px-6 py-3 shadow-md">
                محاكاة طلب جديد 🚀
              </button>
            </div>
          ) : (
            <div className="bg-[#E5DDD5] rounded-2xl p-4 min-h-[320px] flex flex-col justify-between border border-slate-200">
              <div className="bg-[#075E54] text-white p-3 rounded-t-xl -mx-4 -mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center font-bold text-xs">م</div>
                  <div className="text-xs font-bold">بوت مجيب | تأكيد فوري</div>
                </div>
                <span className="text-[10px] bg-emerald-500/25 px-2 py-0.5 rounded font-mono">Order: #{activeSimId?.slice(0,4)}</span>
              </div>

              <div className="space-y-3 mt-4 flex-1 overflow-y-auto max-h-[220px]">
                <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                  مرحباً بك! تم استلام طلبك بقيمة <strong>{simAmount} ريال</strong>. هل ترغب بتأكيد شحن طلبك الآن؟
                </div>

                {simStep !== "pending_confirm" && (
                  <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                    نعم، أكيد تأكيد الطلب ✅
                  </div>
                )}

                {(simStep === "pending_gps" || simStep === "pending_upsell" || simStep === "completed") && (
                  <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                    شكراً لتأكيد الطلب! فضلاً أرسل موقعك الجغرافي (GPS) لتسهيل التسليم.
                  </div>
                )}

                {simStep !== "pending_confirm" && simStep !== "pending_gps" && (
                  <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                    📍 مشاركة الإحداثيات (Riyadh: 24.71, 46.67)
                  </div>
                )}

                {(simStep === "pending_upsell" || simStep === "completed") && (
                  <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                    موقعك معتمد. بمناسبة تأكيد الطلب، هل تود إضافة عطر 'بريز الخليج الفاخر' بخصم 30% بسعر 99 ريال فقط؟
                  </div>
                )}

                {simStep === "completed" && (
                  <>
                    <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                      نعم، أريد إضافة العطر! 🧴
                    </div>
                    <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed text-emerald-800 font-bold border border-emerald-250">
                      رائع! تم تحديث قيمة الفاتورة إلى {simAmount} ريال ومزامنة الطلب فوراً في Google Sheets.
                    </div>
                  </>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200/50">
                {simStep === "pending_confirm" && (
                  <div className="flex gap-2">
                    <button onClick={()=>handleSimAction("confirm")} className="flex-1 bg-[#25D366] text-white p-2 text-xs font-bold rounded-xl shadow">تأكيد الطلب ✅</button>
                    <button onClick={()=>setSimStep("ready")} className="bg-white text-slate-500 border border-slate-200 p-2 text-xs font-bold rounded-xl">إلغاء</button>
                  </div>
                )}
                {simStep === "pending_gps" && (
                  <button onClick={()=>handleSimAction("share_location")} className="w-full bg-blue-600 text-white p-2 text-xs font-bold rounded-xl shadow">إرسال إحداثيات الموقع (GPS) 📍</button>
                )}
                {simStep === "pending_upsell" && (
                  <div className="flex gap-2">
                    <button onClick={()=>handleSimAction("accept_upsell")} className="flex-1 bg-emerald-600 text-white p-2 text-xs font-bold rounded-xl shadow">نعم، إضافة المنتج المقترح 🧴</button>
                    <button onClick={()=>handleSimAction("reject_upsell")} className="flex-1 bg-slate-100 text-slate-600 p-2 text-xs font-bold rounded-xl">لا شكراً، شحن الطلب الأصلي</button>
                  </div>
                )}
                {simStep === "completed" && (
                  <div className="space-y-2">
                    <div className="text-xs text-center text-emerald-700 bg-emerald-50 p-2 rounded-lg font-bold">✓ تمت محاكاة الدورة كاملة وتسجيلها بنجاح</div>
                    <button onClick={()=>setSimStep("ready")} className="w-full bg-slate-900 text-white p-2 text-xs font-bold rounded-xl">جرب مرة أخرى 🔄</button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-950 text-white p-5 rounded-2xl border border-slate-800">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">نشاط المزامنة المباشر</h4>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">تأكيد WABA:</span><span>{simStep !== "ready" && simStep !== "pending_confirm" ? "مكتمل ✓" : "بانتظار التأكيد"}</span></div>
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">إحداثيات GPS:</span><span>{simStep === "pending_upsell" || simStep === "completed" ? "مستلمة (24.71, 46.67)" : "بانتظار العميل"}</span></div>
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">العرض الإضافي (Upsell):</span><span>{simStep === "completed" ? "+99 ريال (مقبول)" : "لم يقترح بعد"}</span></div>
              <div className="flex justify-between pb-2"><span className="text-slate-400">Google Sheet:</span><span>{simStep === "completed" ? (s.google_sheets_sync_healthy ? "مكتمل ومزامن ✓" : "تمت المحاكاة لوحة محددة") : "قيد المعالجة"}</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </>}

  {tab === "legacy-orders" && (
    <section className="glass rounded-2xl p-5 mt-8 overflow-auto">
      <h2 className="text-xl font-black mb-5">سجل الطلبيات</h2>
      {orders.isLoading ? (
        <p>جاري التحميل…</p>
      ) : orders.data?.length ? (
        <table className="w-full text-sm">
          <thead className="text-slate-500 border-b border-slate-100">
            <tr>
              <th className="text-right p-3">الطلب</th>
              <th>القيمة</th>
              <th>الحالة</th>
              <th>المخاطرة</th>
              <th>الموقع (GPS)</th>
              <th>التاريخ</th>
            </tr>
          </thead>
          <tbody>
            {orders.data.map(o => (
              <tr key={o.id} className="border-b border-slate-50 hover:bg-slate-50/50">
                <td className="p-3 font-bold">#{o.external_order_number || o.id.slice(0, 8)}</td>
                <td className="text-center font-semibold">{o.amount} {o.currency}</td>
                <td className="text-center">
                  <span className={`status-${o.status} py-1 px-3 text-[11px]`}>
                    {statusLabel[o.status] || o.status}
                  </span>
                </td>
                <td className="text-center">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${o.risk_level === "high" ? "bg-red-100 text-red-700" : o.risk_level === "medium" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                    {o.risk_score}/100
                  </span>
                </td>
                <td className="text-center">
                  {o.gps_lat && o.gps_lng ? (
                    <a href={`https://www.google.com/maps?q=${o.gps_lat},${o.gps_lng}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-sky font-bold hover:underline">
                      <MapPin size={12} /> {o.gps_lat.slice(0, 5)}, {o.gps_lng.slice(0, 5)}
                    </a>
                  ) : (
                    <span className="text-slate-400 text-xs">غير محدد</span>
                  )}
                </td>
                <td className="text-center text-slate-500 text-xs">{new Date(o.created_at).toLocaleDateString("ar-SA")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="py-16 text-center text-slate-500">ستظهر الطلبيات هنا فور سحبها من متجرك أو إرسالها عبر API.</p>
      )}
    </section>
  )}
  
  {tab === "orders" && <OperationalDashboard summary={s} orders={orders.data || []}/>}
  {tab==="integrations"&&<ZeroFrictionOnboarding storeId={store.id} storeName={store.name} freeRemaining={s.free_pilot_remaining ?? 50} onReady={() => {summary.refetch();integrationStatus.refetch();waapiStatus.refetch();}}/>}
  {tab==="billing"&&<Billing storeId={store.id} shopifyConnected={Boolean(integrationStatus.data?.shopify?.connected)}/>}
  {tab==="privacy"&&<Privacy/>}
  </main></div>;
}

export default function App() {
  const [viewAdmin, setViewAdmin] = useState(location.pathname === "/admin");
  const me = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<User>("/api/auth/me")).data,
    retry: false,
  });
  const shopifyInstall = new URLSearchParams(location.search).get("shopify") === "ready";
  useEffect(() => {
    if (!me.data || !shopifyInstall) return;
    void api.post("/api/integrations/shopify/claim", {}).then(() => {
      history.replaceState({}, "", "/dashboard/integrations?connected=shopify");
      void me.refetch();
    }).catch(() => {
      // Keep the merchant signed in and return them to the connection screen.
      // The integration card exposes a clear retry path without an unhandled
      // promise or a blank Shopify hand-off.
      history.replaceState({}, "", "/dashboard/integrations?shopify=retry");
    });
  }, [me.data?.id, shopifyInstall]);

  const logout = async () => {
    await api.post("/api/auth/logout");
    location.reload();
  };

  if (me.isLoading)
    return <div className="min-h-screen grid place-items-center font-black">مُجيب</div>;
  if (!me.data)
    return <Auth onDone={() => me.refetch()} />;

  if (viewAdmin || location.pathname === "/admin") {
    return (
      <AdminCrm
        user={me.data}
        onLogout={logout}
        onSwitchToMerchant={() => {
          setViewAdmin(false);
          window.history.pushState({}, "", "/");
        }}
      />
    );
  }

  return (
    <Dashboard
      user={me.data}
      onLogout={logout}
    />
  );
}

