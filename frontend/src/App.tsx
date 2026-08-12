import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {
  BarChart3, Boxes, CheckCircle2, Clipboard, Code2, CreditCard, Link2,
  Download, LockKeyhole, LogOut, MessageCircle, PackageCheck, ShieldCheck, Sparkles,
  Trash2, TriangleAlert, ChevronRight, X, ArrowRightLeft, ShieldAlert, BadgePercent, HelpCircle,
  Zap, Coins, FileText, Search, Star, MapPin
} from "lucide-react";
import {api} from "./api";
import {launchEmbeddedSignup} from "./meta";
import type {Order, Summary, User} from "./types";

const statusLabel: Record<string,string> = {
  pending:"Ø¬Ø¯ÙŠØ¯", awaiting_customer:"Ø¨Ø§Ù†ØªØ¸Ø§Ø± Ø§Ù„Ø¹Ù…ÙŠÙ„", confirmed:"Ù…Ø¤ÙƒØ¯",
  cancelled:"Ù…Ù„ØºÙŠ", human_follow_up:"Ù…ØªØ§Ø¨Ø¹Ø© Ø¨Ø´Ø±ÙŠØ©", shipped:"ØªÙ… Ø§Ù„Ø´Ø­Ù†",
  delivered:"ØªÙ… Ø§Ù„ØªØ³Ù„ÙŠÙ…", returned:"Ù…Ø±ØªØ¬Ø¹",
};

// 12/10 Conversion Landing Page + Interactive Auth modal
function Auth({onDone}:{onDone:()=>void}) {
  const [mode,setMode]=useState<"login"|"register">("login");
  const [modalOpen,setModalOpen]=useState(false);
  const [error,setError]=useState("");

  // Simulator States
  const [simStatus, setSimStatus] = useState<"pending" | "confirmed" | "cancelled" | "typing">("pending");
  const [simSavings, setSimSavings] = useState(8420);

  // ROI Calculator States
  const [calcOrders, setCalcOrders] = useState(350);
  const [calcAov, setCalcAov] = useState(280);
  const [calcRto, setCalcRto] = useState(25);
  const [calcShipping, setCalcShipping] = useState(35);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError("");
    try { 
      await api.post(`/api/auth/${mode}`, Object.fromEntries(new FormData(e.currentTarget))); 
      if (mode === "register") (window as any).twq?.("event", "tw-re98e-reaq4", {});
      onDone(); 
    }
    catch (err: any) { 
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (typeof detail === 'string' ? detail : "ØªØ£ÙƒØ¯ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø¯Ø®Ù„Ø©"));
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

  const triggerSim = (status: "confirmed" | "cancelled") => {
    setSimStatus("typing");
    setTimeout(() => {
      setSimStatus(status);
      if (status === "confirmed") {
        setSimSavings(prev => prev + 320);
      } else {
        setSimSavings(prev => prev + 80); // saved shipping fee (35*2 + 10)
      }
    }, 1200);
  };

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
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-mint to-emerald-700 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-mint/20">Ù…</div>
            Ù…ÙØ¬ÙŠØ¨
          </a>
          <ul className="hidden md:flex gap-6 text-sm font-semibold text-slate-600">
            <li><a href="#problem" className="hover:text-sky transition-colors">Ø§Ù„Ù…Ø´ÙƒÙ„Ø©</a></li>
            <li><a href="#features" className="hover:text-sky transition-colors">Ø§Ù„Ù…Ù…ÙŠØ²Ø§Øª</a></li>
            <li><a href="#simulator" className="hover:text-sky transition-colors">ÙƒÙŠÙ ÙŠØ¹Ù…Ù„</a></li>
            <li><a href="#calculator" className="hover:text-sky transition-colors">Ø­Ø§Ø³Ø¨Ø© Ø§Ù„ØªÙˆÙÙŠØ±</a></li>
            <li><a href="#pricing" className="hover:text-sky transition-colors">Ø§Ù„Ø£Ø³Ø¹Ø§Ø±</a></li>
          </ul>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => openAuth("login")} className="text-sm font-bold text-blue-deep hover:text-sky px-3 py-2 transition-colors">ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„</button>
          <button onClick={() => openAuth("register")} className="rounded-xl btn-gold text-sm font-black px-5 py-2.5 shadow-md">Ø§Ø¨Ø¯Ø£ Ù…Ø¬Ø§Ù†Ø§Ù‹ ðŸš€</button>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="pt-32 pb-20 px-6 max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold shadow-sm">
            <Sparkles size={14} className="text-gold animate-pulse" />
            <span>Ù†Ø¸Ø§Ù… Ø¥ÙŠØ±Ø§Ø¯Ø§Øª ÙˆØ§ØªØ³Ø§Ø¨ Ø§Ù„Ø°ÙƒÙŠ Ø§Ù„Ø£ÙˆÙ„ Ù„Ù„Ù…ØªØ§Ø¬Ø± Ø§Ù„Ø®Ù„ÙŠØ¬ÙŠØ©</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-blue-deep leading-tight">
            Ø§Ø³ØªØ±Ø¬Ø¹ Ø£Ø±Ø¨Ø§Ø­Ùƒ Ø§Ù„Ø¶Ø§Ø¦Ø¹Ø© Ù…Ù† <span className="text-transparent bg-clip-text bg-gradient-to-l from-emerald-600 to-teal-800">Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù…</span> ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ ÙˆØ¨Ø°ÙƒØ§Ø¡
          </h1>
          <p className="text-slate-600 text-lg leading-relaxed max-w-xl">
            Ù…Ø¬ÙŠØ¨ ÙŠØ¤ÙƒØ¯ Ø·Ù„Ø¨Ø§Øª Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù… (COD)ØŒ ÙŠØ¬Ù…Ø¹ Ù…ÙˆØ§Ù‚Ø¹ GPS Ø§Ù„Ø¯Ù‚ÙŠÙ‚Ø© Ù„Ù„Ø¹Ù…Ù„Ø§Ø¡ØŒ ÙˆÙŠØ®ÙÙ‘Ø¶ Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª RTO Ù…Ù† 30% Ø¥Ù„Ù‰ 12% Ø¯ÙˆÙ† ØªØºÙŠÙŠØ± Ø´Ø±ÙƒØ© Ø´Ø­Ù†Ùƒ.
          </p>
          <div className="flex flex-wrap gap-4 pt-2">
            <button onClick={() => openAuth("register")} className="rounded-xl btn-gold text-lg font-black px-8 py-4 shadow-xl hover:shadow-2xl shadow-emerald-500/10">
              Ø§Ø¨Ø¯Ø£ ØªØ¬Ø±Ø¨ØªÙƒ Ø§Ù„Ù…Ø¬Ø§Ù†ÙŠØ© (50 Ø·Ù„Ø¨)
            </button>
            <a href="#calculator" className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-ink font-bold px-8 py-4 flex items-center justify-center gap-2">
              Ø§Ø­Ø³Ø¨ Ø£Ø±Ø¨Ø§Ø­ Ù…ØªØ¬Ø±Ùƒ
            </a>
          </div>
          <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-100 text-slate-500">
            <div>
              <p className="text-2xl font-black text-blue-deep">98%</p>
              <p className="text-xs">Ù†Ø³Ø¨Ø© Ø§Ù„ÙˆØµÙˆÙ„ Ø¨Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨</p>
            </div>
            <div>
              <p className="text-2xl font-black text-blue-deep">94.2%</p>
              <p className="text-xs">Ø¯Ù‚Ø© ÙØ±Ø² ÙˆØªØµÙ†ÙŠÙ Ø§Ù„Ø·Ù„Ø¨Ø§Øª</p>
            </div>
            <div>
              <p className="text-2xl font-black text-blue-deep">120+ Ù…ØªØ¬Ø±</p>
              <p className="text-xs">ÙŠØ¹ØªÙ…Ø¯ÙˆÙ† Ø¹Ù„Ù‰ Ø®ÙˆØ§Ø±Ø²Ù…ÙŠØ§ØªÙ†Ø§</p>
            </div>
          </div>
        </div>

        {/* Live Simulator Widget */}
        <div id="simulator" className="lg:col-span-5">
          <div className="bg-white rounded-3xl p-6 shadow-2xl border border-slate-100 relative">
            <div className="absolute -top-3 -left-3 bg-mint text-white text-xs font-black px-3 py-1 rounded-full shadow">Ù…Ø­Ø§ÙƒØ§Ø© ØªÙØ§Ø¹Ù„ÙŠØ© Ø­ÙŠØ©</div>
            <p className="text-xs text-slate-400 font-bold mb-4 uppercase tracking-wider">ØªÙØ§Ø¹Ù„ Ù…Ø¹ Ø§Ù„Ø±Ø³Ø§Ù„Ø© ÙˆØ´Ø§Ù‡Ø¯ Ø§Ù„Ù†ØªÙŠØ¬Ø© ÙÙŠ Ù„ÙˆØ­Ø© Ø§Ù„ØªØ­ÙƒÙ…:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* WhatsApp Mockup */}
              <div className="bg-[#E5DDD5] rounded-2xl p-3 border border-slate-200 min-h-[300px] flex flex-col justify-between">
                <div className="bg-[#075E54] text-white p-2 rounded-t-xl -mx-3 -mt-3 flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center font-bold text-xs">Ù…</div>
                  <div className="text-xs font-bold">Ù…ÙØ¬ÙŠØ¨ | ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨Ø§Øª</div>
                </div>
                
                <div className="space-y-2 mt-4 overflow-y-auto flex-1">
                  <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                    Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÙŠÙƒÙ… Ù…Ù† Ù…ØªØ¬Ø± Ø§Ù„Ø¹Ø·ÙˆØ± Ø§Ù„ÙØ§Ø®Ø±Ø© ðŸŒ¸.
                    Ø·Ù„Ø¨Ùƒ Ø±Ù‚Ù… <strong>#1042</strong> Ø¨Ù‚ÙŠÙ…Ø© <strong>320 Ø±ÙŠØ§Ù„</strong> Ø¬Ø§Ù‡Ø² Ù„Ù„Ø´Ø­Ù†. Ù‡Ù„ ØªØ±ØºØ¨ Ø¨ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨ Ø§Ù„Ø¢Ù†ØŸ
                  </div>

                  {simStatus === "typing" && (
                    <div className="bg-white p-2.5 rounded-lg text-xs max-w-[40%] shadow-sm text-slate-400 animate-pulse">
                      ÙŠÙƒØªØ¨ Ø§Ù„Ø¢Ù†...
                    </div>
                  )}

                  {simStatus === "confirmed" && (
                    <>
                      <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                        Ù†Ø¹Ù…ØŒ Ø£ÙƒÙŠØ¯
                      </div>
                      <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                        Ø±Ø§Ø¦Ø¹! ØªÙ… ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨Ùƒ Ø¨Ù†Ø¬Ø§Ø­ ÙˆØ³Ù†Ù‚ÙˆÙ… Ø¨Ø´Ø­Ù†Ù‡ ÙÙˆØ±Ø§Ù‹. Ø´ÙƒØ±Ø§Ù‹ Ù„Ùƒ âœ¨
                      </div>
                    </>
                  )}

                  {simStatus === "cancelled" && (
                    <>
                      <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                        Ø¥Ù„ØºØ§Ø¡ Ø§Ù„Ø·Ù„Ø¨
                      </div>
                      <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed text-red-700">
                        ØªÙ… Ø¥Ù„ØºØ§Ø¡ Ø§Ù„Ø·Ù„Ø¨ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø±ØºØ¨ØªÙƒ. Ø´ÙƒØ±Ø§Ù‹ Ù„Ùƒ ÙˆØ³Ù†Ù‚ÙˆÙ… Ø¨ØªØ­Ø¯ÙŠØ« Ø§Ù„Ù…ØªØ¬Ø±.
                      </div>
                    </>
                  )}
                </div>

                {simStatus === "pending" && (
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <button onClick={() => triggerSim("confirmed")} className="bg-[#25D366] text-white font-bold p-2 rounded-xl text-xs shadow hover:bg-emerald-600 transition-colors">
                      Ù†Ø¹Ù…ØŒ Ø£ÙƒÙŠØ¯ âœ…
                    </button>
                    <button onClick={() => triggerSim("cancelled")} className="bg-white text-red-600 border border-red-200 font-bold p-2 rounded-xl text-xs hover:bg-red-50 transition-colors">
                      Ø¥Ù„ØºØ§Ø¡ Ø§Ù„Ø·Ù„Ø¨ âŒ
                    </button>
                  </div>
                )}

                {simStatus !== "pending" && simStatus !== "typing" && (
                  <button onClick={() => setSimStatus("pending")} className="mt-2 w-full bg-slate-800 text-white font-bold p-2 rounded-xl text-xs hover:bg-slate-900 transition-colors">
                    Ø¥Ø¹Ø§Ø¯Ø© Ø§Ù„ØªØ¬Ø±Ø¨Ø© ðŸ”„
                  </button>
                )}
              </div>

              {/* Mini Dashboard widget mockup */}
              <div className="bg-slate-900 text-white rounded-2xl p-4 flex flex-col justify-between">
                <div>
                  <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Ù„ÙˆØ­Ø© Ø§Ù„ØªØ­ÙƒÙ… Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠØ©</h4>
                  <div className="mt-3 flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs">Ø·Ù„Ø¨ #1042</span>
                    {simStatus === "pending" && <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full font-bold">Ø¨Ø§Ù†ØªØ¸Ø§Ø± Ø§Ù„Ø¹Ù…ÙŠÙ„</span>}
                    {simStatus === "typing" && <span className="text-[10px] bg-sky-500/20 text-sky-400 px-2 py-0.5 rounded-full font-bold animate-pulse">Ø¬Ø§Ø±ÙŠ Ø§Ù„Ù…ØªØ§Ø¨Ø¹Ø©</span>}
                    {simStatus === "confirmed" && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-bold">Ù…Ø¤ÙƒØ¯</span>}
                    {simStatus === "cancelled" && <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full font-bold">Ù…Ù„ØºÙŠ</span>}
                  </div>
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between"><span className="text-slate-400">Ø§Ù„Ù…Ù†ØµØ©:</span><span className="font-bold">Ø³Ù„Ø© (Salla)</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Ø·Ø±ÙŠÙ‚Ø© Ø§Ù„Ø¯ÙØ¹:</span><span className="font-bold">COD</span></div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Ø¥Ø¬Ù…Ø§Ù„ÙŠ Ø§Ù„ØªÙˆÙÙŠØ± Ù‡Ø°Ø§ Ø§Ù„Ø´Ù‡Ø±:</span>
                  <strong className="text-2xl text-mint font-black block mt-1 transition-all duration-500">{simSavings.toLocaleString()} Ø±ÙŠØ§Ù„</strong>
                </div>
              </div>

            </div>
          </div>
        </div>
      </header>

      {/* The Problem Section */}
      <section id="problem" className="bg-white py-20 px-6 border-y border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">Ù„Ù…Ø§Ø°Ø§ ØªÙÙ‚Ø¯ Ù…ØªØ§Ø¬Ø± Ø§Ù„Ø®Ù„ÙŠØ¬ 30% Ù…Ù† Ø£Ø±Ø¨Ø§Ø­Ù‡Ø§ØŸ</h2>
            <p className="text-slate-500">Ø·Ø±Ù‚ ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨Ø§Øª Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù… Ø§Ù„ØªÙ‚Ù„ÙŠØ¯ÙŠØ© ØªØ¯Ù…Ø± Ù‡ÙˆØ§Ù…Ø´ Ø§Ù„Ø±Ø¨Ø­ ÙˆØªØ³ØªÙ†Ø²Ù ÙˆÙ‚Øª Ø§Ù„ÙØ±ÙŠÙ‚.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <article className="bg-slate-50 border border-slate-100 rounded-3xl p-8 space-y-5">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center"><ShieldAlert size={24} /></div>
              <h3 className="text-xl font-bold text-blue-deep">Ø§Ù„ÙÙˆØ¶Ù‰ Ø§Ù„ÙŠØ¯ÙˆÙŠØ© Ø§Ù„ØªÙ‚Ù„ÙŠØ¯ÙŠØ© (Ù‚Ø¨Ù„ Ù…Ø¬ÙŠØ¨)</h3>
              <ul className="space-y-3 text-slate-600 text-sm">
                <li className="flex items-start gap-2">âŒ <span className="font-medium">ØªÙƒØ§Ù„ÙŠÙ Ø´Ø­Ù† Ø°Ù‡Ø§Ø¨ ÙˆØ¹ÙˆØ¯Ø© Ù„Ù„Ù…Ø´ØªØ±ÙŠÙ† Ø§Ù„ÙˆÙ‡Ù…ÙŠÙŠÙ†.</span></li>
                <li className="flex items-start gap-2">âŒ <span className="font-medium">Ø³Ø§Ø¹Ø§Øª Ø·ÙˆÙŠÙ„Ø© ØªØ¶ÙŠØ¹ ÙŠÙˆÙ…ÙŠØ§Ù‹ ÙÙŠ Ù…ÙƒØ§Ù„Ù…Ø§Øª Ø§Ù„ØªØ£ÙƒÙŠØ¯.</span></li>
                <li className="flex items-start gap-2">âŒ <span className="font-medium">Ø¹Ø¯Ù… Ø§Ù„Ø±Ø¯ Ù…Ù† Ø§Ù„Ø¹Ù…Ù„Ø§Ø¡ ÙŠØ¹Ù„Ù‚ Ø§Ù„Ø·Ù„Ø¨Ø§Øª Ù„Ø£ÙŠØ§Ù….</span></li>
                <li className="flex items-start gap-2">âŒ <span className="font-medium">Ù†Ø³Ø¨ Ù…Ø±ØªØ¬Ø¹Ø§Øª RTO ÙƒØ§Ø±Ø«ÙŠØ© ØªØµÙ„ Ø¥Ù„Ù‰ 30% ÙˆØ£ÙƒØ«Ø±.</span></li>
              </ul>
            </article>

            <article className="bg-emerald-950 text-white rounded-3xl p-8 space-y-5 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl"></div>
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-mint flex items-center justify-center"><CheckCircle2 size={24} /></div>
              <h3 className="text-xl font-bold">Ø§Ù„ØªØ£ÙƒÙŠØ¯ Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ Ø¨Ø°ÙƒØ§Ø¡ 180IQ (Ù…Ø¹ Ù…Ø¬ÙŠØ¨)</h3>
              <ul className="space-y-3 text-emerald-100 text-sm">
                <li className="flex items-start gap-2">âœ… <span className="font-medium">Ø¥Ù„ØºØ§Ø¡ ÙÙˆØ±ÙŠ ÙˆØªÙ„Ù‚Ø§Ø¦ÙŠ Ù„Ù„Ø·Ù„Ø¨Ø§Øª Ø§Ù„ÙˆÙ‡Ù…ÙŠØ© Ù‚Ø¨Ù„ Ø§Ù„Ø´Ø­Ù† ÙˆØ§Ù„ØªØºÙ„ÙŠÙ.</span></li>
                <li className="flex items-start gap-2">âœ… <span className="font-medium">ØªÙˆØ§ØµÙ„ ÙÙˆØ±ÙŠ Ø¹Ø¨Ø± Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ ÙŠØ¹Ø·ÙŠ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø®ÙŠØ§Ø± ØªØ£ÙƒÙŠØ¯ Ø¨Ø¶ØºØ·Ø© Ø²Ø±.</span></li>
                <li className="flex items-start gap-2">âœ… <span className="font-medium">Ø¬Ù…Ø¹ Ù…ÙˆØ§Ù‚Ø¹ GPS Ø¯Ù‚ÙŠÙ‚Ø© Ù„Ø¶Ù…Ø§Ù† ØªØ³Ù„ÙŠÙ… Ø§Ù„Ø´Ø­Ù†Ø§Øª Ø¨Ù†Ø³Ø¨Ø© 100%.</span></li>
                <li className="flex items-start gap-2">âœ… <span className="font-medium">Ø§Ù†Ø®ÙØ§Ø¶ Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª Ù„Ø£Ù‚Ù„ Ù…Ù† 12%Ø› Ù„ØªÙˆÙØ± Ø¢Ù„Ø§Ù Ø§Ù„Ø±ÙŠØ§Ù„Ø§Øª.</span></li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      {/* Core Mujeeb SaaS Services Grid */}
      <section id="features" className="py-20 px-6 bg-slate-50/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <span className="text-xs text-sky font-black uppercase tracking-widest block">Ø§Ù„Ø®Ø¯Ù…Ø§Øª ÙˆØ§Ù„Ù…ÙŠØ²Ø§Øª Ø§Ù„Ù…ØªÙƒØ§Ù…Ù„Ø©</span>
            <h2 className="text-3xl font-black text-blue-deep">Ù…Ù†Ø¸ÙˆÙ…Ø© Ø°ÙƒÙŠØ© Ù…ØªÙƒØ§Ù…Ù„Ø© Ù„Ø­Ù…Ø§ÙŠØ© ÙˆØ¥Ø¯Ø§Ø±Ø© Ø·Ù„Ø¨ÙŠØ§ØªÙƒ</h2>
            <p className="text-slate-500 text-sm">Une multitude d'outils et de fonctionnalitÃ©s gratuites pour vous guider vers le succÃ¨s et la rÃ©ussite.</p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            
            {/* Service 1 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><Link2 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ø±Ø¨Ø· Ø§Ù„Ù…ØªØ§Ø¬Ø± Ø¨Ø¶ØºØ·Ø© Ø²Ø±</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">One-Click Store Connect</p>
              <p className="text-xs text-slate-500 leading-relaxed">Ø±Ø¨Ø· Ø±Ø³Ù…ÙŠ ÙˆØ³Ø±ÙŠØ¹ Ù…Ø¹ Ù…Ù†ØµØ§Øª Ø³Ù„Ø© (Salla) ÙˆØ²Ø¯ (Zid) ÙˆØ´ÙˆØ¨ÙŠÙØ§ÙŠ (Shopify) Ù„Ø³Ø­Ø¨ ÙˆØ¥Ø¯Ø§Ø±Ø© Ø§Ù„Ø·Ù„Ø¨Ø§Øª ÙÙˆØ±Ø§Ù‹.</p>
            </article>

            {/* Service 2 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><MessageCircle size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">ØªÙØ¹ÙŠÙ„ Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ (WABA) Ø§Ù„ÙÙˆØ±ÙŠ</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">One-Click WABA Integration</p>
              <p className="text-xs text-slate-500 leading-relaxed">Ø±Ø¨Ø· Ø­Ø³Ø§Ø¨ Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ Ø§Ù„Ø®Ø§Øµ Ø¨Ù…ØªØ¬Ø±Ùƒ Ø¨Ø¶ØºØ·Ø© ÙˆØ§Ø­Ø¯Ø© Ù…Ù† Ø®Ù„Ø§Ù„ Ù†Ø¸Ø§Ù… Ø§Ù„ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ù…Ø¯Ù…Ø¬ Ù…Ù† Meta.</p>
            </article>

            {/* Service 3 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><CheckCircle2 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨Ø§Øª Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">Automated Chatbot Confirmation</p>
              <p className="text-xs text-slate-500 leading-relaxed">ÙŠØªÙˆÙ„Ù‰ Ø§Ù„Ø¨ÙˆØª Ø§Ù„ØªÙØ§Ø¹Ù„ Ø§Ù„ÙÙˆØ±ÙŠ Ù…Ø¹ Ø¹Ù…Ù„Ø§Ø¦Ùƒ Ø¨Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ Ù„ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨ÙŠØ§Øª Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù… ÙˆÙÙ„ØªØ±Ø© Ø§Ù„ÙˆÙ‡Ù…ÙŠÙŠÙ†.</p>
            </article>

            {/* Service 4 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><MapPin size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ø§Ù„ØªØ­Ù‚Ù‚ Ø§Ù„Ø¬ØºØ±Ø§ÙÙŠ ÙˆØªØ­Ø¯ÙŠØ« Ø§Ù„Ø¹Ù†Ø§ÙˆÙŠÙ†</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">Auto-update Salla/Zid Address</p>
              <p className="text-xs text-slate-500 leading-relaxed">ÙŠØ¬Ù…Ø¹ Ø§Ù„Ø¨ÙˆØª Ø¥Ø­Ø¯Ø§Ø«ÙŠØ§Øª GPS ÙˆÙŠÙƒØªØ¨Ù‡Ø§ Ù…Ø¨Ø§Ø´Ø±Ø© ÙÙŠ ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø´Ø­Ù† Ø¨Ø³Ù„Ø©/Ø²Ø¯ Ù„ØªØªÙ…ÙƒÙ† Ù…Ù† Ø·Ø¨Ø§Ø¹Ø© Ø¨ÙˆÙ„ÙŠØµØ© Ø§Ù„ØªÙˆØµÙŠÙ„ ÙÙˆØ±Ø§.</p>
            </article>

            {/* Service 5 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><BadgePercent size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ø¹Ø±ÙˆØ¶ Ø§Ù„Ø¨ÙŠØ¹ Ø§Ù„Ø¥Ø¶Ø§ÙÙŠ (Upsell)</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">Post-Confirmation Upsell</p>
              <p className="text-xs text-slate-500 leading-relaxed">Ø§Ù‚ØªØ±Ø§Ø­ Ø¹Ø±ÙˆØ¶ Ø¥Ø¶Ø§ÙÙŠØ© Ø°ÙƒÙŠØ© Ù„Ù„Ø¹Ù…ÙŠÙ„ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ ÙÙŠ Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ ÙÙˆØ± ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨Ù‡ Ù„Ø²ÙŠØ§Ø¯Ø© Ø£Ø±Ø¨Ø§Ø­Ùƒ.</p>
            </article>

            {/* Service 6 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><FileText size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ø§Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ù…Ø¹ Google Sheets</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">Google Sheets Instant Sync</p>
              <p className="text-xs text-slate-500 leading-relaxed">ØªØ­Ø¯ÙŠØ« ÙÙˆØ±ÙŠ ÙˆØªÙ„Ù‚Ø§Ø¦ÙŠ Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¹Ù…Ù„Ø§Ø¡ ÙˆØ­Ø§Ù„Ø© Ø·Ù„Ø¨ÙŠØ§ØªÙ‡Ù… ÙˆÙ…ÙˆØ§Ù‚Ø¹Ù‡Ù… ÙÙŠ Ø¬Ø¯ÙˆÙ„ Ø¨ÙŠØ§Ù†Ø§Øª Ø¬ÙˆØ¬Ù„ Ø§Ù„Ø®Ø§Øµ Ø¨Ùƒ.</p>
            </article>

            {/* Service 7 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><HelpCircle size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ø§Ù„ØªØ¯Ø®Ù„ Ø§Ù„Ø¨Ø´Ø±ÙŠ ÙˆØ§Ù„ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ø°ÙƒÙŠ</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">Smart Agent Handover</p>
              <p className="text-xs text-slate-500 leading-relaxed">ÙÙŠ Ø­Ø§Ù„ Ø·Ø±Ø­ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø³Ø¤Ø§Ù„Ø§Ù‹ Ù…Ø¹Ù‚Ø¯Ø§Ù‹ Ø£Ùˆ ØªØ¹Ø¯ÙŠÙ„Ø§Ù‹ØŒ ÙŠØªÙˆÙ‚Ù Ø§Ù„Ø¨ÙˆØª ÙÙˆØ±Ø§Ù‹ ÙˆÙŠØ­ÙŠÙ„ Ø§Ù„Ø¯Ø±Ø¯Ø´Ø© Ù„ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„ÙˆØ§Ø±Ø¯ Ø§Ù„Ù…Ø´ØªØ±Ùƒ.</p>
            </article>

            {/* Service 8 */}
            <article className="bg-white border border-slate-100 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-shadow">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky flex items-center justify-center"><BarChart3 size={20}/></div>
              <h3 className="font-bold text-base text-blue-deep">Ù„ÙˆØ­Ø© ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ù…Ø®Ø§Ø·Ø± ÙˆØ§Ù„ØªØ­Ù„ÙŠÙ„Ø§Øª</h3>
              <p className="text-xs text-slate-400 font-bold block -mt-2">AI Analytics & Risk Dashboard</p>
              <p className="text-xs text-slate-500 leading-relaxed">Ù…Ø±Ø§Ù‚Ø¨Ø© ØªÙØµÙŠÙ„ÙŠØ© Ù„Ù…Ø¹Ø¯Ù„Ø§Øª Ø§Ù„ØªØ³Ù„ÙŠÙ… ÙˆÙ…Ø³ØªÙˆÙŠØ§Øª Ø§Ù„Ù…Ø®Ø§Ø·Ø± ÙˆØ³Ù„ÙˆÙƒ Ø§Ù„Ù…Ø´ØªØ±ÙŠ Ù„Ø¶Ù…Ø§Ù† ØªØ­Ø³ÙŠÙ† Ù…Ø³ØªÙ…Ø± Ù„Ù„Ù‡ÙˆØ§Ù…Ø´.</p>
            </article>

          </div>
        </div>
      </section>

      {/* ROI Savings Calculator */}
      <section id="calculator" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">Ø­Ø§Ø³Ø¨Ø© Ø§Ù„Ø¹Ø§Ø¦Ø¯ Ø§Ù„Ø§Ø³ØªØ«Ù…Ø§Ø±ÙŠ Ø§Ù„ØªÙØ§Ø¹Ù„ÙŠØ©</h2>
            <p className="text-slate-500">Ø­Ø±Ùƒ Ø§Ù„Ù…Ø¤Ø´Ø±Ø§Øª Ù„ØªØ±Ù‰ Ù…Ù‚Ø¯Ø§Ø± Ø§Ù„Ù…Ø¨Ø§Ù„Øº Ø§Ù„Ù…Ù‡Ø¯ÙˆØ±Ø© ÙˆØ£Ø±Ø¨Ø§Ø­Ùƒ Ø§Ù„Ù…Ø³ØªØ±Ø¯Ø© Ø¨Ø¯Ù‚Ø©.</p>
          </div>

          <div className="bg-white rounded-3xl p-8 lg:p-12 border border-slate-100 shadow-2xl grid lg:grid-cols-12 gap-10">
            {/* Input Controls */}
            <div className="lg:col-span-7 space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>Ø¹Ø¯Ø¯ Ø·Ù„Ø¨Ø§Øª Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù… Ø´Ù‡Ø±ÙŠØ§Ù‹:</span>
                  <span className="text-sky">{calcOrders.toLocaleString()} Ø·Ù„Ø¨</span>
                </div>
                <input type="range" min="50" max="5000" step="50" value={calcOrders} onChange={e=>setCalcOrders(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>Ù…ØªÙˆØ³Ø· Ù‚ÙŠÙ…Ø© Ø§Ù„Ø·Ù„Ø¨ (AOV):</span>
                  <span className="text-sky">{calcAov} Ø±ÙŠØ§Ù„</span>
                </div>
                <input type="range" min="50" max="1500" step="10" value={calcAov} onChange={e=>setCalcAov(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª Ø§Ù„Ø­Ø§Ù„ÙŠØ© (RTO):</span>
                  <span className="text-rose-600">{calcRto}%</span>
                </div>
                <input type="range" min="5" max="50" step="1" value={calcRto} onChange={e=>setCalcRto(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-rose-500"/>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between font-bold text-sm">
                  <span>ØªÙƒÙ„ÙØ© Ø§Ù„Ø´Ø­Ù† Ù„Ø´Ø±ÙƒØ© Ø§Ù„Ø´Ø­Ù† (Ø°Ù‡Ø§Ø¨ ÙˆØ¹ÙˆØ¯Ø©):</span>
                  <span className="text-sky">{calcShipping} Ø±ÙŠØ§Ù„</span>
                </div>
                <input type="range" min="15" max="100" step="5" value={calcShipping} onChange={e=>setCalcShipping(Number(e.target.value))} className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky"/>
              </div>
            </div>

            {/* Results Panel */}
            <div className="lg:col-span-5 bg-blue-deep text-white rounded-2xl p-8 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"></div>
              <div className="space-y-6 relative z-10">
                <div>
                  <span className="text-xs text-rose-300 font-bold uppercase tracking-wider block">Ø§Ù„Ø®Ø³Ø§Ø±Ø© Ø§Ù„Ø´Ù‡Ø±ÙŠØ© Ø§Ù„Ø­Ø§Ù„ÙŠØ© Ù„Ù…ØªØ¬Ø±Ùƒ:</span>
                  <strong className="text-xl text-rose-200 line-through block mt-1">{totalCurrentLoss.toLocaleString()} Ø±ÙŠØ§Ù„</strong>
                </div>
                <div>
                  <span className="text-xs text-emerald-300 font-bold uppercase tracking-wider block">Ø§Ù„Ø£Ø±Ø¨Ø§Ø­ Ø§Ù„Ù…Ø³ØªØ±Ø¯Ø© Ø´Ù‡Ø±ÙŠØ§Ù‹ Ù…Ø¹ Ù…Ø¬ÙŠØ¨:</span>
                  <strong className="text-4xl text-mint font-black block mt-2">{totalSavedRevenue.toLocaleString()} Ø±ÙŠØ§Ù„</strong>
                </div>
                <p className="text-xs text-blue-200 leading-relaxed">
                  Ø§Ù„Ø­Ø³Ø§Ø¨Ø§Øª ØªÙØªØ±Ø¶ Ø§Ù†Ø®ÙØ§Ø¶ Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª Ø¥Ù„Ù‰ <strong>12%</strong>ØŒ ÙˆØªÙˆÙÙŠØ± ØªÙƒØ§Ù„ÙŠÙ Ø§Ù„Ø´Ø­Ù† Ø§Ù„Ù…Ù‡Ø¯Ø± ÙˆØªØ¬Ù‡ÙŠØ² Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª.
                </p>
              </div>

              <button onClick={() => openAuth("register")} className="mt-8 w-full btn-gold font-black py-4 rounded-xl shadow-lg relative z-10 border-none text-base">
                ÙˆÙØ± {totalSavedRevenue.toLocaleString()} Ø±ÙŠØ§Ù„ Ø´Ù‡Ø±ÙŠØ§Ù‹ ÙˆØ§Ø¨Ø¯Ø£ Ù…Ø¬Ø§Ù†Ø§Ù‹
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-slate-50 py-20 px-6 border-t border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <h2 className="text-3xl font-black text-blue-deep">Ø§Ø³ØªØ«Ù…Ø± Ø¬Ø²Ø¡Ø§Ù‹ ØµØºÙŠØ±Ø§Ù‹ Ù…Ù…Ø§ Ù†ÙˆÙØ±Ù‡ Ù„Ùƒ</h2>
            <p className="text-slate-500">Ø¨Ø§Ù‚Ø§Øª Ø´ÙØ§ÙØ© ÙˆØ¨Ø³ÙŠØ·Ø©ØŒ Ø¨Ø¯ÙˆÙ† Ø±Ø³ÙˆÙ… Ù…Ø®ÙÙŠØ© Ø£Ùˆ Ø¹Ù…ÙˆÙ„Ø§Øª Ø¹Ù„Ù‰ Ø§Ù„Ø±Ø³Ø§Ø¦Ù„.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <article className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between hover:shadow-xl transition-all">
              <div>
                <p className="font-black text-xl text-blue-deep">Ø§Ù„Ø¨Ø§Ù‚Ø© Ø§Ù„Ù…Ø¨ØªØ¯Ø¦Ø© (Starter)</p>
                <p className="text-slate-400 text-sm mt-1">Ù„Ù„Ù…ØªØ§Ø¬Ø± Ø§Ù„Ø¬Ø¯ÙŠØ¯Ø© ÙˆØ§Ù„Ù†Ø§Ø´Ø¦Ø©</p>
                <strong className="text-3xl font-black text-sky block mt-6">299 Ø±ÙŠØ§Ù„ <span className="text-xs font-normal text-slate-400">/Ø´Ù‡Ø±ÙŠØ§Ù‹</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">âœ“ ØªØ£ÙƒÙŠØ¯ ØªÙ„Ù‚Ø§Ø¦ÙŠ Ø­ØªÙ‰ 300 Ø·Ù„Ø¨/Ø´Ù‡Ø±</li>
                  <li className="flex items-center gap-2 font-bold text-emerald-800">âœ“ Ù…ÙŠØ²Ø© Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù…ÙˆÙ‚Ø¹ GPS Ù…Ø´Ù…ÙˆÙ„Ø©</li>
                  <li className="flex items-center gap-2">âœ“ Ø±Ø¨Ø· ÙÙˆØ±ÙŠ Ù…Ø¹ Ø³Ù„Ø©ØŒ Ø²Ø¯ØŒ ÙˆØ´ÙˆØ¨ÙŠÙØ§ÙŠ</li>
                  <li className="flex items-center gap-2 text-slate-400">âœ— ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„ÙˆØ§Ø±Ø¯ Ø§Ù„Ù…Ø´ØªØ±Ùƒ Ù„Ù„ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ø¨Ø´Ø±ÙŠ</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full bg-slate-100 text-slate-700 font-bold p-3 rounded-xl hover:bg-slate-200 transition-colors">Ø§Ù„Ø¨Ø¯Ø¡ Ù…Ø¬Ø§Ù†Ø§Ù‹</button>
            </article>

            <article className="bg-white border-2 border-emerald-500 rounded-3xl p-8 flex flex-col justify-between shadow-2xl relative">
              <span className="absolute -top-3 right-8 rounded-full bg-emerald-500 px-4 py-1 text-xs font-bold text-white shadow">ðŸš€ Ø§Ù„Ù…ÙˆØµÙ‰ Ø¨Ù‡Ø§ (180IQ)</span>
              <div>
                <p className="font-black text-xl text-blue-deep">Ø¨Ø§Ù‚Ø© Ø§Ù„Ù†Ù…Ùˆ (Growth)</p>
                <p className="text-slate-400 text-sm mt-1">ØªØ£ÙƒÙŠØ¯ Ù…ØªÙ‚Ø¯Ù… ÙˆØ°ÙƒØ§Ø¡ Ø§ØµØ·Ù†Ø§Ø¹ÙŠ ÙƒØ§Ù…Ù„</p>
                <strong className="text-3xl font-black text-sky block mt-6">599 Ø±ÙŠØ§Ù„ <span className="text-xs font-normal text-slate-400">/Ø´Ù‡Ø±ÙŠØ§Ù‹</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">âœ“ ØªØ£ÙƒÙŠØ¯ ØªÙ„Ù‚Ø§Ø¦ÙŠ Ø­ØªÙ‰ 5,000 Ø·Ù„Ø¨/Ø´Ù‡Ø±</li>
                  <li className="flex items-center gap-2 font-bold text-emerald-800">âœ“ Ø­Ù…Ø§ÙŠØ© Ø§Ù„ØªÙˆØµÙŠÙ„ Ø§Ù„ÙƒØ§Ù…Ù„Ø© (GPS + ÙØ­Øµ Ø§Ù„Ø¹Ù†Ø§ÙˆÙŠÙ†)</li>
                  <li className="flex items-center gap-2 font-bold text-blue-800">âœ“ ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø§Øª Ø§Ù„Ù…Ø´ØªØ±Ùƒ ÙˆØ§Ù„ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ø¨Ø´Ø±ÙŠ</li>
                  <li className="flex items-center gap-2">âœ“ Ù„ÙˆØ­Ø§Øª ØªØ­ÙƒÙ… Ù…ØªÙ‚Ø¯Ù…Ø© Ø¨Ø§Ù„ÙƒØ§Ù…Ù„ ÙˆØ¯Ø¹Ù… Ø£ÙˆÙ„ÙˆÙŠ</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full btn-gold font-bold p-3.5 rounded-xl shadow-lg border-none">Ø§Ù„Ø¨Ø¯Ø¡ Ù…Ø¬Ø§Ù†Ø§Ù‹</button>
            </article>

            <article className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between hover:shadow-xl transition-all">
              <div>
                <p className="font-black text-xl text-blue-deep">Ø¨Ø§Ù‚Ø© Ø§Ù„ØªÙˆØ³Ø¹ (Scale)</p>
                <p className="text-slate-400 text-sm mt-1">Ù„Ù„Ù…Ø§Ø±ÙƒØ§Øª Ø§Ù„ÙƒØ¨Ø±Ù‰ ÙˆÙ…ØªØ¹Ø¯Ø¯Ø© Ø§Ù„Ù…ØªØ§Ø¬Ø±</p>
                <strong className="text-3xl font-black text-sky block mt-6">1,199 Ø±ÙŠØ§Ù„ <span className="text-xs font-normal text-slate-400">/Ø´Ù‡Ø±ÙŠØ§Ù‹</span></strong>
                <ul className="mt-8 space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2">âœ“ ØªØ£ÙƒÙŠØ¯ ØªÙ„Ù‚Ø§Ø¦ÙŠ ØºÙŠØ± Ù…Ø­Ø¯ÙˆØ¯</li>
                  <li className="flex items-center gap-2">âœ“ Ø±Ø¨Ø· Ù…ØªØ§Ø¬Ø± Ù…ØªØ¹Ø¯Ø¯Ø© Ø¨Ù„ÙˆØ­Ø© ÙˆØ§Ø­Ø¯Ø©</li>
                  <li className="flex items-center gap-2">âœ“ ØªÙƒØ§Ù…Ù„ Ù…Ø¹ API Ø§Ù„Ù…Ø®ØµØµ ÙˆØ§Ù„Ù…Ø®Ø§Ø²Ù†</li>
                  <li className="flex items-center gap-2 font-bold text-blue-800">âœ“ Ø®Ø§Ø¯Ù… Ù…Ø®ØµØµ Ù„Ù„Ù…Ø§Ø±ÙƒØ© ÙˆØ¯Ø¹Ù… Ù…Ø®ØµØµ</li>
                </ul>
              </div>
              <button onClick={() => openAuth("register")} className="mt-8 w-full bg-slate-100 text-slate-700 font-bold p-3 rounded-xl hover:bg-slate-200 transition-colors">Ø§Ù„Ø¨Ø¯Ø¡ Ù…Ø¬Ø§Ù†Ø§Ù‹</button>
            </article>
          </div>
        </div>
      </section>

      {/* FAQ / Transparency Section */}
      <section className="bg-white py-16 px-6 border-t border-slate-100">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <h3 className="text-2xl font-black text-blue-deep">Ø£Ø³Ø¦Ù„Ø© Ø´Ø§Ø¦Ø¹Ø© ÙˆØ´ÙØ§ÙÙŠØ© ØªØ§Ù…Ø© âš–ï¸</h3>
            <p className="text-slate-500 text-sm">ÙƒÙ„ Ù…Ø§ ØªÙˆØ¯ Ù…Ø¹Ø±ÙØªÙ‡ Ø¹Ù† Ø§Ù„ÙÙˆØªØ±Ø©ØŒ Ø­Ù…Ø§ÙŠØ© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª ÙˆØ§Ù„Ø±Ø¨Ø· Ø§Ù„Ø±Ø³Ù…ÙŠ Ù…Ø¹ Meta.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mt-10">
            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">ÙƒÙŠÙ ÙŠØªÙ… Ø§Ø­ØªØ³Ø§Ø¨ Ø±Ø³ÙˆÙ… Ù…Ø­Ø§Ø¯Ø«Ø§Øª ÙˆØ§ØªØ³Ø§Ø¨ (Meta)ØŸ</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                Ù†Ù‚ÙˆÙ… Ø¨Ø±Ø¨Ø· Ù…ØªØ¬Ø±Ùƒ ÙˆØ­Ø³Ø§Ø¨ WABA Ø¨Ø§Ù„Ù…Ù†ØµØ© Ù…Ø¬Ø§Ù†Ø§Ù‹ ÙˆØ¨Ø¶ØºØ·Ø© Ø²Ø±. Ø±Ø³ÙˆÙ… Ù…Ø­Ø§Ø¯Ø«Ø§Øª ÙˆØ§ØªØ³Ø§Ø¨ (Conversation Fees) ÙŠØªÙ… Ø¯ÙØ¹Ù‡Ø§ ÙˆØ§Ø­ØªØ³Ø§Ø¨Ù‡Ø§ Ù…Ø¨Ø§Ø´Ø±Ø© Ù„Ø­Ø³Ø§Ø¨Ùƒ ÙÙŠ Meta Ø­Ø³Ø¨ Ø³ÙŠØ§Ø³Ø© ÙÙŠØ³Ø¨ÙˆÙƒ Ø§Ù„Ø±Ø³Ù…ÙŠØ©ØŒ Ù…Ù…Ø§ ÙŠØ¶Ù…Ù† Ù„Ùƒ Ø§Ù„Ø´ÙØ§ÙÙŠØ© Ø§Ù„Ù…Ø·Ù„Ù‚Ø© Ø¯ÙˆÙ† Ø£ÙŠ Ø¹Ù…ÙˆÙ„Ø© Ø¥Ø¶Ø§ÙÙŠØ© Ù…Ù† Ù…Ø¬ÙŠØ¨.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">Ù‡Ù„ ÙŠØªÙ… ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø¹Ù†ÙˆØ§Ù† ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ ÙÙŠ Ø³Ù„Ø© ÙˆØ²Ø¯ØŸ</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                Ù†Ø¹Ù…ØŒ Ø¨Ù…Ø¬Ø±Ø¯ Ù‚ÙŠØ§Ù… Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø¨Ù…Ø´Ø§Ø±ÙƒØ© Ù…ÙˆÙ‚Ø¹Ù‡ Ø§Ù„Ø¬ØºØ±Ø§ÙÙŠ (GPS) Ø¨Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ØŒ ÙŠÙ‚ÙˆÙ… Ù…Ø¬ÙŠØ¨ Ø¨ÙƒØªØ§Ø¨Ø© Ø¥Ø­Ø¯Ø§Ø«ÙŠØ§Øª ÙˆÙ…ÙˆÙ‚Ø¹ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ù…Ø¨Ø§Ø´Ø±Ø© Ø¯Ø§Ø®Ù„ ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø´Ø­Ù† Ø§Ù„Ø®Ø§ØµØ© Ø¨Ø§Ù„Ø·Ù„Ø¨ ÙÙŠ Ø³Ù„Ø©/Ø²Ø¯ Ù„ØªØªÙ…ÙƒÙ† Ù…Ù† Ø·Ø¨Ø§Ø¹Ø© Ø§Ù„Ø¨ÙˆÙ„ÙŠØµØ§Øª ÙÙˆØ±Ø§Ù‹ ÙˆØ´Ø­Ù†Ù‡Ø§ Ø¯ÙˆÙ† Ø£ÙŠ Ø¥Ø¯Ø®Ø§Ù„ ÙŠØ¯ÙˆÙŠ.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">Ù…Ø§Ø°Ø§ ÙŠØ­Ø¯Ø« Ø¹Ù†Ø¯Ù…Ø§ ÙŠÙƒØªØ¨ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø±Ø¯Ø§Ù‹ Ù…Ø¹Ù‚Ø¯Ø§Ù‹ Ù„Ù„Ø¨ÙˆØªØŸ</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                ÙŠØ­ØªÙˆÙŠ Ù…Ø¬ÙŠØ¨ Ø¹Ù„Ù‰ Ù†Ø¸Ø§Ù… ØªØ­ÙˆÙŠÙ„ Ø¨Ø´Ø±ÙŠ Ø°ÙƒÙŠ (Agent Handover)Ø› ÙÙŠ Ø­Ø§Ù„ Ø·Ø±Ø­ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ø³Ø¤Ø§Ù„Ø§Ù‹ Ø®Ø§Ø±Ø¬ Ù†Ø·Ø§Ù‚ Ø§Ù„ØªØ£ÙƒÙŠØ¯ Ø£Ùˆ Ø·Ù„Ø¨ ØªØ¹Ø¯ÙŠÙ„Ø§Ù‹ØŒ ÙŠØªÙˆÙ‚Ù Ø§Ù„Ø¨ÙˆØª ÙÙˆØ±Ø§Ù‹ ÙˆÙŠØ­ÙŠÙ„ Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø© Ù„ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„ÙˆØ§Ø±Ø¯ Ø§Ù„Ù…Ø´ØªØ±Ùƒ Ù„ÙŠØªØ¯Ø®Ù„ ÙØ±ÙŠÙ‚ Ø§Ù„Ø¯Ø¹Ù… Ø§Ù„Ø®Ø§Øµ Ø¨Ùƒ ÙŠØ¯ÙˆÙŠØ§Ù‹.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">Ù‡Ù„ Ù…ÙŠØ²Ø© Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù…ÙˆÙ‚Ø¹ GPS Ù…ØªÙˆÙØ±Ø© ÙÙŠ Ø§Ù„Ø¨Ø§Ù‚Ø© Ø§Ù„Ù…Ø¨ØªØ¯Ø¦Ø©ØŸ</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                Ù†Ø¹Ù…! Ù‚Ù…Ù†Ø§ Ø¨Ù†Ù‚Ù„ Ù…ÙŠØ²Ø© Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù€ GPS Ù„Ù„Ø¨Ø§Ù‚Ø© Ø§Ù„Ù…Ø¨ØªØ¯Ø¦Ø© (Starter) Ø¨Ø­Ø¯ Ø£Ù‚ØµÙ‰ 300 Ø·Ù„Ø¨ Ø´Ù‡Ø±ÙŠØ§Ù‹ Ù„ØªØªÙ…ÙƒÙ† Ù…Ù† Ø§Ø®ØªØ¨Ø§Ø± Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„ÙØ¹Ù„ÙŠØ© Ù„Ù„Ù…Ù†ØµØ© ÙˆØªÙ‚Ù„ÙŠÙ„ Ø§Ù„Ù…Ø±ØªØ¬Ø¹Ø§Øª Ù‚Ø¨Ù„ Ø§Ù„Ø­Ø§Ø¬Ø© Ù„ØªØ±Ù‚ÙŠØ© Ø¨Ø§Ù‚ØªÙƒ.
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-bold text-blue-deep text-base">Ù‡Ù„ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…ÙˆÙ‚Ø¹ Ø¢Ù…Ù†Ø© ÙˆÙ…ØªÙˆØ§ÙÙ‚Ø© Ù…Ø¹ Ø§Ù„Ø®ØµÙˆØµÙŠØ©ØŸ</h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                ÙŠØ´Ø§Ø±Ùƒ Ø§Ù„Ø¹Ù…ÙŠÙ„ Ù…ÙˆÙ‚Ø¹Ù‡ Ø¨Ù…ÙˆØ§ÙÙ‚ØªÙ‡ Ø§Ù„ÙˆØ§Ø¶Ø­Ø© ÙÙ‚Ø·. Ù†Ø³ØªØ®Ø¯Ù… Ø£Ù‚Ù„ Ù‚Ø¯Ø± Ù„Ø§Ø²Ù… Ù…Ù† Ø§Ù„Ø¨ÙŠØ§Ù†Ø§ØªØŒ ÙˆÙ†Ø­Ù…ÙŠÙ‡Ø§ Ø£Ø«Ù†Ø§Ø¡ Ø§Ù„Ù†Ù‚Ù„ ÙˆØ§Ù„ØªØ®Ø²ÙŠÙ†ØŒ Ù…Ø¹ Ø¥Ù…ÙƒØ§Ù†ÙŠØ© Ø·Ù„Ø¨ Ø§Ù„ØªØµØ¯ÙŠØ± Ø£Ùˆ Ø§Ù„Ø­Ø°Ù Ù…Ù† Ù„ÙˆØ­Ø© Ø§Ù„Ø®ØµÙˆØµÙŠØ©. ÙŠØ¸Ù„ Ø§Ù„ØªØ§Ø¬Ø± Ù…Ø³Ø¤ÙˆÙ„Ø§Ù‹ Ø¹Ù† Ø¥Ø´Ø¹Ø§Ø± Ø¹Ù…Ù„Ø§Ø¦Ù‡ ÙˆØ§Ù„Ø§Ù„ØªØ²Ø§Ù… Ø¨Ù…ØªØ·Ù„Ø¨Ø§Øª PDPL Ø§Ù„Ù…Ø­Ù„ÙŠØ©.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Integration showcase */}
      <section className="py-20 px-6 bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto text-center space-y-8">
          <h3 className="text-lg font-bold text-slate-400 uppercase tracking-widest">Ø±Ø¨Ø· ÙˆØªÙƒØ§Ù…Ù„ Ø±Ø³Ù…ÙŠ Ø³Ø±ÙŠØ¹</h3>
          <div className="flex flex-wrap justify-center gap-8 items-center opacity-75">
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Ø³Ù„Ø© Salla</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Ø²Ø¯ Zid</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Shopify</span>
            <span className="text-2xl font-black text-slate-400 border border-slate-200 rounded-xl px-5 py-2 hover:opacity-100 transition-opacity">Custom API</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 text-center text-slate-400 text-xs border-t border-slate-100 bg-slate-50">
        <p>Â© 2026 Ù…Ø¬ÙŠØ¨ (Mujeeb). Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø­Ù‚ÙˆÙ‚ Ù…Ø­ÙÙˆØ¸Ø© Ù„Ø´Ø±ÙƒØ§Ø¡ Ø§Ù„Ù‡ÙˆÙŠØ©.</p>
        <div className="mt-2 flex justify-center gap-4">
          <a href="/privacy.html" className="hover:underline">Ø³ÙŠØ§Ø³Ø© Ø§Ù„Ø®ØµÙˆØµÙŠØ©</a>
          <a href="/terms.html" className="hover:underline">Ø´Ø±ÙˆØ· Ø§Ù„Ø®Ø¯Ù…Ø©</a>
        </div>
        <p className="mt-2">Mujeeb is operated by <strong className="text-slate-600">AYOUB FADIL</strong> Â· <a href="mailto:support@usemujeeb.com" className="text-slate-600 hover:underline">support@usemujeeb.com</a></p>
        <div className="mt-4 flex justify-center gap-4 flex-wrap">
          <a href="/data-deletion.html" className="hover:underline">Delete my data</a>
          <a href="https://x.com/DigiClub09" target="_blank" rel="noreferrer" aria-label="Mujeeb on X" className="font-bold text-slate-600 hover:text-black">ð• X</a>
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
              <p className="inline-block px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold w-fit mb-3">Ø­Ø³Ø§Ø¨Ø§Øª Ø§Ù„Ù…Ø¤Ø³Ø³ÙŠÙ† Ø§Ù„ØªØ¬Ø±ÙŠØ¨ÙŠØ©</p>
              <h3 className="text-2xl font-black mt-2 text-ink">{mode === "login" ? "Ù…Ø±Ø­Ø¨Ø§Ù‹ Ø¨Ø¹ÙˆØ¯ØªÙƒ" : "Ø§Ø¨Ø¯Ø£ ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨Ø§ØªÙƒ Ù…Ø¬Ø§Ù†Ø§Ù‹"}</h3>
              <p className="text-slate-500 text-sm mt-1">Ø§Ù†Ø¶Ù… Ù„ØµÙÙˆØ© ØªØ¬Ø§Ø± Ø§Ù„Ø®Ù„ÙŠØ¬ ÙˆØªØ®Ù„Øµ Ù…Ù† Ø®Ø³Ø§Ø¦Ø± Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù… Ù†Ù‡Ø§Ø¦ÙŠØ§Ù‹.</p>

              <div className="grid gap-3 mt-7">
                {mode === "register" && (
                  <>
                    <input name="full_name" required placeholder="Ø§Ù„Ø§Ø³Ù… Ø§Ù„ÙƒØ§Ù…Ù„" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <input name="phone" required placeholder="+9665xxxxxxxx" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <input name="store_name" required placeholder="Ø§Ø³Ù… Ø§Ù„Ù…ØªØ¬Ø±" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                    <div className="grid grid-cols-2 gap-3">
                      <select name="platform" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky">
                        <option value="salla">Ø³Ù„Ø©</option>
                        <option value="zid">Ø²Ø¯</option>
                        <option value="shopify">Shopify</option>
                        <option value="custom">Ù…ØªØ¬Ø± Ù…Ø®ØµØµ</option>
                      </select>
                      <select name="country_code" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky">
                        <option value="SA">Ø§Ù„Ø³Ø¹ÙˆØ¯ÙŠØ©</option>
                        <option value="AE">Ø§Ù„Ø¥Ù…Ø§Ø±Ø§Øª</option>
                        <option value="KW">Ø§Ù„ÙƒÙˆÙŠØª</option>
                        <option value="QA">Ù‚Ø·Ø±</option>
                        <option value="BH">Ø§Ù„Ø¨Ø­Ø±ÙŠÙ†</option>
                        <option value="OM">Ø¹ÙÙ…Ø§Ù†</option>
                      </select>
                    </div>
                  </>
                )}
                <input name="email" type="email" required placeholder="Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ Ù„Ù„Ø¹Ù…Ù„" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                <input name="password" type="password" minLength={10} required placeholder="ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±" dir="ltr" className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky" />
                
                {error && <p className="text-rose-600 text-sm font-bold bg-rose-50 p-2 rounded">{error}</p>}
                
                <button className="rounded-xl btn-gold font-black p-4 mt-2 text-lg shadow-xl hover:shadow-2xl">
                  {mode === "login" ? "Ø¯Ø®ÙˆÙ„ Ø¢Ù…Ù† Ù„Ù„ÙˆØ­Ø© Â· 180IQ" : "Ø£ÙƒÙ‘Ø¯ Ù…ÙƒØ§Ù†ÙŠ ÙƒØ¹Ø¶Ùˆ Ù…Ø¤Ø³Ø³"}
                </button>
              </div>

              <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="mt-5 text-sm text-sky font-bold hover:underline">
                {mode === "login" ? "Ù…ØªØ¬Ø± Ø¬Ø¯ÙŠØ¯ØŸ Ø£Ù†Ø´Ø¦ Ø­Ø³Ø§Ø¨Ùƒ Ù„Ø¨Ø¯Ø¡ Ø§Ù„ØªØ¬Ø±Ø¨Ø©" : "Ù„Ø¯ÙŠÙƒ Ø­Ø³Ø§Ø¨ Ù…Ø¤Ø³Ø³ØŸ Ø³Ø¬Ù‘Ù„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù‡Ù†Ø§"}
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

function DeveloperApi({storeId}:{storeId:string}) {
  const [createdKey,setCreatedKey]=useState(""); const [message,setMessage]=useState("");
  const keys=useQuery({queryKey:["api-keys",storeId],queryFn:async()=> (await api.get("/api/api-keys",{params:{store_id:storeId}})).data});
  const generate=async()=>{const r=await api.post("/api/api-keys",{store_id:storeId,name:"Pilot integration"});setCreatedKey(r.data.api_key);setMessage("Ø§Ù†Ø³Ø® Ø§Ù„Ù…ÙØªØ§Ø­ Ø§Ù„Ø¢Ù†. Ù„Ù† Ù†Ø¹Ø±Ø¶Ù‡ ÙƒØ§Ù…Ù„Ø§Ù‹ Ù…Ø±Ø© Ø£Ø®Ø±Ù‰.");keys.refetch();};
  const snippet=`curl -X POST https://api.usemujeeb.com/api/orders/custom \\\n+  -H "Content-Type: application/json" \\\n+  -H "X-Mujeeb-API-Key: YOUR_KEY" \\\n+  -d '{"order_id":"1001","customer_name":"Customer","customer_phone":"+966501234567","amount":250,"currency":"SAR","payment_method":"COD","items":[]}'`;
  return <section className="mt-8 max-w-4xl"><div className="flex items-center gap-3"><Code2 className="text-sky"/><div><h2 className="text-xl font-black">ØªÙƒØ§Ù…Ù„ API Ù„Ù„Ù…ØªØ§Ø¬Ø±</h2><p className="text-sm text-slate-500">ShopifyØŒ WooCommerceØŒ Laravel ÙˆØ£ÙŠ Ù…ØªØ¬Ø± Ù…Ø®ØµØµ.</p></div></div>
    <div className="grid lg:grid-cols-2 gap-5 mt-5"><article className="glass rounded-2xl p-6"><h3 className="font-black">Ù…ÙØªØ§Ø­ Ø§Ù„Ù…ØªØ¬Ø±</h3><p className="text-sm text-slate-500 mt-2">ÙŠÙØ­ÙØ¸ Ø§Ù„Ù…ÙØªØ§Ø­ Ù…Ø´ÙØ±Ø§Ù‹ ÙƒØ¨ØµÙ…Ø©ØŒ ÙˆÙŠÙ…ÙƒÙ† Ø¥Ù„ØºØ§Ø¤Ù‡ in any time.</p>{createdKey?<><div dir="ltr" className="mt-4 break-all rounded-xl bg-slate-950 p-4 text-xs text-emerald-300">{createdKey}</div><button onClick={()=>navigator.clipboard.writeText(createdKey)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> Ù†Ø³Ø® Ø§Ù„Ù…ÙØªØ§Ø­</button></>:<button onClick={generate} className="mt-5 rounded-xl bg-ink text-white px-5 py-3 font-bold">Ø¥Ù†Ø´Ø§Ø¡ Ù…ÙØªØ§Ø­ API</button>}{message&&<p className="mt-3 text-xs text-amber-700">{message}</p>}<p className="mt-5 text-xs text-slate-500">Ø§Ù„Ù…ÙØ§ØªÙŠØ­ Ø§Ù„Ù†Ø´Ø·Ø©: {keys.data?.length||0}</p></article>
    <article className="glass rounded-2xl p-6"><h3 className="font-black">Ø£Ø±Ø³Ù„ Ø£ÙˆÙ„ Ø·Ù„Ø¨</h3><pre dir="ltr" className="mt-4 overflow-auto rounded-xl bg-slate-950 p-4 text-[11px] leading-5 text-slate-200">{snippet}</pre><button onClick={()=>navigator.clipboard.writeText(snippet)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> Ù†Ø³Ø® Ø§Ù„Ù…Ø«Ø§Ù„</button></article></div></section>;
}

function Billing({storeId}:{storeId:string}) {
  const [checkingOut,setCheckingOut]=useState("");
  const [message,setMessage]=useState("");
  const plans=[
    {id:"starter",name:"Starter",price:"299",orders:"Ø­ØªÙ‰ 300 Ø·Ù„Ø¨ Ø´Ù‡Ø±ÙŠØ§Ù‹",detail:"Ù„Ù…ØªØ¬Ø± ÙˆØ§Ø­Ø¯ ÙˆÙØ±ÙŠÙ‚ ØµØºÙŠØ±"},
    {id:"growth",name:"Growth",price:"599",orders:"Ø­ØªÙ‰ 5,000 Ø·Ù„Ø¨ Ø´Ù‡Ø±ÙŠØ§Ù‹",detail:"ØªØ­Ù„ÙŠÙ„ Ø£Ø¹Ù…Ù‚ ÙˆØ¯Ø¹Ù… Ø¨Ø£ÙˆÙ„ÙˆÙŠØ©",featured:true},
    {id:"scale",name:"Scale",price:"1,199",orders:"Ø­Ø¬Ù… Ù…Ø±ØªÙØ¹ ÙˆÙÙ‚ Ø§Ù„Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ø¹Ø§Ø¯Ù„",detail:"Ù„Ù„Ø¹Ù„Ø§Ù…Ø§Øª Ù…ØªØ¹Ø¯Ø¯Ø© Ø§Ù„Ù…ØªØ§Ø¬Ø±"},
  ];
  const checkout=async(plan:string)=>{
    setCheckingOut(plan); setMessage("");
    try { const r=await api.post("/api/payments/checkout",{store_id:storeId,plan}); location.href=r.data.url; }
    catch(err:any){ setMessage(err.response?.status===503?"Ø§Ù„Ø¯ÙØ¹ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ Ù„Ù‡Ø°Ù‡ Ø§Ù„Ø®Ø·Ø© Ù‚ÙŠØ¯ Ø§Ù„ØªÙØ¹ÙŠÙ„. ØªÙˆØ§ØµÙ„ Ù…Ø¹Ù†Ø§ Ù„ØªØ«Ø¨ÙŠØª Ø¹Ø±Ø¶ Ø§Ù„Ù…Ø¤Ø³Ø³ÙŠÙ†.":"ØªØ¹Ø°Ø± ÙØªØ­ ØµÙØ­Ø© Ø§Ù„Ø¯ÙØ¹ Ø§Ù„Ø¢Ù…Ù†Ø©. Ø­Ø§ÙˆÙ„ Ù…Ø±Ø© Ø£Ø®Ø±Ù‰."); setCheckingOut(""); }
  };
  return <section className="mt-8 max-w-5xl"><p className="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-bold w-fit mb-3">Ù†Ù…ÙˆØ°Ø¬ Ø£Ø¹Ù…Ø§Ù„ ÙŠØ¶Ù…Ù† Ø±Ø¨Ø­Ùƒ</p><h2 className="text-3xl font-black mt-2 text-ink">Ø§Ø³ØªØ«Ù…Ø± Ø¬Ø²Ø¡Ø§Ù‹ ØµØºÙŠØ±Ø§Ù‹ Ù…Ù…Ø§ Ù†ÙˆÙØ±Ù‡ Ù„Ùƒ</h2><p className="text-slate-500 mt-3 text-lg">Ø¨Ø¯ÙˆÙ† Ø¹Ù…ÙˆÙ„Ø§Øª Ø¥Ø¶Ø§ÙÙŠØ© Ø¹Ù„Ù‰ Ø§Ù„Ø±Ø³Ø§Ø¦Ù„ Ù„Ù„Ø­ÙØ§Ø¸ Ø¹Ù„Ù‰ Ù‡Ø§Ù…Ø´ Ø±Ø¨Ø­Ùƒ Ø¹Ø§Ù„ÙŠØ§Ù‹. Ø§Ø¯ÙØ¹ Ø¨Ø¹Ø¯ ØªØ­Ù‚Ù‚ Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„ÙØ¹Ù„ÙŠØ© Ù…Ù† Ø§Ù„Ù†Ø¸Ø§Ù….</p><div className="grid md:grid-cols-3 gap-5 mt-8">{plans.map(plan=><article key={plan.id} className={`glass rounded-2xl p-8 relative flex flex-col ${plan.featured?"border-2 border-mint shadow-2xl shadow-mint/10":""}`}>{plan.featured&&<span className="absolute -top-3 right-8 rounded-full bg-mint px-4 py-1.5 text-xs font-bold text-white shadow-lg">ðŸš€ Ù…Ù‚ØªØ±Ø­ Ù„Ù„Ù†Ù…Ùˆ (180IQ)</span>}<p className="font-black text-2xl text-blue-deep">{plan.name}</p><p className="mt-5 text-4xl font-black text-sky">{plan.price} <span className="text-sm font-medium text-slate-400">Ø±ÙŠØ§Ù„/Ø´Ù‡Ø±</span></p><p className="mt-5 font-bold p-3 bg-sky-50 rounded-xl text-blue-deep text-center">{plan.orders}</p><p className="mt-4 min-h-16 text-sm text-slate-500 leading-relaxed font-medium">{plan.detail}</p><button onClick={()=>checkout(plan.id)} disabled={!!checkingOut} className={`mt-auto w-full rounded-xl p-4 font-bold text-lg transition-transform ${plan.featured?"btn-gold":"bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>{checkingOut===plan.id?"Ø¬Ø§Ø±Ù Ø§Ù„ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ø¢Ù…Ù†...":`Ø§Ø®ØªÙŠØ§Ø± Ø¨Ø§Ù‚Ø© ${plan.name}`}</button></article>)}</div>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800 border border-amber-200">{message}</p>}<p className="mt-6 text-xs text-slate-400 text-center uppercase tracking-wider">Ù†Ø¸Ø§Ù… ÙÙˆØ§ØªÙŠØ± Ø¢Ù…Ù† Ù…Ø¯Ø¹ÙˆÙ… Ø¨Ù€ Stripe | Ø¥Ù„ØºØ§Ø¡ Ù…ØªÙ‰ Ø´Ø¦Øª</p></section>;
}

function Integrations({storeId, onConnectedChange}:{storeId:string, onConnectedChange:()=>void}) {
  const [shop,setShop]=useState(""); const [message,setMessage]=useState("");
  const [sheetUrl,setSheetUrl]=useState("");
  const [waInstance,setWaInstance]=useState(""); const [waToken,setWaToken]=useState(""); const [waQr,setWaQr]=useState("");

  const status=useQuery({queryKey:["integration-status",storeId],queryFn:async()=> (await api.get("/api/integrations/status",{params:{store_id:storeId}})).data});
  const waStatus=useQuery({queryKey:["waapi-status",storeId],queryFn:async()=> (await api.get("/api/waapi/status",{params:{store_id:storeId}})).data});
  
  const connect=async(provider:"salla"|"zid")=>{setMessage("");try{const r=await api.post(`/api/integrations/${provider}/start`,{store_id:storeId});location.href=r.data.url;}catch(err:any){setMessage(err.response?.data?.detail||"ØªØ¹Ø°Ø± Ø¨Ø¯Ø¡ Ø§Ù„Ø±Ø¨Ø·");}};
  const connectShopify=async()=>{setMessage("");try{const r=await api.post("/api/integrations/shopify/start",{store_id:storeId,shop});location.href=r.data.url;}catch(err:any){setMessage(err.response?.data?.detail||"ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ø³Ù… Ù…ØªØ¬Ø± Shopify");}};
  const provisionWaapi=async()=>{setMessage("");try{const r=await api.post("/api/waapi/provision",{store_id:storeId});setWaInstance(r.data.instance_id||"");setWaQr(r.data.qr||"");setMessage("تم إنشاء قناة WhatsApp. امسح رمز QR من هاتفك لإكمال الربط.");waStatus.refetch();}catch(err:any){setMessage(err.response?.data?.detail||"تعذر إنشاء قناة WhatsApp");}};
  const connectWhatsApp=async()=>{setMessage("");try{const signup=await launchEmbeddedSignup();await api.post("/api/whatsapp/embedded-signup",{store_id:storeId,...signup});setMessage("ØªÙ… Ø±Ø¨Ø· Ø±Ù‚Ù… ÙˆØ§ØªØ³Ø§Ø¨ ÙˆØ§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù…Ù„ÙƒÙŠØªÙ‡.");status.refetch();onConnectedChange();}catch(err:any){setMessage(err.response?.data?.detail||err.message||"ØªØ¹Ø°Ø± Ø±Ø¨Ø· ÙˆØ§ØªØ³Ø§Ø¨");}};
  
  const connectGoogleSheets=async()=>{
    setMessage("");
    if(!sheetUrl.startsWith("http")){
      setMessage("ÙŠØ±Ø¬Ù‰ Ø¥Ø¯Ø®Ø§Ù„ Ø±Ø§Ø¨Ø· Google Webhook ØµØ­ÙŠØ­.");
      return;
    }
    try{
      await api.post("/api/integrations/google-sheets/connect", {store_id:storeId, url:sheetUrl});
      setMessage("ØªÙ… Ø±Ø¨Ø· Google Sheet Ø¨Ù†Ø¬Ø§Ø­! Ø³ÙŠØªÙ… Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø·Ù„Ø¨ÙŠØ§Øª ÙÙˆØ±Ø§Ù‹.");
      setSheetUrl("");
      status.refetch();
      onConnectedChange();
    }catch(err:any){
      setMessage(err.response?.data?.detail||"ØªØ¹Ø°Ø± Ø±Ø¨Ø· Google Sheet");
    }
  };

  const disconnectGoogleSheets=async()=>{
    setMessage("");
    try{
      await api.post("/api/integrations/google-sheets/disconnect", {store_id:storeId});
      setMessage("ØªÙ… ÙØµÙ„ Google Sheet.");
      status.refetch();
      onConnectedChange();
    }catch(err:any){
      setMessage("ØªØ¹Ø°Ø± Ø¥ÙŠÙ‚Ø§Ù Ø§Ù„Ø±Ø¨Ø·");
    }
  };

  const entry=(provider:string)=>status.data?.[provider]||{configured:false,connected:false};

  return <section className="mt-8"><h2 className="text-xl font-black">Ø±Ø¨Ø· Ø¨ÙˆØ§Ø¨Ø§Øª Ø§Ù„Ù…Ø¨ÙŠØ¹Ø§Øª ÙˆØ§Ù„Ø¹Ù…Ù„ÙŠØ§Øª</h2><p className="text-slate-500 mt-1">ØªÙƒØ§Ù…Ù„ Ù…Ø¨Ø§Ø´Ø± Ù…Ø¹ Ø§Ù„Ù…ØªØ§Ø¬Ø±ØŒ ÙˆÙ‚Ù†ÙˆØ§Øª Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ ÙˆØ¬Ø¯Ø§ÙˆÙ„ Ø¬ÙˆØ¬Ù„ Ù„ØªÙ†Ø¸ÙŠÙ… Ø¯ÙˆØ±Ø© Ø§Ù„Ø¹Ù…Ù„ Ø¨Ø§Ù„ÙƒØ§Ù…Ù„.</p>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800 border border-amber-200">{message}</p>}<div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5 mt-5">
    {[{id:"salla",name:"Ø³Ù„Ø©",desc:"Ù…Ø²Ø§Ù…Ù†Ø© ØªÙ„Ù‚Ø§Ø¦ÙŠØ© Ù„Ù„Ø·Ù„Ø¨ÙŠØ§Øª ÙˆØ§Ù„Ø¹Ù…Ù„Ø§Ø¡"},{id:"zid",name:"Ø²Ø¯",desc:"Ø³Ø­Ø¨ Ø§Ù„Ø·Ù„Ø¨ÙŠØ§Øª ÙˆØªØ£ÙƒÙŠØ¯ Ø­Ø§Ù„ØªÙ‡Ø§"}].map(item=>{const state=entry(item.id);return <article className="glass rounded-2xl p-6" key={item.id}><Link2 className="text-mint"/><h3 className="font-black text-lg mt-5">{item.name}</h3><p className="text-sm text-slate-500 mt-2 min-h-10">{item.desc}</p><button disabled={!state.configured||state.connected} onClick={()=>connect(item.id as "salla"|"zid")} className="mt-5 w-full rounded-xl border border-sky text-sky p-2 font-bold disabled:border-slate-200 disabled:text-slate-400">{state.connected?"Ù…ØªØµÙ„":state.configured?"Ø±Ø¨Ø· Ø¢Ù…Ù†":"Ù‚ÙŠØ¯ Ø¥Ø¹Ø¯Ø§Ø¯ Ø§Ù„Ø´Ø±ÙŠÙƒ"}</button></article>})}
    <article className="glass rounded-2xl p-6"><Link2 className="text-mint"/><h3 className="font-black text-lg mt-5">Shopify</h3><p className="text-sm text-slate-500 mt-2">Ø£Ø¯Ø®Ù„ Ø§Ø³Ù… Ø§Ù„Ù…ØªØ¬Ø± ÙÙ‚Ø·.</p><input value={shop} onChange={e=>setShop(e.target.value)} dir="ltr" placeholder="store.myshopify.com" className="mt-3 w-full rounded-xl border border-slate-200 p-2 text-sm"/><button disabled={!entry("shopify").configured||entry("shopify").connected||!shop} onClick={connectShopify} className="mt-3 w-full rounded-xl border border-sky text-sky p-2 font-bold disabled:border-slate-200 disabled:text-slate-400">{entry("shopify").connected?"Ù…ØªØµÙ„":entry("shopify").configured?"Ø±Ø¨Ø· Ø¢Ù…Ù†":"Ù‚ÙŠØ¯ Ø¥Ø¹Ø¯Ø§Ø¯ Ø§Ù„Ø´Ø±ÙŠÙƒ"}</button></article>
    
    <article className="glass rounded-2xl p-6 border border-emerald-200 bg-emerald-50/30"><MessageCircle className="text-emerald-600"/><h3 className="font-black text-lg mt-5">WhatsApp عبر Mujeeb</h3><p className="text-sm text-slate-600 mt-2">Mujeeb ينشئ القناة تلقائياً. لا يحتاج التاجر إلى إنشاء حساب WaAPI أو نسخ أي ID أو token.</p>{waQr?<div className="mt-4 space-y-3"><img src={waQr} alt="WhatsApp QR" className="mx-auto w-48 h-48 rounded-xl bg-white p-2"/><p className="text-xs text-center font-bold">افتح واتساب ← الأجهزة المرتبطة ← ربط جهاز، ثم امسح الرمز</p></div>:<button onClick={provisionWaapi} className="mt-5 w-full rounded-xl bg-emerald-600 text-white p-2 font-bold">إنشاء قناة ومسح QR</button>}</article>
    <DevWhatsAppSimulator storeId={storeId}/>
    <article className="glass rounded-2xl p-6 border border-amber-200"><MessageCircle className="text-amber-600"/><h3 className="font-black text-lg mt-5">WAAPI (pilote externe)</h3><p className="text-sm text-slate-500 mt-2">Instance WAAPI isolÃ©e par boutique. Le token est chiffrÃ© cÃ´tÃ© serveur.</p>{waStatus.data?.connected?<div className="mt-4 rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm font-bold text-emerald-800">Instance {waStatus.data.instance_id} Â· connectÃ©e âœ“</div>:<div className="mt-3 space-y-2"><input value={waInstance} onChange={e=>setWaInstance(e.target.value.replace(/\D/g,""))} dir="ltr" placeholder="ID instance WaAPI (numeric)" inputMode="numeric" className="w-full rounded-xl border border-slate-200 p-2 text-sm"/><input value={waToken} onChange={e=>setWaToken(e.target.value)} dir="ltr" type="password" placeholder="WAAPI API token" className="w-full rounded-xl border border-slate-200 p-2 text-sm"/><button disabled={!/^\d+$/.test(waInstance)||!waToken} className="w-full rounded-xl bg-amber-600 text-white p-2 font-bold disabled:opacity-50" onClick={async()=>{try{await api.post("/api/waapi/connect",{store_id:storeId,instance_id:waInstance,api_token:waToken});setWaToken("");setMessage("WAAPI connectÃ©.");waStatus.refetch();}catch(err:any){setMessage(err.response?.data?.detail||"Impossible de vÃ©rifier WAAPI");}}}>VÃ©rifier et connecter WAAPI</button></div>}</article>
    {/* WhatsApp WABA Embedding Card */}
    <article className="glass rounded-2xl p-6"><MessageCircle className="text-mint"/><h3 className="font-black text-lg mt-5">WhatsApp Business (WABA)</h3><p className="text-sm text-slate-500 mt-2 min-h-10">Ø±Ø¨Ø· Ø±Ù‚Ù… Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨ Ø§Ù„Ø®Ø§Øµ Ø¨Ù…ØªØ¬Ø±Ùƒ Ø¨Ø¶ØºØ·Ø© ÙˆØ§Ø­Ø¯Ø© Ø¹Ø¨Ø± Meta Embedded Signup.</p><button disabled={!entry("whatsapp").enabled} onClick={connectWhatsApp} className={`mt-5 w-full rounded-xl p-2 font-bold border transition-colors ${entry("whatsapp").connected?"bg-emerald-50 border-emerald-500 text-emerald-800":"border-sky text-sky hover:bg-sky-50"}`}>{entry("whatsapp").connected?"Ù…ØªØµÙ„ Ø¨Ù†Ø¬Ø§Ø­ âœ“":"Ø±Ø¨Ø· Ø§Ù„Ø­Ø³Ø§Ø¨ Ø¨Ø¶ØºØ·Ø© ÙˆØ§Ø­Ø¯Ø©"}</button></article>

    {/* Google Sheets Sync Card */}
    <article className="glass rounded-2xl p-6"><FileText className="text-mint"/><h3 className="font-black text-lg mt-5">Google Sheets Sync</h3><p className="text-sm text-slate-500 mt-2">Ù…Ø²Ø§Ù…Ù†Ø© ØªÙ„Ù‚Ø§Ø¦ÙŠØ© Ù„Ù„Ù…Ø¨ÙŠØ¹Ø§Øª ÙˆØªØ­Ø¯ÙŠØ«Ø§Øª Ø§Ù„Ø´Ø­Ù† Ù…Ø¨Ø§Ø´Ø±Ø© ÙÙŠ Ø¬Ø¯ÙˆÙ„Ùƒ Ø§Ù„Ø®Ø§Øµ.</p>
      {entry("google_sheets").connected ? (
        <div className="mt-4 space-y-3">
          <div className="bg-emerald-50 border border-emerald-250 p-2 rounded-xl text-xs text-emerald-800 font-bold text-center">Ù…ØªØµÙ„ Ø¨Ù†Ø´Ø§Ø· ÙˆÙ…Ø²Ø§Ù…Ù† âœ“</div>
          <button onClick={disconnectGoogleSheets} className="w-full rounded-xl border border-rose-300 text-rose-600 p-2 text-xs font-bold hover:bg-rose-50">Ø¥ÙŠÙ‚Ø§Ù Ø§Ù„Ù…Ø²Ø§Ù…Ù†Ø©</button>
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          <input value={sheetUrl} onChange={e=>setSheetUrl(e.target.value)} dir="ltr" placeholder="Ø±Ø§Ø¨Ø· Google Webhook URL" className="w-full rounded-xl border border-slate-200 p-2 text-xs"/>
          <button onClick={connectGoogleSheets} className="w-full rounded-xl border border-sky text-sky p-2 text-xs font-bold hover:bg-sky-50">Ø±Ø¨Ø· ÙˆØªÙØ¹ÙŠÙ„ Ø§Ù„Ù…Ø²Ø§Ù…Ù†Ø©</button>
        </div>
      )}
    </article>
  </div></section>;
}

function DevWhatsAppSimulator({storeId}:{storeId:string}) {
  const [session,setSession]=useState<any>(null);
  const [message,setMessage]=useState("");
  const start=async()=>{try{setMessage("");setSession((await api.post("/api/dev/whatsapp/session",{store_id:storeId})).data);}catch(err:any){setMessage(err.response?.data?.detail||"ØªØ¹Ø°Ø± Ø¨Ø¯Ø¡ Ø§Ù„Ù…Ø­Ø§ÙƒÙŠ");}};
  const emit=async(event:string,payload:Record<string,unknown>={})=>{if(!session)return;setSession((await api.post(`/api/dev/whatsapp/session/${session.id}/event`,{event,payload})).data);};
  return <article className="glass rounded-2xl p-6 border border-amber-200 bg-amber-50/40"><MessageCircle className="text-amber-600"/><h3 className="font-black text-lg mt-5">Pilote WhatsApp local</h3><p className="text-sm text-slate-600 mt-2">Simule le QR et le parcours Mujeeb sans connecter de compte WhatsApp rÃ©el.</p>{!session?<button onClick={start} className="mt-5 w-full rounded-xl bg-amber-600 text-white p-2 font-bold">DÃ©marrer le pilote</button>:<div className="mt-4 space-y-3"><div className="mx-auto grid grid-cols-9 gap-0 w-28 h-28 bg-white p-2 border-4 border-slate-900" aria-label="QR de simulation">{Array.from({length:81},(_,i)=><span key={i} className={(i*17+i*i)%7<3?"bg-slate-900":"bg-white"}/>)}</div><p className="text-[11px] text-center font-mono break-all text-slate-500">{session.qr_payload}</p><div className="grid grid-cols-2 gap-2"><button onClick={()=>emit("qr_scanned")} className="rounded-lg bg-slate-900 text-white p-2 text-xs font-bold">Simuler scan</button><button onClick={()=>emit("order_created",{order_id:"DEV-001"})} className="rounded-lg bg-emerald-600 text-white p-2 text-xs font-bold">Simuler commande</button><button onClick={()=>emit("location_received",{lat:29.3759,lng:47.9774})} className="rounded-lg bg-sky-600 text-white p-2 text-xs font-bold">Simuler GPS</button><button onClick={()=>emit("store_synced",{status:"confirmed"})} className="rounded-lg bg-indigo-600 text-white p-2 text-xs font-bold">Simuler sync</button></div><p className="text-xs font-bold text-amber-800">Statut : {session.status} Â· Ã©vÃ©nements : {session.events.length}</p></div>}{message&&<p className="mt-3 text-xs text-rose-700">{message}</p>}</article>;
}

function Privacy() {
  const [password,setPassword]=useState(""); const [message,setMessage]=useState("");
  const deletion=useQuery({queryKey:["deletion-status"],queryFn:async()=> (await api.get("/api/privacy/deletion-request")).data});
  const download=async()=>{const r=await api.get("/api/privacy/export");const blob=new Blob([JSON.stringify(r.data,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="mujeeb-data-export.json";link.click();URL.revokeObjectURL(url);};
  const schedule=async()=>{setMessage("");try{const r=await api.post("/api/privacy/deletion-request",{password});setMessage(`ØªÙ…Øª Ø¬Ø¯ÙˆÙ„Ø© Ø§Ù„Ø­Ø°Ù ÙÙŠ ${new Date(r.data.scheduled_for).toLocaleDateString("ar-SA")}.`);setPassword("");deletion.refetch();}catch(err:any){setMessage(err.response?.data?.detail||"ØªØ¹Ø°Ø± Ø¬Ø¯ÙˆÙ„Ø© Ø§Ù„Ø­Ø°Ù");}};
  const cancel=async()=>{await api.delete("/api/privacy/deletion-request");setMessage("ØªÙ… Ø¥Ù„ØºØ§Ø¡ Ø·Ù„Ø¨ Ø§Ù„Ø­Ø°Ù.");deletion.refetch();};
  return <section className="mt-8 max-w-4xl"><h2 className="text-2xl font-black">Ø¨ÙŠØ§Ù†Ø§ØªÙƒ ØªØ­Øª Ø³ÙŠØ·Ø±ØªÙƒ</h2><p className="text-slate-500 mt-2">Ù†Ø²Ù‘Ù„ Ù†Ø³Ø®Ø© Ù‚Ø§Ø¨Ù„Ø© Ù„Ù„Ù‚Ø±Ø§Ø¡Ø© Ø£Ùˆ Ø§Ø·Ù„Ø¨ Ø­Ø°Ù Ø§Ù„Ø­Ø³Ø§Ø¨ Ø¢Ù„ÙŠØ§Ù‹ Ø¨Ø¹Ø¯ Ù…Ù‡Ù„Ø© Ø£Ù…Ø§Ù† 7 Ø£ÙŠØ§Ù….</p>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">{message}</p>}<div className="grid md:grid-cols-2 gap-5 mt-6"><article className="glass rounded-2xl p-6"><Download className="text-sky"/><h3 className="font-black text-lg mt-4">ØªØµØ¯ÙŠØ± Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª</h3><p className="text-sm text-slate-500 mt-2">Ø§Ù„Ø­Ø³Ø§Ø¨ØŒ Ø§Ù„Ù…ØªØ§Ø¬Ø±ØŒ Ø§Ù„Ø·Ù„Ø¨Ø§Øª ÙˆØ§Ù„Ø¹Ù…Ù„Ø§Ø¡ Ø¯ÙˆÙ† ÙƒÙ„Ù…Ø§Øª Ø§Ù„Ù…Ø±ÙˆØ± Ø£Ùˆ Ù…ÙØ§ØªÙŠØ­ Ø§Ù„ÙˆØµÙˆÙ„.</p><button onClick={download} className="mt-5 rounded-xl bg-ink px-5 py-3 text-white font-bold">ØªÙ†Ø²ÙŠÙ„ JSON</button></article><article className="glass rounded-2xl p-6"><Trash2 className="text-rose-600"/><h3 className="font-black text-lg mt-4">Ø­Ø°Ù Ø§Ù„Ø­Ø³Ø§Ø¨</h3>{deletion.data?.status==="scheduled"?<><p className="text-sm text-slate-500 mt-2">Ø§Ù„Ø­Ø°Ù Ù…Ø¬Ø¯ÙˆÙ„ ÙÙŠ {new Date(deletion.data.scheduled_for).toLocaleDateString("ar-SA")}.</p><button onClick={cancel} className="mt-5 rounded-xl border border-slate-300 px-5 py-3 font-bold">Ø¥Ù„ØºØ§Ø¡ Ø§Ù„Ø·Ù„Ø¨</button></>:<><p className="text-sm text-slate-500 mt-2">Ø£ÙƒØ¯ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±. Ø³ÙŠØ¨Ù‚Ù‰ Ø¨Ø¥Ù…ÙƒØ§Ù†Ùƒ Ø¥Ù„ØºØ§Ø¡ Ø§Ù„Ø·Ù„Ø¨ Ø®Ù„Ø§Ù„ Ø§Ù„Ù…Ù‡Ù„Ø©.</p><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±" className="mt-4 w-full rounded-xl border border-slate-200 p-3"/><button disabled={!password} onClick={schedule} className="mt-3 rounded-xl bg-rose-600 px-5 py-3 text-white font-bold disabled:opacity-50">Ø¬Ø¯ÙˆÙ„Ø© Ø§Ù„Ø­Ø°Ù</button></>}</article></div></section>;
}

function Dashboard({user,onLogout}:{user:User;onLogout:()=>void}) {
  const store=user.stores[0]; const [tab,setTab]=useState("overview");
  const [showUpsell, setShowUpsell] = useState(true);

  // Bot Simulator States
  const [activeSimId, setActiveSimId] = useState<string | null>(null);
  const [simStep, setSimStep] = useState<"ready" | "pending_confirm" | "pending_gps" | "pending_upsell" | "completed">("ready");
  const [simAmount, setSimAmount] = useState(320);

  const summary=useQuery({queryKey:["summary",store.id],queryFn:async()=> (await api.get<any>("/api/orders/summary",{params:{store_id:store.id}})).data});
  const orders=useQuery({queryKey:["orders",store.id],queryFn:async()=> (await api.get<Order[]>("/api/orders",{params:{store_id:store.id}})).data});
  
  const s = summary.data || {
    total:0, confirmed:0, cancelled:0, human_follow_up:0, confirmation_rate:0,
    plan:"free", free_pilot_remaining:50, gps_verified_count: 0,
    upsell_conversion_count: 0, upsell_revenue: 0.0, google_sheets_sync_healthy: false
  };

  const startSimulator = async () => {
    try {
      const r = await api.post("/api/orders/simulate-chatbot");
      setActiveSimId(r.data.order_id);
      setSimStep("pending_confirm");
      setSimAmount(320);
    } catch(err:any) {
      alert("ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªØ£ÙƒØ¯ Ù…Ù† Ø¥Ø¶Ø§ÙØ© Ù…ØªØ¬Ø± Ø£ÙˆÙ„Ø§Ù‹.");
    }
  };

  const handleSimAction = async (action: "confirm" | "share_location" | "accept_upsell" | "reject_upsell") => {
    if (!activeSimId) return;
    try {
      const r = await api.post(`/api/orders/${activeSimId}/chatbot`, {action});
      if (action === "confirm") {
        setSimStep("pending_gps");
      } else if (action === "share_location") {
        setSimStep("pending_upsell");
      } else {
        setSimStep("completed");
        setActiveSimId(null);
        // Refresh summary stats and orders list immediately
        summary.refetch();
        orders.refetch();
      }
      setSimAmount(Number(r.data.amount));
    } catch(err:any) {
      console.error(err);
    }
  };

  const nav=[
    {id:"overview",label:"Ù„ÙˆØ­Ø© Ø§Ù„Ù‚ÙŠØ§Ø¯Ø©",icon:BarChart3},
    {id:"orders",label:"Ø³Ø¬Ù„ Ø§Ù„Ø·Ù„Ø¨Ø§Øª",icon:Boxes},
    {id:"integrations",label:"ØªÙØ¹ÙŠÙ„ Ø§Ù„Ù‚Ù†ÙˆØ§Øª",icon:Link2},
    {id:"developer",label:"API Ø§Ù„Ù…Ø·ÙˆØ±ÙŠÙ†",icon:Code2},
    {id:"billing",label:"Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ ÙˆØ§Ù„ØªØ±Ù‚ÙŠØ©",icon:CreditCard},
    {id:"privacy",label:"Ø§Ù„Ø®ØµÙˆØµÙŠØ© ÙˆØ§Ù„Ø£Ù…Ø§Ù†",icon:ShieldCheck}
  ];

  return <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]" dir="rtl"><aside className="bg-blue-deep text-white p-6 lg:min-h-screen border-l border-blue-900 shadow-[4px_0_24px_rgba(30,58,138,0.2)]"><div className="text-2xl font-black mb-10 flex items-center gap-2"><div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mint to-teal-800 flex items-center justify-center shadow-lg shadow-mint/20 text-xl font-bold">M</div>Ù…ÙØ¬ÙŠØ¨</div><nav className="flex lg:flex-col gap-2 overflow-auto">{nav.map(n=><button key={n.id} onClick={()=>setTab(n.id)} className={`flex items-center gap-3 rounded-xl px-4 py-3.5 whitespace-nowrap transition-colors font-medium ${tab===n.id?"bg-white text-blue-deep shadow-md font-bold":"text-blue-200 hover:bg-white/10 hover:text-white"}`}><n.icon size={20}/>{n.label}</button>)}</nav><button onClick={onLogout} className="mt-12 lg:mt-[40vh] flex items-center gap-3 text-blue-300 hover:text-white transition-colors w-full px-4"><LogOut size={20}/> ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø®Ø±ÙˆØ¬</button></aside>
  <main className="mesh p-5 lg:px-10 lg:py-8"><header className="flex justify-between items-center bg-white/50 backdrop-blur-md p-4 rounded-2xl border border-slate-100 shadow-sm"><div><p className="text-sm font-bold text-sky">{store.name} Â· {store.country_code}</p><h1 className="text-2xl font-black mt-1 text-ink">Ø£Ù‡Ù„Ø§Ù‹ØŒ {user.full_name.split(" ")[0]} ðŸ‘‹</h1></div><div className="flex items-center gap-3"><button onClick={()=>setTab("billing")} className="px-4 py-2 font-bold text-sm bg-blue-deep text-white rounded-xl shadow-md hover:bg-blue-800 transition-colors">ØªØ±Ù‚ÙŠØ© Ø§Ù„Ø­Ø³Ø§Ø¨</button><span className="rounded-xl border border-mint bg-emerald-50 text-emerald-800 px-4 py-2 text-sm font-black shadow-sm">{s.plan==="free"?`Ø§Ù„ØªØ¬Ø±Ø¨Ø© (ØªØ¨Ù‚Ù‰ ${s.free_pilot_remaining??50} Ø·Ù„Ø¨)`:`Ø¨Ø§Ù‚Ø© ${s.plan}`}</span></div></header>
  
  {showUpsell && s.plan==="free" && tab==="overview" && (
    <div className="mt-6 glass rounded-2xl p-6 border-l-4 border-l-gold relative flex flex-col sm:flex-row justify-between items-center shadow-xl shadow-gold/5 bg-gradient-to-r from-amber-50 to-white overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-gold/10 rounded-full blur-3xl"></div>
      <div className="z-10">
        <h3 className="text-lg font-black text-ink flex items-center gap-2"><Sparkles className="text-gold" size={18} /> Ø­Ù…Ø§ÙŠØ© Ø§Ù„ØªÙˆØµÙŠÙ„ (Protect) Ù…Ø¹Ø·Ù„Ø© Ù„Ù„Ù…ØªØ§Ø¬Ø± Ø§Ù„Ù…Ø¬Ø§Ù†ÙŠØ©</h3>
        <p className="text-slate-600 text-sm mt-1">Ù…ÙŠØ²Ø© GPS Ù…Ø´Ù…ÙˆÙ„Ø© ÙÙŠ Starter Ø­ØªÙ‰ 300 Ø·Ù„Ø¨ Ø´Ù‡Ø±ÙŠØ§Ù‹. Ø±Ù‚Ù‘Ù Ø¥Ù„Ù‰ Growth Ø¹Ù†Ø¯ Ø§Ù„Ø­Ø§Ø¬Ø© Ø¥Ù„Ù‰ 5,000 Ø·Ù„Ø¨ØŒ Shared Inbox ÙˆØªØ³Ù„ÙŠÙ… Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø© Ù„ÙØ±ÙŠÙ‚Ùƒ.</p>
      </div>
      <div className="flex gap-3 mt-4 sm:mt-0 z-10 w-full sm:w-auto">
        <button className="text-slate-500 text-sm font-bold px-3 hover:text-ink transition-colors" onClick={() => setShowUpsell(false)}>Ø¥Ø®ÙØ§Ø¡ Ø§Ù„ØªÙ†Ø¨ÙŠÙ‡</button>
        <button onClick={() => setTab("billing")} className="btn-gold whitespace-nowrap text-sm px-6 py-2.5 rounded-xl shadow-lg border-none w-full sm:w-auto">Ø§ÙƒØªØ´Ù Ø¨Ø§Ù‚Ø© Growth</button>
      </div>
    </div>
  )}

  {tab==="overview"&&<>
    {/* Core Stats Overview */}
    <section className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mt-8">
      <Stat title="Ø¥Ø¬Ù…Ø§Ù„ÙŠ Ø§Ù„Ø·Ù„Ø¨Ø§Øª Ø§Ù„Ù…Ø³ØªÙ„Ù…Ø©" value={s.total} detail="Ù‡Ø°Ø§ Ø§Ù„Ø´Ù‡Ø± (ÙˆØ§ØªØ³Ø§Ø¨)" icon={PackageCheck} tone="bg-blue-100 text-blue-700 shadow-blue-500/10"/>
      <Stat title="Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ£ÙƒÙŠØ¯ Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ" value={`${s.confirmation_rate}%`} detail={`ØªÙ… ØªØ£ÙƒÙŠØ¯ ${s.confirmed} Ø·Ù„Ø¨ Ø¨Ø§Ù„ÙƒØ§Ù…Ù„`} icon={CheckCircle2} tone="bg-emerald-100 text-emerald-700 shadow-emerald-500/10"/>
      <Stat title="Ù…ÙˆØ§Ù‚Ø¹ GPS Ø§Ù„Ù…Ø³ØªÙ„Ù…Ø©" value={s.gps_verified_count} detail="Ø¹Ù†Ø§ÙˆÙŠÙ† Ø¯Ù‚ÙŠÙ‚Ø© Ø¨Ù†Ø³Ø¨Ø© 100%" icon={MapPin} tone="bg-indigo-100 text-indigo-700 shadow-indigo-500/10"/>
      <Stat title="Ø¥ÙŠØ±Ø§Ø¯Ø§Øª Ø§Ù„Ù€ Upsell" value={`${s.upsell_revenue} Ø±.Ø³`} detail={`ØªØ­ÙˆÙŠÙ„ ${s.upsell_conversion_count} Ø¹Ø±ÙˆØ¶ Ø¥Ø¶Ø§ÙÙŠØ©`} icon={BadgePercent} tone="bg-amber-100 text-amber-700 shadow-amber-500/10"/>
    </section>

    {/* Google Sheets Sync status banner */}
    <div className="mt-6 flex items-center justify-between p-4 rounded-xl bg-white border border-slate-100 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${s.google_sheets_sync_healthy ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`}></div>
        <p className="text-sm font-bold text-slate-700">ØªØ­Ø¯ÙŠØ« Ø¬Ø¯Ø§ÙˆÙ„ Ø¬ÙˆØ¬Ù„ (Google Sheets):</p>
        <span className="text-xs text-slate-500">{s.google_sheets_sync_healthy ? "Ù†Ø´Ø· ÙˆÙ…Ø²Ø§Ù…Ù† ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ âœ“" : "ØºÙŠØ± Ù…ÙØ¹Ù„ (Ø§Ø°Ù‡Ø¨ Ø¥Ù„Ù‰ ØªÙØ¹ÙŠÙ„ Ø§Ù„Ù‚Ù†ÙˆØ§Øª Ù„Ù„Ø±Ø¨Ø·)"}</span>
      </div>
      {s.google_sheets_sync_healthy && <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">Ø¬Ø§Ù‡Ø² Ù„Ù„Ø¹Ù…Ù„</span>}
    </div>

    {/* Interactive Chatbot Simulation Sandbox */}
    <section className="glass rounded-2xl p-8 mt-6 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-sky/5 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
      
      <div className="flex justify-between items-center relative z-10 border-b border-slate-100 pb-5">
        <div>
          <h2 className="font-black text-xl text-ink">Ù…Ø­Ø§ÙƒÙŠ Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø© ÙˆØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨ÙŠØ§Øª (Sandbox)</h2>
          <p className="text-sm font-medium text-slate-500 mt-2">Ø§Ø®ØªØ¨Ø± Ø¯ÙˆØ±Ø© Ø­ÙŠØ§Ø© Ø§Ù„Ø¨ÙˆØª Ø¨Ø§Ù„ÙƒØ§Ù…Ù„: Ø§Ù„ØªØ£ÙƒÙŠØ¯ØŒ Ø¬Ù…Ø¹ GPSØŒ ÙˆØªÙ‚Ø¯ÙŠÙ… Ø¹Ø±ÙˆØ¶ Ø§Ù„Ù€ Upsell.</p>
        </div>
        <div className="w-12 h-12 bg-sky-100 text-sky rounded-2xl flex items-center justify-center border border-sky-200 shadow-lg shadow-sky/20"><Sparkles /></div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8 mt-6 items-start relative z-10">
        <div className="lg:col-span-7 space-y-4">
          {simStep === "ready" ? (
            <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
              <MessageCircle className="mx-auto text-slate-400 mb-3" size={32} />
              <h4 className="font-bold text-slate-700">Ø§Ø¨Ø¯Ø£ ØªØ¬Ø±Ø¨Ø© Ø§Ù„Ø¨ÙˆØª Ø§Ù„ØªÙØ§Ø¹Ù„ÙŠ</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Ø³ÙŠÙ‚ÙˆÙ… Ø§Ù„Ù†Ø¸Ø§Ù… Ø¨Ø¥Ù†Ø´Ø§Ø¡ Ø·Ù„Ø¨ ÙˆÙ‡Ù…ÙŠ Ø¨Ù‚ÙŠÙ…Ø© 320 Ø±ÙŠØ§Ù„ ÙˆØ¨Ø¯Ø¡ Ù…Ø­Ø§Ø¯Ø«Ø© ØªØ£ÙƒÙŠØ¯ Ø¢Ù„ÙŠØ© Ø¨Ø§Ù„ÙˆØ§ØªØ³Ø§Ø¨.</p>
              <button onClick={startSimulator} className="mt-5 rounded-xl bg-blue-deep hover:bg-blue-800 text-white font-bold text-sm px-6 py-3 shadow-md">
                Ù…Ø­Ø§ÙƒØ§Ø© Ø·Ù„Ø¨ Ø¬Ø¯ÙŠØ¯ ðŸš€
              </button>
            </div>
          ) : (
            <div className="bg-[#E5DDD5] rounded-2xl p-4 min-h-[320px] flex flex-col justify-between border border-slate-200">
              <div className="bg-[#075E54] text-white p-3 rounded-t-xl -mx-4 -mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center font-bold text-xs">Ù…</div>
                  <div className="text-xs font-bold">Ø¨ÙˆØª Ù…Ø¬ÙŠØ¨ | ØªØ£ÙƒÙŠØ¯ ÙÙˆØ±ÙŠ</div>
                </div>
                <span className="text-[10px] bg-emerald-500/25 px-2 py-0.5 rounded font-mono">Order: #{activeSimId?.slice(0,4)}</span>
              </div>

              <div className="space-y-3 mt-4 flex-1 overflow-y-auto max-h-[220px]">
                <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                  Ù…Ø±Ø­Ø¨Ø§Ù‹ Ø¨Ùƒ! ØªÙ… Ø§Ø³ØªÙ„Ø§Ù… Ø·Ù„Ø¨Ùƒ Ø¨Ù‚ÙŠÙ…Ø© <strong>{simAmount} Ø±ÙŠØ§Ù„</strong>. Ù‡Ù„ ØªØ±ØºØ¨ Ø¨ØªØ£ÙƒÙŠØ¯ Ø´Ø­Ù† Ø·Ù„Ø¨Ùƒ Ø§Ù„Ø¢Ù†ØŸ
                </div>

                {simStep !== "pending_confirm" && (
                  <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                    Ù†Ø¹Ù…ØŒ Ø£ÙƒÙŠØ¯ ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨ âœ…
                  </div>
                )}

                {(simStep === "pending_gps" || simStep === "pending_upsell" || simStep === "completed") && (
                  <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                    Ø´ÙƒØ±Ø§Ù‹ Ù„ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨! ÙØ¶Ù„Ø§Ù‹ Ø£Ø±Ø³Ù„ Ù…ÙˆÙ‚Ø¹Ùƒ Ø§Ù„Ø¬ØºØ±Ø§ÙÙŠ (GPS) Ù„ØªØ³Ù‡ÙŠÙ„ Ø§Ù„ØªØ³Ù„ÙŠÙ….
                  </div>
                )}

                {simStep !== "pending_confirm" && simStep !== "pending_gps" && (
                  <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                    ðŸ“ Ù…Ø´Ø§Ø±ÙƒØ© Ø§Ù„Ø¥Ø­Ø¯Ø§Ø«ÙŠØ§Øª (Riyadh: 24.71, 46.67)
                  </div>
                )}

                {(simStep === "pending_upsell" || simStep === "completed") && (
                  <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed">
                    Ù…ÙˆÙ‚Ø¹Ùƒ Ù…Ø¹ØªÙ…Ø¯. Ø¨Ù…Ù†Ø§Ø³Ø¨Ø© ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨ØŒ Ù‡Ù„ ØªÙˆØ¯ Ø¥Ø¶Ø§ÙØ© Ø¹Ø·Ø± 'Ø¨Ø±ÙŠØ² Ø§Ù„Ø®Ù„ÙŠØ¬ Ø§Ù„ÙØ§Ø®Ø±' Ø¨Ø®ØµÙ… 30% Ø¨Ø³Ø¹Ø± 99 Ø±ÙŠØ§Ù„ ÙÙ‚Ø·ØŸ
                  </div>
                )}

                {simStep === "completed" && (
                  <>
                    <div className="bg-[#DCF8C6] p-2.5 rounded-lg text-xs max-w-[80%] shadow-sm ml-auto mr-0 text-right font-bold">
                      Ù†Ø¹Ù…ØŒ Ø£Ø±ÙŠØ¯ Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø¹Ø·Ø±! ðŸ§´
                    </div>
                    <div className="bg-white p-2.5 rounded-lg text-xs max-w-[85%] shadow-sm leading-relaxed text-emerald-800 font-bold border border-emerald-250">
                      Ø±Ø§Ø¦Ø¹! ØªÙ… ØªØ­Ø¯ÙŠØ« Ù‚ÙŠÙ…Ø© Ø§Ù„ÙØ§ØªÙˆØ±Ø© Ø¥Ù„Ù‰ {simAmount} Ø±ÙŠØ§Ù„ ÙˆÙ…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ø·Ù„Ø¨ ÙÙˆØ±Ø§Ù‹ ÙÙŠ Google Sheets.
                    </div>
                  </>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200/50">
                {simStep === "pending_confirm" && (
                  <div className="flex gap-2">
                    <button onClick={()=>handleSimAction("confirm")} className="flex-1 bg-[#25D366] text-white p-2 text-xs font-bold rounded-xl shadow">ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨ âœ…</button>
                    <button onClick={()=>setSimStep("ready")} className="bg-white text-slate-500 border border-slate-200 p-2 text-xs font-bold rounded-xl">Ø¥Ù„ØºØ§Ø¡</button>
                  </div>
                )}
                {simStep === "pending_gps" && (
                  <button onClick={()=>handleSimAction("share_location")} className="w-full bg-blue-600 text-white p-2 text-xs font-bold rounded-xl shadow">Ø¥Ø±Ø³Ø§Ù„ Ø¥Ø­Ø¯Ø§Ø«ÙŠØ§Øª Ø§Ù„Ù…ÙˆÙ‚Ø¹ (GPS) ðŸ“</button>
                )}
                {simStep === "pending_upsell" && (
                  <div className="flex gap-2">
                    <button onClick={()=>handleSimAction("accept_upsell")} className="flex-1 bg-emerald-600 text-white p-2 text-xs font-bold rounded-xl shadow">Ù†Ø¹Ù…ØŒ Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ù…Ù†ØªØ¬ Ø§Ù„Ù…Ù‚ØªØ±Ø­ ðŸ§´</button>
                    <button onClick={()=>handleSimAction("reject_upsell")} className="flex-1 bg-slate-100 text-slate-600 p-2 text-xs font-bold rounded-xl">Ù„Ø§ Ø´ÙƒØ±Ø§Ù‹ØŒ Ø´Ø­Ù† Ø§Ù„Ø·Ù„Ø¨ Ø§Ù„Ø£ØµÙ„ÙŠ</button>
                  </div>
                )}
                {simStep === "completed" && (
                  <div className="space-y-2">
                    <div className="text-xs text-center text-emerald-700 bg-emerald-50 p-2 rounded-lg font-bold">âœ“ ØªÙ…Øª Ù…Ø­Ø§ÙƒØ§Ø© Ø§Ù„Ø¯ÙˆØ±Ø© ÙƒØ§Ù…Ù„Ø© ÙˆØªØ³Ø¬ÙŠÙ„Ù‡Ø§ Ø¨Ù†Ø¬Ø§Ø­</div>
                    <button onClick={()=>setSimStep("ready")} className="w-full bg-slate-900 text-white p-2 text-xs font-bold rounded-xl">Ø¬Ø±Ø¨ Ù…Ø±Ø© Ø£Ø®Ø±Ù‰ ðŸ”„</button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-950 text-white p-5 rounded-2xl border border-slate-800">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Ù†Ø´Ø§Ø· Ø§Ù„Ù…Ø²Ø§Ù…Ù†Ø© Ø§Ù„Ù…Ø¨Ø§Ø´Ø±</h4>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">ØªØ£ÙƒÙŠØ¯ WABA:</span><span>{simStep !== "ready" && simStep !== "pending_confirm" ? "Ù…ÙƒØªÙ…Ù„ âœ“" : "Ø¨Ø§Ù†ØªØ¸Ø§Ø± Ø§Ù„ØªØ£ÙƒÙŠØ¯"}</span></div>
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">Ø¥Ø­Ø¯Ø§Ø«ÙŠØ§Øª GPS:</span><span>{simStep === "pending_upsell" || simStep === "completed" ? "Ù…Ø³ØªÙ„Ù…Ø© (24.71, 46.67)" : "Ø¨Ø§Ù†ØªØ¸Ø§Ø± Ø§Ù„Ø¹Ù…ÙŠÙ„"}</span></div>
              <div className="flex justify-between border-b border-slate-900 pb-2"><span className="text-slate-400">Ø§Ù„Ø¹Ø±Ø¶ Ø§Ù„Ø¥Ø¶Ø§ÙÙŠ (Upsell):</span><span>{simStep === "completed" ? "+99 Ø±ÙŠØ§Ù„ (Ù…Ù‚Ø¨ÙˆÙ„)" : "Ù„Ù… ÙŠÙ‚ØªØ±Ø­ Ø¨Ø¹Ø¯"}</span></div>
              <div className="flex justify-between pb-2"><span className="text-slate-400">Google Sheet:</span><span>{simStep === "completed" ? (s.google_sheets_sync_healthy ? "Ù…ÙƒØªÙ…Ù„ ÙˆÙ…Ø²Ø§Ù…Ù† âœ“" : "ØªÙ…Øª Ø§Ù„Ù…Ø­Ø§ÙƒØ§Ø© Ù„ÙˆØ­Ø© Ù…Ø­Ø¯Ø¯Ø©") : "Ù‚ÙŠØ¯ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø©"}</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </>}

  {tab === "orders" && (
    <section className="glass rounded-2xl p-5 mt-8 overflow-auto">
      <h2 className="text-xl font-black mb-5">Ø³Ø¬Ù„ Ø§Ù„Ø·Ù„Ø¨ÙŠØ§Øª</h2>
      {orders.isLoading ? (
        <p>Ø¬Ø§Ø±ÙŠ Ø§Ù„ØªØ­Ù…ÙŠÙ„â€¦</p>
      ) : orders.data?.length ? (
        <table className="w-full text-sm">
          <thead className="text-slate-500 border-b border-slate-100">
            <tr>
              <th className="text-right p-3">Ø§Ù„Ø·Ù„Ø¨</th>
              <th>Ø§Ù„Ù‚ÙŠÙ…Ø©</th>
              <th>Ø§Ù„Ø­Ø§Ù„Ø©</th>
              <th>Ø§Ù„Ù…Ø®Ø§Ø·Ø±Ø©</th>
              <th>Ø§Ù„Ù…ÙˆÙ‚Ø¹ (GPS)</th>
              <th>Ø§Ù„ØªØ§Ø±ÙŠØ®</th>
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
                    <span className="text-slate-400 text-xs">ØºÙŠØ± Ù…Ø­Ø¯Ø¯</span>
                  )}
                </td>
                <td className="text-center text-slate-500 text-xs">{new Date(o.created_at).toLocaleDateString("ar-SA")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="py-16 text-center text-slate-500">Ø³ØªØ¸Ù‡Ø± Ø§Ù„Ø·Ù„Ø¨ÙŠØ§Øª Ù‡Ù†Ø§ ÙÙˆØ± Ø³Ø­Ø¨Ù‡Ø§ Ù…Ù† Ù…ØªØ¬Ø±Ùƒ Ø£Ùˆ Ø¥Ø±Ø³Ø§Ù„Ù‡Ø§ Ø¹Ø¨Ø± API.</p>
      )}
    </section>
  )}
  
  {tab==="integrations"&&<Integrations storeId={store.id} onConnectedChange={() => summary.refetch()}/>}
  {tab==="developer"&&<DeveloperApi storeId={store.id}/>} 
  {tab==="billing"&&<Billing storeId={store.id}/>}
  {tab==="privacy"&&<Privacy/>}
  </main></div>;
}

function repairEncoding(root: ParentNode=document){
  const nodes=root.querySelectorAll?.("*:not(script):not(style)") || [];
  const repair=(node: Node)=>{if(node.nodeType!==Node.TEXT_NODE)return;const t=node.textContent||"";if(!/[ØÙÃÂ]/.test(t))return;try{const bytes=[];for(const ch of t){const c=ch.codePointAt(0)!;if(c>=0x80&&c<=0x9f){const cp=[0x20ac,0x201a,0x192,0x201e,0x2026,0x2020,0x2021,0x2c6,0x2030,0x160,0x2039,0x152,0x17d,0x2018,0x2019,0x201c,0x201d,0x2022,0x2013,0x2014,0x2dc,0x2122,0x161,0x203a,0x153,0x17e,0x178];const i=cp.indexOf(c);bytes.push(i<0?c:i+0x80);}else bytes.push(c);}const fixed=new TextDecoder().decode(new Uint8Array(bytes));if(fixed!==t&&/[؀-ۿ]/.test(fixed))(node as Text).textContent=fixed;}catch{}}
  nodes.forEach(el=>el.childNodes.forEach(repair));
}
export default function App(){useEffect(()=>{repairEncoding();const observer=new MutationObserver(()=>repairEncoding());observer.observe(document.body,{subtree:true,childList:true,characterData:true});return()=>observer.disconnect();},[]);const me=useQuery({queryKey:["me"],queryFn:async()=> (await api.get<User>("/api/auth/me")).data,retry:false});if(me.isLoading)return <div className="min-h-screen grid place-items-center font-black">Ù…ÙØ¬ÙŠØ¨</div>;if(!me.data)return <Auth onDone={()=>me.refetch()}/>;return <Dashboard user={me.data} onLogout={async()=>{await api.post("/api/auth/logout");location.reload();}}/>;}

