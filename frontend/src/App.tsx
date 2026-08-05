import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {
  BarChart3, Boxes, CheckCircle2, Clipboard, Code2, CreditCard, Link2,
  Download, LockKeyhole, LogOut, MessageCircle, PackageCheck, ShieldCheck, Sparkles,
  Trash2, TriangleAlert,
} from "lucide-react";
import {api} from "./api";
import {launchEmbeddedSignup} from "./meta";
import type {Order, Summary, User} from "./types";

const statusLabel: Record<string,string> = {
  pending:"جديد", awaiting_customer:"بانتظار العميل", confirmed:"مؤكد",
  cancelled:"ملغي", human_follow_up:"متابعة بشرية", shipped:"تم الشحن",
  delivered:"تم التسليم", returned:"مرتجع",
};

function Auth({onDone}:{onDone:()=>void}) {
  const [mode,setMode]=useState<"login"|"register">("login");
  const [error,setError]=useState("");
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError("");
    try { 
      await api.post(`/api/auth/${mode}`, Object.fromEntries(new FormData(e.currentTarget))); 
      onDone(); 
    }
    catch (err: any) { 
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (typeof detail === 'string' ? detail : "تأكد من صحة البيانات المدخلة"));
    }
  };
  return <main className="mesh min-h-screen grid place-items-center p-5"><section className="glass w-full max-w-5xl overflow-hidden rounded-[2rem] shadow-2xl shadow-slate-900/10 grid lg:grid-cols-2">
    <div className="bg-ink p-10 text-white min-h-[520px] flex flex-col justify-between"><div><div className="text-3xl font-black">مُجيب <span className="text-mint">Mujeeb</span></div><p className="mt-5 text-4xl font-black leading-tight">حوّل واتساب إلى<br/>محرك إيرادات لمتجرك.</p><p className="mt-5 text-slate-300 leading-7">تأكيد الطلبات، حماية الدفع عند الاستلام، واستعادة المبيعات — من لوحة واحدة.</p></div><div className="grid grid-cols-3 gap-3 text-center text-xs"><span className="rounded-xl bg-white/5 p-3">Salla</span><span className="rounded-xl bg-white/5 p-3">Zid</span><span className="rounded-xl bg-white/5 p-3">Custom API</span></div></div>
    <form onSubmit={submit} className="p-8 lg:p-12 flex flex-col justify-center"><p className="text-sm font-bold text-sky">نسخة المؤسسين التجريبية</p><h1 className="text-3xl font-black mt-2">{mode==="login"?"مرحباً بعودتك":"ابدأ بناء نظامك"}</h1><p className="text-slate-500 mt-2">أول 50 طلباً للاختبار، بلا بطاقة بنكية.</p><div className="grid gap-3 mt-7">
      {mode==="register"&&<><input name="full_name" required placeholder="الاسم الكامل" className="rounded-xl border border-slate-200 p-3"/><input name="phone" required placeholder="+9665xxxxxxxx" dir="ltr" className="rounded-xl border border-slate-200 p-3"/><input name="store_name" required placeholder="اسم المتجر" className="rounded-xl border border-slate-200 p-3"/><div className="grid grid-cols-2 gap-3"><select name="platform" className="rounded-xl border border-slate-200 p-3"><option value="salla">سلة</option><option value="zid">زد</option><option value="shopify">Shopify</option><option value="custom">متجر مخصص</option></select><select name="country_code" className="rounded-xl border border-slate-200 p-3"><option value="SA">السعودية</option><option value="AE">الإمارات</option><option value="KW">الكويت</option><option value="QA">قطر</option><option value="BH">البحرين</option><option value="OM">عُمان</option></select></div></>}
      <input name="email" type="email" required placeholder="البريد الإلكتروني" dir="ltr" className="rounded-xl border border-slate-200 p-3"/><input name="password" type="password" minLength={10} required placeholder="كلمة المرور" dir="ltr" className="rounded-xl border border-slate-200 p-3"/>{error&&<p className="text-red-600 text-sm">{error}</p>}<button className="rounded-xl bg-sky text-white font-black p-3 hover:bg-blue-700">{mode==="login"?"دخول آمن":"إنشاء الحساب"}</button></div>
      <button type="button" onClick={()=>setMode(mode==="login"?"register":"login")} className="mt-5 text-sm text-slate-600">{mode==="login"?"متجر جديد؟ أنشئ حسابك":"لديك حساب؟ سجّل الدخول"}</button>
    </form></section></main>;
}

function Stat({title,value,detail,icon:Icon,tone}:{title:string;value:string|number;detail:string;icon:any;tone:string}) {
  return <article className="glass rounded-2xl p-5"><div className="flex justify-between"><div><p className="text-sm text-slate-500">{title}</p><p className="text-3xl font-black mt-2">{value}</p></div><div className={`w-11 h-11 rounded-xl grid place-items-center ${tone}`}><Icon size={21}/></div></div><p className="text-xs text-slate-500 mt-4">{detail}</p></article>;
}

function DeveloperApi({storeId}:{storeId:string}) {
  const [createdKey,setCreatedKey]=useState(""); const [message,setMessage]=useState("");
  const keys=useQuery({queryKey:["api-keys",storeId],queryFn:async()=> (await api.get("/api/api-keys",{params:{store_id:storeId}})).data});
  const generate=async()=>{const r=await api.post("/api/api-keys",{store_id:storeId,name:"Pilot integration"});setCreatedKey(r.data.api_key);setMessage("انسخ المفتاح الآن. لن نعرضه كاملاً مرة أخرى.");keys.refetch();};
  const snippet=`curl -X POST https://api.usemujeeb.com/api/orders/custom \\\n+  -H "Content-Type: application/json" \\\n+  -H "X-Mujeeb-API-Key: YOUR_KEY" \\\n+  -d '{"order_id":"1001","customer_name":"Customer","customer_phone":"+966501234567","amount":250,"currency":"SAR","payment_method":"COD","items":[]}'`;
  return <section className="mt-8 max-w-4xl"><div className="flex items-center gap-3"><Code2 className="text-sky"/><div><h2 className="text-xl font-black">تكامل API للمتاجر</h2><p className="text-sm text-slate-500">Shopify، WooCommerce، Laravel وأي متجر مخصص.</p></div></div>
    <div className="grid lg:grid-cols-2 gap-5 mt-5"><article className="glass rounded-2xl p-6"><h3 className="font-black">مفتاح المتجر</h3><p className="text-sm text-slate-500 mt-2">يُحفظ المفتاح مشفراً كبصمة، ويمكن إلغاؤه في أي وقت.</p>{createdKey?<><div dir="ltr" className="mt-4 break-all rounded-xl bg-slate-950 p-4 text-xs text-emerald-300">{createdKey}</div><button onClick={()=>navigator.clipboard.writeText(createdKey)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> نسخ المفتاح</button></>:<button onClick={generate} className="mt-5 rounded-xl bg-ink text-white px-5 py-3 font-bold">إنشاء مفتاح API</button>}{message&&<p className="mt-3 text-xs text-amber-700">{message}</p>}<p className="mt-5 text-xs text-slate-500">المفاتيح النشطة: {keys.data?.length||0}</p></article>
    <article className="glass rounded-2xl p-6"><h3 className="font-black">أرسل أول طلب</h3><pre dir="ltr" className="mt-4 overflow-auto rounded-xl bg-slate-950 p-4 text-[11px] leading-5 text-slate-200">{snippet}</pre><button onClick={()=>navigator.clipboard.writeText(snippet)} className="mt-3 flex items-center gap-2 text-sky font-bold"><Clipboard size={16}/> نسخ المثال</button></article></div></section>;
}

function Billing({storeId}:{storeId:string}) {
  const [checkingOut,setCheckingOut]=useState("");
  const [message,setMessage]=useState("");
  const plans=[
    {id:"starter",name:"Starter",price:"399",orders:"حتى 1,000 طلب شهرياً",detail:"لمتجر واحد وفريق صغير"},
    {id:"growth",name:"Growth",price:"799",orders:"حتى 5,000 طلب شهرياً",detail:"تحليل أعمق ودعم بأولوية",featured:true},
    {id:"scale",name:"Scale",price:"1,499",orders:"حجم مرتفع وفق الاستخدام العادل",detail:"للعلامات متعددة المتاجر"},
  ];
  const checkout=async(plan:string)=>{
    setCheckingOut(plan); setMessage("");
    try { const r=await api.post("/api/payments/checkout",{store_id:storeId,plan}); location.href=r.data.url; }
    catch(err:any){ setMessage(err.response?.status===503?"الدفع الإلكتروني لهذه الخطة قيد التفعيل. تواصل معنا لتثبيت عرض المؤسسين.":"تعذر فتح صفحة الدفع الآمنة. حاول مرة أخرى."); setCheckingOut(""); }
  };
  return <section className="mt-8 max-w-5xl"><p className="text-sm font-bold text-sky">ادفع بعد تحقق القيمة</p><h2 className="text-3xl font-black mt-2">اختر الحجم الذي تبرره أرقام متجرك.</h2><p className="text-slate-500 mt-3">ابدأ بـ50 طلباً مجاناً. الترقية تمر عبر صفحة Creem الآمنة، ولا نخزن بيانات بطاقتك.</p><div className="grid md:grid-cols-3 gap-4 mt-7">{plans.map(plan=><article key={plan.id} className={`glass rounded-2xl p-6 relative ${plan.featured?"ring-2 ring-emerald-500":""}`}>{plan.featured&&<span className="absolute -top-3 right-5 rounded-full bg-emerald-600 px-3 py-1 text-xs font-bold text-white">الأفضل للنمو</span>}<p className="font-black text-xl">{plan.name}</p><p className="mt-4 text-3xl font-black text-sky">{plan.price} <span className="text-sm font-medium text-slate-500">ريال/شهر</span></p><p className="mt-4 font-bold">{plan.orders}</p><p className="mt-2 min-h-10 text-sm text-slate-500">{plan.detail}</p><button onClick={()=>checkout(plan.id)} disabled={!!checkingOut} className={`mt-6 w-full rounded-xl p-3 font-bold disabled:opacity-50 ${plan.featured?"bg-emerald-600 text-white":"bg-ink text-white"}`}>{checkingOut===plan.id?"جارٍ فتح الدفع…":`اختيار ${plan.name}`}</button></article>)}</div>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">{message}</p>}<p className="mt-5 text-xs text-slate-500">لا نضمن نسبة إيراد محددة. قرار الترقية يعتمد على تقرير التجربة ونتائج متجرك الفعلية.</p></section>;
}

function Integrations({storeId}:{storeId:string}) {
  const [shop,setShop]=useState(""); const [message,setMessage]=useState("");
  const status=useQuery({queryKey:["integration-status",storeId],queryFn:async()=> (await api.get("/api/integrations/status",{params:{store_id:storeId}})).data});
  const connect=async(provider:"salla"|"zid")=>{setMessage("");try{const r=await api.post(`/api/integrations/${provider}/start`,{store_id:storeId});location.href=r.data.url;}catch(err:any){setMessage(err.response?.data?.detail||"تعذر بدء الربط");}};
  const connectShopify=async()=>{setMessage("");try{const r=await api.post("/api/integrations/shopify/start",{store_id:storeId,shop});location.href=r.data.url;}catch(err:any){setMessage(err.response?.data?.detail||"تحقق من اسم متجر Shopify");}};
  const connectWhatsApp=async()=>{setMessage("");try{const signup=await launchEmbeddedSignup();await api.post("/api/whatsapp/embedded-signup",{store_id:storeId,...signup});setMessage("تم ربط رقم واتساب والتحقق من ملكيته.");status.refetch();}catch(err:any){setMessage(err.response?.data?.detail||err.message||"تعذر ربط واتساب");}};
  const entry=(provider:string)=>status.data?.[provider]||{configured:false,connected:false};
  return <section className="mt-8"><h2 className="text-xl font-black">اربط منظومة البيع</h2><p className="text-slate-500 mt-1">كل ربط يستخدم تفويضاً رسمياً؛ لا نطلب كلمة مرور متجرك.</p>{message&&<p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">{message}</p>}<div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4 mt-5">
    {[{id:"salla",name:"سلة",desc:"الطلبات وتحديثات الحالة"},{id:"zid",name:"زد",desc:"الطلبات والعملاء"}].map(item=>{const state=entry(item.id);return <article className="glass rounded-2xl p-6" key={item.id}><Link2 className="text-mint"/><h3 className="font-black text-lg mt-5">{item.name}</h3><p className="text-sm text-slate-500 mt-2 min-h-10">{item.desc}</p><button disabled={!state.configured||state.connected} onClick={()=>connect(item.id as "salla"|"zid")} className="mt-5 w-full rounded-xl border border-sky text-sky p-2 font-bold disabled:border-slate-200 disabled:text-slate-400">{state.connected?"متصل":state.configured?"ربط آمن":"قيد إعداد الشريك"}</button></article>})}
    <article className="glass rounded-2xl p-6"><Link2 className="text-mint"/><h3 className="font-black text-lg mt-5">Shopify</h3><p className="text-sm text-slate-500 mt-2">أدخل اسم المتجر فقط.</p><input value={shop} onChange={e=>setShop(e.target.value)} dir="ltr" placeholder="store.myshopify.com" className="mt-3 w-full rounded-xl border border-slate-200 p-2 text-sm"/><button disabled={!entry("shopify").configured||entry("shopify").connected||!shop} onClick={connectShopify} className="mt-3 w-full rounded-xl border border-sky text-sky p-2 font-bold disabled:border-slate-200 disabled:text-slate-400">{entry("shopify").connected?"متصل":entry("shopify").configured?"ربط آمن":"قيد إعداد الشريك"}</button></article>
    <article className="glass rounded-2xl p-6"><MessageCircle className="text-mint"/><h3 className="font-black text-lg mt-5">WhatsApp Business</h3><p className="text-sm text-slate-500 mt-2 min-h-10">الربط الذاتي يُفتح فور اعتماد Meta.</p><button disabled={!entry("whatsapp").enabled} onClick={connectWhatsApp} className="mt-5 w-full rounded-xl bg-slate-100 text-slate-500 p-2 font-bold flex items-center justify-center gap-2 disabled:cursor-not-allowed"><LockKeyhole size={16}/>{entry("whatsapp").enabled?"ربط الرقم":"بانتظار اعتماد Meta"}</button></article>
  </div></section>;
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
  const store=user.stores[0]; const [tab,setTab]=useState("overview");
  const summary=useQuery({queryKey:["summary",store.id],queryFn:async()=> (await api.get<Summary>("/api/orders/summary",{params:{store_id:store.id}})).data});
  const orders=useQuery({queryKey:["orders",store.id],queryFn:async()=> (await api.get<Order[]>("/api/orders",{params:{store_id:store.id}})).data});
  const s:Summary=summary.data||{total:0,confirmed:0,cancelled:0,human_follow_up:0,confirmation_rate:0,plan:"free",pilot_orders_used:0,free_pilot_limit:50,free_pilot_remaining:50};
  const nav=[{id:"overview",label:"نظرة عامة",icon:BarChart3},{id:"orders",label:"الطلبات",icon:Boxes},{id:"integrations",label:"الربط",icon:Link2},{id:"developer",label:"API المتجر",icon:Code2},{id:"billing",label:"الباقة",icon:CreditCard},{id:"privacy",label:"الخصوصية",icon:ShieldCheck}];
  return <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]" dir="rtl"><aside className="bg-ink text-white p-5 lg:min-h-screen"><div className="text-2xl font-black mb-8">مُجيب <span className="text-mint">M</span></div><nav className="flex lg:flex-col gap-2 overflow-auto">{nav.map(n=><button key={n.id} onClick={()=>setTab(n.id)} className={`flex items-center gap-3 rounded-xl px-4 py-3 whitespace-nowrap ${tab===n.id?"bg-white text-ink":"text-slate-300 hover:bg-white/10"}`}><n.icon size={18}/>{n.label}</button>)}</nav><button onClick={onLogout} className="mt-8 lg:mt-[45vh] flex gap-2 text-slate-400"><LogOut size={18}/> خروج</button></aside>
  <main className="mesh p-5 lg:p-8"><header className="flex justify-between items-center"><div><p className="text-sm text-slate-500">{store.name} · {store.country_code}</p><h1 className="text-2xl font-black mt-1">أهلاً، {user.full_name.split(" ")[0]}</h1></div><span className="rounded-full bg-emerald-100 text-emerald-800 px-3 py-1 text-xs font-bold">{s.plan==="free"?`التجربة · ${s.free_pilot_remaining??50} طلباً متبقياً`:`خطة ${s.plan}`}</span></header>
  {tab==="overview"&&<><section className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4 mt-8"><Stat title="إجمالي الطلبات" value={s.total} detail="هذا الشهر" icon={PackageCheck} tone="bg-blue-100 text-blue-700"/><Stat title="طلبات مؤكدة" value={s.confirmed} detail={`${s.confirmation_rate}% معدل التأكيد`} icon={CheckCircle2} tone="bg-emerald-100 text-emerald-700"/><Stat title="تحتاج متابعة" value={s.human_follow_up} detail="أولوية فريقك" icon={TriangleAlert} tone="bg-amber-100 text-amber-700"/><Stat title="طلبات ملغاة" value={s.cancelled} detail="راجع أسباب الرفض" icon={ShieldCheck} tone="bg-rose-100 text-rose-700"/></section><section className="glass rounded-2xl p-6 mt-5"><div className="flex justify-between"><div><h2 className="font-black text-lg">مركز العمل اليومي</h2><p className="text-sm text-slate-500 mt-1">ابدأ بالطلبات الأعلى مخاطرة، ثم تابع الحالات غير المحسومة.</p></div><Sparkles className="text-sky"/></div><div className="mt-6 rounded-xl bg-ink text-white p-5 flex flex-wrap justify-between gap-4"><div><p className="text-sm text-slate-300">الخطوة التالية</p><p className="font-bold mt-1">اربط متجرك، ثم يفعّل فريق مجيب رقم واتساب التجريبي لك.</p></div><button onClick={()=>setTab("integrations")} className="rounded-xl bg-mint px-5 py-2 font-bold">ابدأ الربط</button></div></section></>}
  {tab==="orders"&&<section className="glass rounded-2xl p-5 mt-8 overflow-auto"><h2 className="text-xl font-black mb-5">الطلبات</h2>{orders.isLoading?<p>جاري التحميل…</p>:orders.data?.length?<table className="w-full text-sm"><thead className="text-slate-500"><tr><th className="text-right p-3">الطلب</th><th>القيمة</th><th>الحالة</th><th>المخاطرة</th><th>التاريخ</th></tr></thead><tbody>{orders.data.map(o=><tr key={o.id} className="border-t border-slate-100"><td className="p-3 font-bold">#{o.external_order_number||o.id.slice(0,8)}</td><td className="text-center">{o.amount} {o.currency}</td><td className="text-center">{statusLabel[o.status]||o.status}</td><td className="text-center"><span className={`rounded-full px-2 py-1 text-xs ${o.risk_level==="high"?"bg-red-100 text-red-700":o.risk_level==="medium"?"bg-amber-100 text-amber-700":"bg-emerald-100 text-emerald-700"}`}>{o.risk_score}/100</span></td><td className="text-center text-slate-500">{new Date(o.created_at).toLocaleDateString("ar-SA")}</td></tr>)}</tbody></table>:<p className="py-16 text-center text-slate-500">ستظهر الطلبات هنا بعد ربط المنصة أو إرسال أول طلب عبر API.</p>}</section>}
  {tab==="integrations"&&<Integrations storeId={store.id}/>}
  {tab==="developer"&&<DeveloperApi storeId={store.id}/>} 
  {tab==="billing"&&<Billing storeId={store.id}/>}
  {tab==="privacy"&&<Privacy/>}
  </main></div>;
}

export default function App(){const me=useQuery({queryKey:["me"],queryFn:async()=> (await api.get<User>("/api/auth/me")).data,retry:false});if(me.isLoading)return <div className="min-h-screen grid place-items-center font-black">مُجيب</div>;if(!me.data)return <Auth onDone={()=>me.refetch()}/>;return <Dashboard user={me.data} onLogout={async()=>{await api.post("/api/auth/logout");location.reload();}}/>;}
