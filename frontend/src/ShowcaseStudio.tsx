import {
  Check,
  CheckCircle2,
  Clock3,
  Link2,
  MapPin,
  MessageCircle,
  PackageCheck,
  QrCode,
  Store,
} from "lucide-react";

type ShowcaseMode = "onboarding" | "workflow";

const order = {
  number: "ORD-2026-10482",
  customer: "عبدالله الشمري",
  city: "حي النرجس، الرياض",
  product: "عطر مروكي ملكي فاخر 100 مل",
  amount: "380 ر.س",
};

function Brand() {
  return <div className="showcase-brand"><span>م</span><strong>مُجيب</strong></div>;
}

function Caption({children}:{children:React.ReactNode}) {
  return <div className="showcase-caption">{children}</div>;
}

function FakeQr() {
  return <img className="showcase-qr" src="/videos/mujeeb-wa-link-qr.png" alt="رمز ربط WhatsApp قابل للمسح"/>;
}

function OnboardingScene({scene}:{scene:string}) {
  const sallaConnected = ["qr", "ready", "end"].includes(scene);
  const whatsappConnected = ["ready", "end"].includes(scene);
  return <main className="showcase-shell" dir="rtl">
    <header className="showcase-header"><Brand/><div className="showcase-pill"><Clock3 size={18}/> جاهز خلال دقيقتين</div></header>
    {scene === "end" ? <FinalCard title="مُجيب — تأكيد أذكى لطلباتك" subtitle="ابدأ أول 50 تأكيد طلب مجاناً"/> : <>
      <section className="showcase-title-row">
        <div><p>إعداد متجرك</p><h1>ابدأ التأكيد التلقائي بثلاث خطوات واضحة</h1></div>
        <div className="showcase-counter"><small>رصيد التجربة</small><strong>0 / 50</strong><span>تأكيد مستخدم</span></div>
      </section>
      <section className="showcase-grid onboarding">
        <article className={`showcase-card ${sallaConnected ? "done" : "active"}`}>
          <div className="card-number">1</div><Store size={26}/><h2>اربط متجرك</h2>
          <div className="platform-row"><button className="selected">سلة <small>Salla</small></button><button>زد <small>Zid</small></button><button>Shopify</button></div>
          {!sallaConnected ? <div className="showcase-modal">
            <div className="modal-head"><span>ربط متجر سلة</span><span className="secure"><Link2 size={15}/> اتصال آمن</span></div>
            <label>مفتاح ربط المتجر</label>
            <div className="key-field" dir="ltr">salla_demo_sec_••••••••19482</div>
            <button className="primary">ربط المتجر</button>
          </div> : <div className="success-box"><CheckCircle2 size={26}/><div><strong>متجر أصالة للعود</strong><span>متصل وتبدأ الطلبات بالمزامنة تلقائياً</span></div></div>}
        </article>
        <article className={`showcase-card ${scene === "qr" ? "active" : whatsappConnected ? "done" : "muted"}`}>
          <div className="card-number">2</div><MessageCircle size={26}/><h2>اربط WhatsApp Business</h2>
          {scene === "qr" ? <div className="qr-layout"><FakeQr/><div><strong>امسح الرمز من هاتفك</strong><p>WhatsApp ← الأجهزة المرتبطة ← ربط جهاز</p><span className="live-dot">بانتظار المسح الآمن</span></div></div> : whatsappConnected ? <div className="success-box"><CheckCircle2 size={26}/><div><strong>تم ربط WhatsApp بنجاح</strong><span>القناة جاهزة لاستقبال الطلبات</span></div></div> : <div className="empty-step"><QrCode size={42}/><span>تظهر هذه الخطوة بعد ربط المتجر</span></div>}
        </article>
        <article className={`showcase-card ${whatsappConnected ? "done" : "muted"}`}>
          <div className="card-number">3</div><PackageCheck size={26}/><h2>شغّل مجيب</h2>
          <ul className="ready-list"><li className={sallaConnected ? "ok" : ""}><Check/> المتجر متصل</li><li className={whatsappConnected ? "ok" : ""}><Check/> WhatsApp متصل</li><li className={whatsappConnected ? "ok" : ""}><Check/> النظام جاهز للعمل</li></ul>
          <button className="primary" disabled={!whatsappConnected}>ابدأ أول 50 تأكيداً مجاناً</button>
        </article>
      </section>
      <Caption>{scene === "salla" ? "ربط فوري عبر API" : scene === "qr" ? "مسح فوري للواتساب" : "50 طلباً مجاناً، بدون بطاقة بنكية"}</Caption>
    </>}
  </main>;
}

function ChatBubble({side="mujeeb",children}:{side?:"mujeeb"|"customer";children:React.ReactNode}) {
  return <div className={`chat-bubble ${side}`}>{children}<time>{side === "mujeeb" ? "10:42" : "10:43"}</time></div>;
}

function OrderCard({confirmed=false}:{confirmed?:boolean}) {
  return <article className={`order-card ${confirmed ? "confirmed" : ""}`}>
    <div className="order-top"><div><small>طلب دفع عند الاستلام</small><strong>#{order.number}</strong></div><span>{confirmed ? "مؤكد ومرفق بالموقع" : "بانتظار التأكيد"}</span></div>
    <div className="order-data"><p><b>العميل</b>{order.customer}</p><p><b>المبلغ</b>{order.amount}</p><p><b>المدينة</b>{order.city}</p><p><b>المنتج</b>{order.product}</p></div>
    {confirmed && <a><MapPin size={17}/> فتح الموقع في Google Maps</a>}
  </article>;
}

function WorkflowScene({scene}:{scene:string}) {
  const showConfirm = ["confirm", "location", "synced", "end"].includes(scene);
  const showLocation = ["location", "synced", "end"].includes(scene);
  const synced = ["synced", "end"].includes(scene);
  return <main className="showcase-shell workflow" dir="rtl">
    <header className="showcase-header"><Brand/><div className="showcase-pill"><span className="live-dot"/> محرك التأكيد يعمل الآن</div></header>
    {scene === "end" ? <FinalCard title="تأكيد أسرع • مرتجعات أقل" subtitle="ابدأ مع 50 تأكيداً مجانياً لمتجرك"/> : <>
      <section className="workflow-grid">
        <div className="store-panel">
          <div className="panel-title"><div><small>متجر أصالة للعود</small><h1>الطلبات</h1></div><span>سلة Salla</span></div>
          <OrderCard confirmed={synced}/>
          <div className="activity-line"><span className={showConfirm ? "done" : "active"}>وصل الطلب</span><i/><span className={showLocation ? "done" : ""}>تم التأكيد</span><i/><span className={synced ? "done" : ""}>تمت المزامنة</span></div>
        </div>
        <div className="phone-wrap">
          <div className="phone">
            <div className="phone-top"><span className="avatar">م</span><div><strong>مُجيب | أصالة للعود</strong><small>WhatsApp Business</small></div></div>
            <div className="chat">
              <ChatBubble>أهلاً بك يالغالي أ. عبدالله من متجر أصالة للعود. نأكد معك طلبك عطر مروكي ملكي بمبلغ 380 ر.س؟</ChatBubble>
              {showConfirm && <ChatBubble side="customer">إي نعم تأكيد، متى يوصل؟</ChatBubble>}
              {showLocation && <ChatBubble>سم يالغالي، يوصلك خلال 48 ساعة. فضلاً شاركنا اللوكيشن لتسليم أدق.</ChatBubble>}
              {showLocation && <div className="location-message"><MapPin size={25}/><div><strong>حي النرجس، الرياض</strong><span>24.8138, 46.6367</span></div></div>}
              {synced && <div className="chat-system"><CheckCircle2 size={16}/> تم تأكيد الطلب وتحديث موقع التسليم</div>}
            </div>
          </div>
        </div>
      </section>
      <Caption>{scene === "incoming" ? "طلب دفع عند الاستلام جديد" : scene === "confirm" ? "تأكيد فوري بلهجة سعودية" : scene === "location" ? "سحب لوكيشن GPS بدقة" : "مزامنة تلقائية مع المتجر"}</Caption>
    </>}
  </main>;
}

function FinalCard({title,subtitle}:{title:string;subtitle:string}) {
  return <section className="showcase-final"><Brand/><h1>{title}</h1><p>{subtitle}</p><button>ابدأ تجربتك المجانية الآن</button><small>usemujeeb.com</small></section>;
}

export default function ShowcaseStudio({mode}:{mode:string}) {
  const safeMode:ShowcaseMode = mode === "workflow" ? "workflow" : "onboarding";
  const scene = new URLSearchParams(location.search).get("scene") || (safeMode === "workflow" ? "incoming" : "salla");
  return safeMode === "workflow" ? <WorkflowScene scene={scene}/> : <OnboardingScene scene={scene}/>;
}
